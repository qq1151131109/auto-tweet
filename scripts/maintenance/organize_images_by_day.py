#!/usr/bin/env python3
"""
重组图片：按persona和day分目录，生成推文-图片索引
"""

import json
import os
import shutil
from pathlib import Path
from collections import defaultdict
import re

# 配置
TWEETS_DIR = Path("output_standalone")
IMAGES_DIR = Path("output_images")
OUTPUT_DIR = Path("output_by_day")


def parse_json_filename(filename: str) -> dict:
    """
    解析JSON文件名: Abigail Grace_day0_tweets5_20251207_181920.json
    """
    match = re.match(r"(.+?)_day(\d+)_tweets\d+_(\d+_\d+)\.json", filename)
    if match:
        return {
            "persona": match.group(1),
            "day": int(match.group(2)),
            "timestamp": match.group(3)
        }
    return None


def find_matching_images(persona_name: str, day: int, slot_numbers: list) -> dict:
    """
    找到匹配的图片文件
    新格式：{persona_name}_day{day}_slot{slot}_timestamp.png
    注意：图片的slot编号是0-4，JSON的tweet slot是1-5，需要映射
    """
    result = {}

    for tweet_slot in slot_numbers:
        image_slot = tweet_slot - 1  # 转换: tweet slot 1 → image slot 0

        # 新格式：包含day信息
        pattern = f"{persona_name}_day{day}_slot{image_slot}_*.png"
        matches = list(IMAGES_DIR.glob(pattern))

        if matches:
            # 如果有多个匹配（理论上只有1个），取第一个
            result[tweet_slot] = matches[0]
        else:
            # 兼容旧格式（没有day信息）
            old_pattern = f"{persona_name}_slot{image_slot}_*.png"
            old_matches = list(IMAGES_DIR.glob(old_pattern))
            if old_matches:
                # 旧格式：按顺序取对应的图片
                day_images = [img for img in old_matches]
                if day < len(day_images):
                    result[tweet_slot] = day_images[day]

    return result


def organize_images():
    """
    主函数：重组图片
    """
    # 清空输出目录
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    # 统计
    stats = {
        "total_files": 0,
        "total_tweets": 0,
        "total_images": 0,
        "personas": set()
    }

    # 处理所有JSON文件
    json_files = sorted(TWEETS_DIR.glob("*.json"))

    print(f"📁 找到 {len(json_files)} 个tweet batch文件")
    print(f"🖼️  图片目录: {IMAGES_DIR}")
    print(f"📤 输出目录: {OUTPUT_DIR}\n")

    for json_path in json_files:
        parsed = parse_json_filename(json_path.name)
        if not parsed:
            print(f"⚠️  跳过无法解析的文件: {json_path.name}")
            continue

        persona = parsed["persona"]
        day = parsed["day"]
        json_timestamp = parsed["timestamp"]

        stats["personas"].add(persona)
        stats["total_files"] += 1

        # 读取JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 获取所有slot编号
        slots = [tweet["slot"] for tweet in data["tweets"]]

        # 找到匹配的图片（传入day而不是timestamp）
        matched_images = find_matching_images(persona, day, slots)

        if not matched_images:
            print(f"⚠️  {persona} day {day}: 没有找到匹配的图片")
            continue

        # 创建输出目录 (日期/人物)
        output_persona_dir = OUTPUT_DIR / f"day_{day}" / persona
        output_persona_dir.mkdir(parents=True, exist_ok=True)

        # 准备索引数据
        index_data = {
            "persona": persona,
            "day": day,
            "date": data["daily_plan"]["date"],
            "tweets": []
        }

        # 复制图片并记录索引
        for tweet in data["tweets"]:
            slot = tweet["slot"]

            if slot not in matched_images:
                print(f"  ⚠️  Slot {slot} 没有匹配的图片")
                continue

            # 新的图片文件名
            new_image_name = f"tweet_{slot}_slot_{slot}.png"
            new_image_path = output_persona_dir / new_image_name

            # 复制图片
            shutil.copy2(matched_images[slot], new_image_path)

            # 记录到索引
            index_data["tweets"].append({
                "slot": slot,
                "time_segment": tweet.get("time_segment", "unknown"),
                "topic_type": tweet.get("topic_type", "unknown"),
                "tweet_text": tweet["tweet_text"],
                "image_file": new_image_name,
                "scene_hint": tweet["image_generation"]["scene_hint"]
            })

            stats["total_tweets"] += 1
            stats["total_images"] += 1

        # 写入索引文件
        index_path = output_persona_dir / "index.json"
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        print(f"✅ {persona} day {day}: {len(matched_images)} 张图片 → {output_persona_dir}")

    # 输出统计
    print("\n" + "="*70)
    print("📊 重组完成统计")
    print("="*70)
    print(f"✅ 处理文件数: {stats['total_files']}")
    print(f"✅ 总推文数: {stats['total_tweets']}")
    print(f"✅ 总图片数: {stats['total_images']}")
    print(f"✅ Persona数: {len(stats['personas'])}")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print("="*70)

    # 展示目录结构示例
    print("\n📂 目录结构示例:")
    days = sorted(OUTPUT_DIR.iterdir())[:3]  # 显示前3天
    for day_dir in days:
        if day_dir.is_dir():
            print(f"\n{day_dir.name}/")
            personas_in_day = sorted(day_dir.iterdir())[:2]  # 显示前2个人物
            for persona_dir in personas_in_day:
                if persona_dir.is_dir():
                    print(f"  ├── {persona_dir.name}/")
                    print(f"  │   ├── index.json")
                    images = list(persona_dir.glob("*.png"))
                    for img in images[:3]:
                        print(f"  │   ├── {img.name}")
                    if len(images) > 3:
                        print(f"  │   └── ... ({len(images)-3} more)")


if __name__ == "__main__":
    organize_images()
