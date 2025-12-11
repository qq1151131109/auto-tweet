#!/usr/bin/env python3
"""
批量更新所有推文JSON文件，添加LoRA配置到每条tweet
从persona级别的lora配置复制到tweets[].image_generation.lora_params
"""
import json
from pathlib import Path

output_dir = Path("output_standalone")
json_files = list(output_dir.glob("*.json"))

print(f"找到 {len(json_files)} 个JSON文件")

updated_count = 0
for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 获取persona级别的LoRA配置
    persona_lora = data.get("persona", {}).get("lora", {})

    if not persona_lora or not persona_lora.get("model_path"):
        print(f"⚠️  跳过（无LoRA配置）: {json_file.name}")
        continue

    # 准备要填充的lora_params
    lora_params = {
        "model_path": persona_lora.get("model_path", ""),
        "strength": persona_lora.get("strength", 0.8)
    }

    # 更新每条推文的lora_params
    modified = False
    for tweet in data.get("tweets", []):
        current_lora = tweet.get("image_generation", {}).get("lora_params", {})
        # 只有当lora_params为空或缺少model_path时才更新
        if not current_lora or not current_lora.get("model_path"):
            tweet["image_generation"]["lora_params"] = lora_params
            modified = True

    if modified:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        updated_count += 1
        print(f"✓ 更新: {json_file.name} (LoRA: {lora_params['model_path']})")

print(f"\n✅ 完成！更新了 {updated_count}/{len(json_files)} 个文件")
