#!/usr/bin/env python3
"""
批量更新所有推文JSON文件中的steps参数
从28改为9
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

    # 更新每条推文的steps和cfg
    modified = False
    for tweet in data.get("tweets", []):
        gen_params = tweet.get("image_generation", {}).get("generation_params", {})
        if gen_params.get("steps") == 28:
            gen_params["steps"] = 9
            modified = True
        if gen_params.get("cfg") == 7.0:
            gen_params["cfg"] = 1.0
            modified = True

    if modified:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        updated_count += 1
        print(f"✓ 更新: {json_file.name}")

print(f"\n✅ 完成！更新了 {updated_count}/{len(json_files)} 个文件")
