#!/usr/bin/env python3
"""
给persona文件添加LoRA配置
"""
import json
from pathlib import Path

# Persona名称 → LoRA文件映射
LORA_MAPPING = {
    "hollyjai_corporate.json": {
        "model_path": "lora/hollyjai.safetensors",
        "strength": 0.8
    },
    "byrecarvalho_fitness.json": {
        "model_path": "lora/byrecarvalho.safetensors",
        "strength": 0.8
    },
    "jazmynmakenna_taboo.json": {
        "model_path": "lora/jazmynmakenna.safetensors",
        "strength": 0.8
    },
    "jfz_131_princess.json": {
        "model_path": "lora/jfz_131.safetensors",
        "strength": 0.8
    },
    "jfz_45_soft_domme.json": {
        "model_path": "lora/jfz_45.safetensors",
        "strength": 0.8
    },
}

def add_lora_to_persona(persona_file: Path, lora_config: dict):
    """给persona文件添加LoRA配置"""
    with open(persona_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 确保扩展字段存在
    if 'extensions' not in data['data']:
        data['data']['extensions'] = {}

    # 添加LoRA配置
    data['data']['extensions']['lora_config'] = lora_config

    # 保存
    with open(persona_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ {persona_file.name}: 已添加LoRA配置")


def main():
    personas_dir = Path("personas")

    for filename, lora_config in LORA_MAPPING.items():
        persona_file = personas_dir / filename
        if not persona_file.exists():
            print(f"✗ {filename}: 文件不存在,跳过")
            continue

        add_lora_to_persona(persona_file, lora_config)

    print(f"\n完成! 已更新 {len(LORA_MAPPING)} 个persona文件")


if __name__ == "__main__":
    main()
