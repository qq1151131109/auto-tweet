#!/usr/bin/env python3
"""
自动从personas JSON中提取LoRA配置并创建符号链接
"""
import json
import os
from pathlib import Path

# ComfyUI LoRA根目录
comfyui_lora_base = Path("/home/ubuntu/shenglin/ComfyUI/models/loras")

# 本地lora目录
local_lora_dir = Path("lora")
local_lora_dir.mkdir(exist_ok=True)

# 扫描所有personas
personas_dir = Path("personas")
lora_configs = {}

for persona_file in personas_dir.glob("*.json"):
    try:
        with open(persona_file, 'r', encoding='utf-8') as f:
            persona = json.load(f)

        lora_config = persona.get("data", {}).get("extensions", {}).get("lora", {})
        model_path = lora_config.get("model_path", "")

        if model_path and model_path.startswith("lora/"):
            filename = model_path.replace("lora/", "")
            lora_configs[filename] = {
                "persona": persona.get("data", {}).get("name", "Unknown"),
                "model_path": model_path
            }
    except Exception as e:
        print(f"⚠️  解析失败: {persona_file.name} - {e}")

print(f"找到 {len(lora_configs)} 个LoRA配置:\n")

# 尝试在ComfyUI目录中查找每个LoRA文件
for filename, config in lora_configs.items():
    print(f"📁 {filename} (for {config['persona']})")

    # 尝试查找文件
    possible_paths = [
        comfyui_lora_base / filename,
        comfyui_lora_base / "jfz" / filename.replace("jfz_", ""),
        comfyui_lora_base / "ai-toolkit-output" / filename.split('.')[0] / filename,
    ]

    found = False
    for path in possible_paths:
        if path.exists():
            target = local_lora_dir / filename
            if target.exists() or target.is_symlink():
                target.unlink()
            target.symlink_to(path)
            print(f"   ✅ 链接到: {path}")
            found = True
            break

    if not found:
        print(f"   ❌ 未找到文件，已尝试:")
        for p in possible_paths:
            print(f"      - {p}")

print(f"\n✅ 完成！请检查lora/目录")
