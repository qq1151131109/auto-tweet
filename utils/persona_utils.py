"""Character Card 解析工具

支持 Character Card V2 格式的人设数据加载和处理
"""
import json
import base64
from PIL import Image


def load_persona_from_json(file_path: str) -> dict:
    """
    从 JSON 文件加载 SillyTavern Character Card

    参数:
        file_path: JSON 文件路径

    返回:
        Character Card 数据字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        persona = json.load(f)

    # 验证格式
    if persona.get("spec") != "chara_card_v2":
        raise ValueError("只支持 Character Card V2 格式")

    return persona


def load_persona_from_png(file_path: str) -> dict:
    """
    从 PNG 文件的 metadata 加载 Character Card

    参数:
        file_path: PNG 文件路径

    返回:
        Character Card 数据字典
    """
    img = Image.open(file_path)

    if "chara" not in img.info:
        raise ValueError("PNG 文件不包含人设数据 (缺少 'chara' metadata)")

    # 解码 base64
    chara_base64 = img.info["chara"]
    chara_json = base64.b64decode(chara_base64).decode('utf-8')
    persona = json.loads(chara_json)

    # 验证格式
    if persona.get("spec") != "chara_card_v2":
        raise ValueError("只支持 Character Card V2 格式")

    return persona


def extract_few_shot_examples(persona: dict, max_examples: int = 3, scenario: str = "twitter") -> list:
    """
    提取 few-shot 示例

    参数:
        persona: Character Card 数据
        max_examples: 最多提取多少个示例
        scenario: 场景类型 ("twitter" 或 "whatsapp")

    返回:
        示例列表 ["示例1", "示例2", ...]
    """
    data = persona["data"]

    # V2格式：从对应场景获取示例
    if scenario == "twitter":
        twitter_scenario = data.get("twitter_scenario", {})
        tweet_examples = twitter_scenario.get("tweet_examples", [])

        if tweet_examples:
            # 提取推文文本
            examples = [ex.get("text", "") for ex in tweet_examples if ex.get("text")]
            return examples[:max_examples]

    elif scenario == "whatsapp":
        whatsapp_scenario = data.get("whatsapp_scenario", {})
        chat_examples = whatsapp_scenario.get("chat_examples", [])

        if chat_examples:
            # 提取对话中的 {{char}} 回复
            examples = []
            for ex in chat_examples:
                exchange = ex.get("exchange", "")
                if "{{char}}:" in exchange:
                    # 提取角色的回复
                    for line in exchange.split("\n"):
                        if "{{char}}:" in line and line.split("{{char}}:")[1].strip():
                            examples.append(line.split("{{char}}:")[1].strip())
            return examples[:max_examples]

    # 兼容旧格式：从 mes_example 提取
    mes_example = data.get("mes_example", "")
    if mes_example:
        examples = []
        for part in mes_example.split("<START>"):
            if "{{char}}:" in part:
                # 提取角色的回复
                char_responses = [
                    line.split("{{char}}:")[1].strip()
                    for line in part.split("\n")
                    if "{{char}}:" in line and line.split("{{char}}:")[1].strip()
                ]
                examples.extend(char_responses)
        return examples[:max_examples]

    return []


def search_character_book(persona: dict, topic: str, max_results: int = 2) -> list:
    """
    从 character_book 检索相关知识条目

    参数:
        persona: Character Card 数据
        topic: 话题关键词
        max_results: 最多返回多少条结果

    返回:
        知识条目列表 ["知识1", "知识2", ...]
    """
    char_book = persona["data"].get("character_book", {})
    entries = char_book.get("entries", [])

    if not entries:
        return []

    results = []
    for entry in entries:
        # 跳过禁用的条目
        if not entry.get("enabled", True):
            continue

        # 检查 keys 和 secondary_keys 匹配
        keys = entry.get("keys", []) + entry.get("secondary_keys", [])

        if any(key.lower() in topic.lower() for key in keys):
            priority = entry.get("priority", 0)
            content = entry.get("content", "")
            if content:
                results.append((priority, content))

    # 按优先级排序
    results.sort(reverse=True, key=lambda x: x[0])

    # 返回 top N
    return [content for _, content in results[:max_results]]


def get_persona_location(persona: dict, default: str = "New York") -> tuple:
    """
    从人设获取地理位置信息

    参数:
        persona: Character Card 数据
        default: 默认城市

    返回:
        (city, country_code) 元组
    """
    data = persona.get("data", {})
    extensions = data.get("extensions", {})

    # 优先从扁平结构的 core_info 读取，其次兼容旧的 extensions.core_info
    core_info = data.get("core_info") or extensions.get("core_info", {})
    location = core_info.get("location", {})

    if isinstance(location, dict):
        city = location.get("city", default)
        country_code = location.get("country_code", "US")
    else:
        # 兼容旧格式：直接从 extensions.location 获取
        location = extensions.get("location", {})
        if isinstance(location, dict):
            city = location.get("city", default)
            country_code = location.get("country_code", "US")
        else:
            # 如果是字符串，尝试解析
            city = str(location) if location else default
            country_code = "US"

    return city, country_code


def generate_persona_summary(persona: dict) -> str:
    """
    生成人设摘要

    参数:
        persona: Character Card 数据

    返回:
        摘要文本
    """
    data = persona.get("data", {})
    extensions = data.get("extensions", {})

    name = data.get("name", "未命名")
    description = data.get("description", "")

    # V2 扁平格式：优先从 data.core_info 获取年龄，兼容旧的 extensions.core_info
    core_info = data.get("core_info") or extensions.get("core_info", {})
    age = core_info.get("age", "?")

    # 获取位置信息
    location = core_info.get("location", {})
    if isinstance(location, dict):
        city = location.get("city", "")
        location_str = f"📍 {city}" if city else ""
    else:
        location_str = ""

    summary = f"【{name}】{age}岁 {location_str}\n"
    summary += f"{description[:150]}{'...' if len(description) > 150 else ''}\n"

    # 获取 Twitter 账号信息（如果有）
    # 支持扁平结构 data.twitter_persona 和旧结构 extensions.twitter_persona
    twitter_persona = data.get("twitter_persona") or extensions.get("twitter_persona", {})
    social_accounts = twitter_persona.get("social_accounts", {})
    twitter_handle = social_accounts.get("twitter_handle", "")
    if twitter_handle:
        summary += f"\nTwitter: {twitter_handle}"

    return summary
