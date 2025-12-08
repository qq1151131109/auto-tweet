"""
统一的LLM JSON响应解析工具
提取自persona_generator.py和calendar_manager.py的重复逻辑
"""
import json
from typing import Dict, Any, Optional


def normalize_quotes(text: str) -> str:
    """
    规范化引号 - 将中文引号替换为英文引号

    Args:
        text: 输入文本

    Returns:
        规范化后的文本
    """
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    return text


def clean_markdown_json(response: str) -> str:
    """
    清理markdown代码块标记

    Args:
        response: LLM响应文本

    Returns:
        清理后的文本
    """
    response = response.strip()

    # 移除markdown代码块
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]

    return response.strip()


def extract_json_object(text: str) -> Optional[str]:
    """
    从文本中提取JSON对象（fallback策略）

    Args:
        text: 包含JSON的文本

    Returns:
        提取的JSON字符串，如果找不到则返回None
    """
    # 尝试找到JSON的开始和结束
    start = text.find('{')
    if start == -1:
        start = text.find('[')

    end = text.rfind('}')
    if end == -1:
        end = text.rfind(']')

    if start != -1 and end != -1:
        return text[start:end+1]

    return None


def parse_llm_json_response(
    response: str,
    source_name: str = "LLM",
    enable_fallback: bool = True,
    enable_truncation_fix: bool = False
) -> Dict[str, Any]:
    """
    统一的LLM JSON响应解析函数

    Args:
        response: LLM返回的JSON响应
        source_name: 来源名称（用于错误消息）
        enable_fallback: 是否启用fallback提取策略
        enable_truncation_fix: 是否启用截断修复（用于calendar等可能被截断的长JSON）

    Returns:
        解析后的字典

    Raises:
        ValueError: 如果无法解析JSON
    """
    # 1. 清理markdown标记
    response = clean_markdown_json(response)

    # 2. 规范化引号
    response = normalize_quotes(response)

    # 3. 截断修复（可选，用于calendar等长JSON）
    if enable_truncation_fix and not response.endswith("}"):
        response = _fix_truncated_json(response)

    # 4. 尝试解析JSON
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        # 5. Fallback策略：提取JSON对象
        if enable_fallback:
            extracted = extract_json_object(response)
            if extracted:
                try:
                    return json.loads(extracted)
                except json.JSONDecodeError:
                    pass

        # 6. 无法解析，抛出详细错误
        raise ValueError(
            f"Cannot parse {source_name} response as JSON: {e}\n"
            f"Response length: {len(response)} characters\n"
            f"Response preview:\n{response[:500]}..."
        )


def _fix_truncated_json(response: str) -> str:
    """
    修复被截断的JSON（用于calendar生成等长JSON场景）

    Args:
        response: 可能被截断的JSON字符串

    Returns:
        修复后的JSON字符串
    """
    # 找到最后一个完整的日期条目
    lines = response.split('\n')

    # 从后向前搜索，直到找到完整的}
    for i in range(len(lines) - 1, -1, -1):
        if '}' in lines[i]:
            # 截断到这里
            response = '\n'.join(lines[:i+1])

            # 添加闭合括号
            if not response.strip().endswith("}"):
                response += "\n}"
            break

    return response


def parse_calendar_json(
    response: str,
    persona_name: str,
    year_month: str
) -> Dict[str, Any]:
    """
    解析calendar JSON响应（带详细错误信息）

    Args:
        response: LLM返回的calendar JSON
        persona_name: 人设名称
        year_month: 年-月

    Returns:
        解析后的calendar字典

    Raises:
        ValueError: 如果无法解析JSON
    """
    # 清理和规范化
    response = clean_markdown_json(response)
    response = normalize_quotes(response)

    # 截断修复
    if not response.endswith("}"):
        response = _fix_truncated_json(response)

    # 解析JSON
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        # 详细错误信息（用于调试calendar生成）
        error_line = e.lineno if hasattr(e, 'lineno') else 'unknown'
        error_col = e.colno if hasattr(e, 'colno') else 'unknown'

        # 显示错误位置附近的内容
        lines = response.split('\n')
        context = ""

        if hasattr(e, 'lineno') and e.lineno <= len(lines):
            context_start = max(0, e.lineno - 3)
            context_end = min(len(lines), e.lineno + 2)
            context = '\n'.join([f"{i+1}: {lines[i]}" for i in range(context_start, context_end)])

            raise ValueError(
                f"Cannot parse calendar JSON for {persona_name} ({year_month}):\n"
                f"Error location: line {error_line}, column {error_col}\n"
                f"Error message: {str(e)}\n\n"
                f"Context near error:\n{context}\n\n"
                f"Full response length: {len(response)} characters\n"
                f"Response beginning:\n{response[:500]}...\n\n"
                f"Response ending:\n...{response[-500:]}"
            )
        else:
            raise ValueError(
                f"Cannot parse calendar JSON for {persona_name} ({year_month}): {e}\n"
                f"Response length: {len(response)} characters\n"
                f"Response content:\n{response[:1000]}..."
            )
