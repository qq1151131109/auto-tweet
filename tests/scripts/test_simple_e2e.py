#!/usr/bin/env python3
"""
简单的端到端测试: 生成3张图片验证
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.comfyui_client import ComfyUIPool, update_workflow_prompt


async def main():
    print("=" * 80)
    print("简单端到端测试: 生成3张图片")
    print("=" * 80)

    # 配置
    tweets_file = "output_standalone/Valeria \"Val\" Ortiz_20251211_071653.json"
    workflow_file = "workflow/zimage-api-121104.json"
    output_dir = "output_test_simple"

    # 加载推文
    with open(tweets_file, 'r') as f:
        tweets_data = json.load(f)
    print(f"✓ 加载推文: {len(tweets_data['tweets'])} 条")

    # 加载工作流
    with open(workflow_file, 'r') as f:
        workflow_template = json.load(f)
    print(f"✓ 加载工作流")

    # 获取LoRA配置
    with open('personas/test_optimized.json', 'r') as f:
        persona_full = json.load(f)

    lora_config = persona_full.get('data', {}).get('lora', {})
    lora_path = lora_config.get('model_path', '')
    lora_strength = lora_config.get('strength', 0.8)
    trigger_words = lora_config.get('trigger_words', [])
    trigger_word = trigger_words[0] if trigger_words else ''

    print(f"✓ LoRA: {lora_path} (强度 {lora_strength})")
    print()

    # 创建ComfyUI客户端池
    pool = ComfyUIPool(ports=[9000])
    print("✓ ComfyUI客户端池初始化完成")
    print()

    # 创建输出目录
    Path(output_dir).mkdir(exist_ok=True)

    # 生成3张图片
    print("🚀 开始生成图片...")
    print()

    success_count = 0
    for i in range(1, 4):  # 只生成3张
        print(f"[{i}/3] 正在生成...", end=" ", flush=True)

        tweet = tweets_data['tweets'][i-1]
        img_gen = tweet.get('image_generation', {})
        scene_hint = img_gen.get('scene_hint', '')

        # 组装提示词
        positive_prompt = f"{trigger_word}, {scene_hint}".strip(', ')

        try:
            # 更新工作流
            workflow_updated = update_workflow_prompt(
                workflow=workflow_template,
                positive_prompt=positive_prompt,
                negative_prompt="",
                trigger_word=trigger_word,
                quality_words="",
                lora_path=lora_path,
                lora_strength=lora_strength,
                seed=None
            )

            # 生成图片
            result = await pool.generate_image(
                workflow=workflow_updated,
                output_dir=output_dir,
                filename_prefix=f"test_{i:02d}"
            )

            if result.get('status') == 'success' and result.get('images'):
                output_path = result['images'][0]
                print(f"✓ {output_path}")
                success_count += 1
            else:
                print(f"✗ 失败: {result.get('error', 'Unknown')}")

        except Exception as e:
            print(f"✗ 异常: {e}")

    print()
    print("=" * 80)
    print(f"完成: {success_count}/3 张图片生成成功")
    print(f"输出目录: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
