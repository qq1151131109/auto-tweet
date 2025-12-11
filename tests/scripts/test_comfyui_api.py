#!/usr/bin/env python3
"""
测试 ComfyUI API 客户端
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.comfyui_client import ComfyUIPool, load_workflow_template, update_workflow_prompt


async def test_single_generation():
    """测试单张图片生成（使用新工作流 zimage-api-121102）"""
    print("🎨 测试 ComfyUI API 单张图片生成\n")

    # 初始化客户端池（只使用 9000 端口）
    pool = ComfyUIPool(ports=[9000])

    # 加载新工作流模板
    workflow_template = load_workflow_template("workflow/zimage-api-121102.json")
    print("✅ 工作流模板加载完成 (zimage-api-121102)\n")

    # 测试参数
    trigger_word = "sunway"  # LoRA 触发词（示例）

    # 场景描述（模拟 LLM 输出，已包含真实感修饰词）
    scene_description = (
        "curvy blonde woman with long braid and heavy tattoos, "
        "mirror selfie in green floral bikini, full body shot, "
        "pale skin, detailed ink on thighs and arms, plain background, "
        "soft lighting, "
        # 真实感修饰词（LLM 应该自动添加这些）
        "Raw photo, candid photography, authentic snapshot, "
        "messy background, uneven skin tone, Chromatic aberration"
    )

    # 不再添加"完美画质词"，这些应该由 LLM 在 scene_hint 中添加
    quality_words = ""  # 留空，让 scene_hint 自带的真实感词起作用

    lora_path = "lora/sunway.safetensors"  # LoRA 文件路径（示例）

    # 更新工作流
    workflow = update_workflow_prompt(
        workflow=workflow_template,
        positive_prompt=scene_description,
        trigger_word=trigger_word,
        quality_words=quality_words,  # 不传入画质词
        lora_path=lora_path,
        lora_strength=0.85,
        seed=12345
    )

    print(f"📝 触发词: {trigger_word}")
    print(f"📝 场景描述: {scene_description[:100]}...")
    print(f"📝 真实感修饰词: ✅ 已包含在场景描述中")
    print(f"📝 LoRA: {lora_path} (强度 0.85)")
    print(f"🎯 开始生成（通过 ComfyUI API）...\n")

    # 生成图片
    result = await pool.generate_image(
        workflow=workflow,
        output_dir="output_images",
        filename_prefix="test_comfyui_realism"
    )

    if result['status'] == 'success':
        print(f"\n✅ 生成成功！")
        print(f"   任务ID: {result['prompt_id']}")
        print(f"   图片: {result['images']}\n")
    else:
        print(f"\n❌ 生成失败: {result.get('error')}\n")


async def test_batch_generation():
    """测试批量并发生成"""
    print("🎨 测试 ComfyUI API 批量并发生成\n")

    # 初始化客户端池
    pool = ComfyUIPool(ports=[9000, 9001, 9002, 9003])

    # 加载工作流模板
    workflow_template = load_workflow_template("workflow/zimage-121101.json")

    # 创建3个测试工作流
    prompts = [
        "photo of a woman in a park, sunny day, natural lighting",
        "photo of a woman in a cafe, reading a book, cozy atmosphere",
        "photo of a woman on a beach, sunset, golden hour lighting"
    ]

    workflows = []
    for i, prompt in enumerate(prompts):
        workflow = update_workflow_prompt(
            workflow=workflow_template,
            positive_prompt=prompt,
            seed=10000 + i
        )
        workflows.append(workflow)

    print(f"📝 准备生成 {len(workflows)} 张图片")
    print(f"🎯 开始并发生成...\n")

    # 批量生成
    results = await pool.generate_batch(
        workflows=workflows,
        output_dir="output_images",
        filename_prefix="test_batch"
    )

    # 统计结果
    success_count = sum(1 for r in results if r.get('status') == 'success')
    print(f"\n✅ 批量生成完成")
    print(f"   成功: {success_count}/{len(results)}")
    print(f"   失败: {len(results) - success_count}/{len(results)}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="测试 ComfyUI API 客户端")
    parser.add_argument("--mode", choices=["single", "batch"], default="single",
                        help="测试模式: single (单张) 或 batch (批量)")

    args = parser.parse_args()

    if args.mode == "single":
        asyncio.run(test_single_generation())
    elif args.mode == "batch":
        asyncio.run(test_batch_generation())


if __name__ == "__main__":
    main()
