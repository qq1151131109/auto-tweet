#!/usr/bin/env python3
"""
为人设生成个性化的content_type_distribution

使用LLM分析人设特征,生成适合该人设的内容类型分布
"""
import sys
import os
import json
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from utils.llm_client import LLMClientPool
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger.remove()
logger.add(sys.stderr, level="INFO")


CONTENT_DISTRIBUTION_PROMPT = """You are an expert in social media content strategy. Analyze this persona and create a personalized content_type_distribution.

PERSONA INFORMATION:
Name: {name}
Description: {description}
Personality: {personality}

TASK: Generate 5-8 content types that fit THIS specific persona's character and posting style.

CRITICAL REQUIREMENTS:
1. Content types MUST be specific to this persona (e.g., "office_tease", "gym_flex", "bedroom_mirror_selfie")
2. Mirror selfies should be 20-30% weight (bathroom_mirror_selfie, bedroom_mirror_selfie, gym_mirror_selfie, fitting_room_selfie)
3. Content types should reflect the persona's personality traits and interests
4. Weights must sum to EXACTLY 1.0
5. Each type needs a clear description

OUTPUT FORMAT (JSON only, no markdown):
{{
  "content_type_distribution": {{
    "type_name_1": {{
      "weight": 0.25,
      "desc": "Clear description of what this content type means for this persona"
    }},
    "type_name_2": {{
      "weight": 0.20,
      "desc": "..."
    }}
  }}
}}

Generate the content_type_distribution now:"""


async def generate_distribution_for_persona(persona_data: dict, api_key: str, api_base: str, model: str) -> dict:
    """为单个人设生成content_type_distribution"""

    data = persona_data.get('data', {})
    name = data.get('name', 'Unknown')
    description = data.get('description', '')
    personality = data.get('personality', '')

    logger.info(f"为人设 '{name}' 生成content_type_distribution...")

    # 准备prompt
    prompt = CONTENT_DISTRIBUTION_PROMPT.format(
        name=name,
        description=description[:500],  # 限制长度
        personality=personality[:500]
    )

    # 调用LLM
    client_pool = LLMClientPool(api_key=api_key, api_base=api_base, model=model, max_concurrent=1)

    try:
        messages = [
            {"role": "system", "content": "You are a content strategy expert. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await client_pool.generate(
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )

        # 解析JSON
        response_text = response.strip()

        # 清理markdown
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text

        result = json.loads(response_text)

        # 验证格式
        if 'content_type_distribution' not in result:
            raise ValueError("Missing content_type_distribution key")

        distribution = result['content_type_distribution']

        # 验证权重总和
        total_weight = sum(item.get('weight', 0) for item in distribution.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"权重总和 {total_weight:.2f} 不等于1.0, 自动归一化")
            for key in distribution:
                distribution[key]['weight'] = distribution[key]['weight'] / total_weight

        logger.success(f"✓ '{name}' 生成成功: {len(distribution)} 个内容类型")
        return distribution

    except Exception as e:
        logger.error(f"✗ '{name}' 生成失败: {e}")
        return None


async def main():
    """主函数"""

    # 检查API key
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('API_KEY')
    api_base = os.getenv('API_BASE', 'https://api.openai.com/v1')
    model = os.getenv('MODEL', 'gpt-4')

    if not api_key:
        logger.error("未设置API key, 请设置环境变量 OPENAI_API_KEY 或 API_KEY")
        sys.exit(1)

    logger.info(f"使用模型: {model}")
    logger.info(f"API Base: {api_base}")

    # 加载所有人设
    personas_dir = Path('personas')
    persona_files = sorted([f for f in personas_dir.glob('*.json') if not f.name.startswith('.')])

    # 过滤掉测试文件
    exclude_files = {'sample_mia_with_strategy.json', 'test_optimized.json'}
    persona_files = [f for f in persona_files if f.name not in exclude_files]

    logger.info(f"找到 {len(persona_files)} 个人设文件")

    results = []

    for persona_file in persona_files:
        # 加载人设
        with open(persona_file, 'r', encoding='utf-8') as f:
            persona_data = json.load(f)

        name = persona_data.get('data', {}).get('name', 'Unknown')

        # 检查是否已有content_type_distribution
        twitter_persona = persona_data.get('data', {}).get('extensions', {}).get('twitter_persona', {})
        if 'content_type_distribution' in twitter_persona:
            logger.info(f"⊙ '{name}' 已有content_type_distribution, 跳过")
            results.append({'file': persona_file.name, 'status': 'skip', 'name': name})
            continue

        # 生成distribution
        distribution = await generate_distribution_for_persona(persona_data, api_key, api_base, model)

        if distribution:
            # 保存到persona
            if 'data' not in persona_data:
                persona_data['data'] = {}
            if 'extensions' not in persona_data['data']:
                persona_data['data']['extensions'] = {}
            if 'twitter_persona' not in persona_data['data']['extensions']:
                persona_data['data']['extensions']['twitter_persona'] = {}

            persona_data['data']['extensions']['twitter_persona']['content_type_distribution'] = distribution

            # 保存文件
            with open(persona_file, 'w', encoding='utf-8') as f:
                json.dump(persona_data, f, indent=2, ensure_ascii=False)

            results.append({'file': persona_file.name, 'status': 'success', 'name': name})
        else:
            results.append({'file': persona_file.name, 'status': 'failed', 'name': name})

        # 避免API限流
        await asyncio.sleep(1)

    # 统计结果
    success_count = sum(1 for r in results if r['status'] == 'success')
    skip_count = sum(1 for r in results if r['status'] == 'skip')
    failed_count = sum(1 for r in results if r['status'] == 'failed')

    logger.info("\n=== 生成结果 ===")
    logger.info(f"成功: {success_count}")
    logger.info(f"跳过: {skip_count}")
    logger.info(f"失败: {failed_count}")

    if failed_count > 0:
        logger.warning("\n失败的人设:")
        for r in results:
            if r['status'] == 'failed':
                logger.warning(f"  - {r['file']} ({r['name']})")


if __name__ == "__main__":
    asyncio.run(main())
