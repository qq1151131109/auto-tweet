#!/usr/bin/env python3
"""
完整端到端测试: 生成10张图片 (4实例并行)
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from core.comfyui_client import ComfyUIPool, update_workflow_prompt


async def main():
    print("=" * 80)
    print("完整端到端测试: 生成10张图片 (4实例并行)")
    print("=" * 80)
    print()

    # 配置
    tweets_file = "output_standalone/Valeria \"Val\" Ortiz_20251211_071653.json"
    workflow_file = "workflow/zimage-api-121104.json"
    output_dir = "output_images_e2e"

    # 加载推文
    with open(tweets_file, 'r') as f:
        tweets_data = json.load(f)
    print(f"✓ 加载推文: {len(tweets_data['tweets'])} 条")

    # 加载工作流
    with open(workflow_file, 'r') as f:
        workflow_template = json.load(f)
    print(f"✓ 加载工作流: {workflow_file}")
    print()

    # 获取LoRA配置
    with open('personas/test_optimized.json', 'r') as f:
        persona_full = json.load(f)

    lora_config = persona_full.get('data', {}).get('lora', {})
    lora_path = lora_config.get('model_path', '')
    lora_strength = lora_config.get('strength', 0.8)
    trigger_words = lora_config.get('trigger_words', [])
    trigger_word = trigger_words[0] if trigger_words else ''

    print("LoRA配置:")
    print(f"  路径: {lora_path}")
    print(f"  强度: {lora_strength}")
    print(f"  触发词: {trigger_word}")
    print()

    # 创建ComfyUI客户端池 (4个实例)
    pool = ComfyUIPool(ports=[9000, 9001, 9002, 9003])
    print("✓ ComfyUI客户端池初始化完成 (4个实例)")
    print()

    # 创建输出目录
    Path(output_dir).mkdir(exist_ok=True)

    # 准备生成任务
    tasks = []
    for i, tweet in enumerate(tweets_data['tweets'], 1):
        img_gen = tweet.get('image_generation', {})
        scene_hint = img_gen.get('scene_hint', '')

        # 组装提示词
        positive_prompt = f"{trigger_word}, {scene_hint}".strip(', ')

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

        # 添加任务
        task = {
            'index': i,
            'workflow': workflow_updated,
            'output_dir': output_dir,
            'filename_prefix': f"e2e_{i:02d}",
            'content_type': tweet.get('content_type', 'unknown'),
            'tweet_text': tweet.get('tweet_text', '')[:50]  # 前50字符
        }
        tasks.append(task)

    # 并行生成
    print("🚀 开始并行生成图片...")
    print(f"   任务数: {len(tasks)}")
    print(f"   并发数: 4 (端口 9000-9003)")
    print()

    start_time = datetime.now()

    async def generate_one(task):
        """生成单张图片"""
        try:
            print(f"[{task['index']}/10] 正在生成... ({task['content_type']})", flush=True)

            result = await pool.generate_image(
                workflow=task['workflow'],
                output_dir=task['output_dir'],
                filename_prefix=task['filename_prefix']
            )

            if result.get('status') == 'success' and result.get('images'):
                output_path = result['images'][0]
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"✓ [{task['index']}/10] {output_path} (用时 {elapsed:.1f}s)")
                return {'status': 'success', 'index': task['index'], 'path': output_path}
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"✗ [{task['index']}/10] 失败: {error_msg}")
                return {'status': 'failed', 'index': task['index'], 'error': error_msg}

        except Exception as e:
            print(f"✗ [{task['index']}/10] 异常: {e}")
            return {'status': 'error', 'index': task['index'], 'error': str(e)}

    # 并行执行所有任务
    results = await asyncio.gather(*[generate_one(task) for task in tasks])

    # 统计结果
    end_time = datetime.now()
    total_elapsed = (end_time - start_time).total_seconds()

    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = len(results) - success_count

    print()
    print("=" * 80)
    print("生成完成!")
    print("=" * 80)
    print(f"✓ 成功: {success_count}/{len(tasks)} 张")
    if failed_count > 0:
        print(f"✗ 失败: {failed_count}/{len(tasks)} 张")
        print()
        print("失败的任务:")
        for r in results:
            if r['status'] != 'success':
                print(f"  [{r['index']}] {r.get('error', 'Unknown error')}")

    print()
    print(f"总用时: {total_elapsed:.1f}秒 ({total_elapsed/60:.1f}分钟)")
    print(f"平均每张: {total_elapsed/len(tasks):.1f}秒")
    if success_count > 0:
        print(f"成功图片平均: {total_elapsed/success_count:.1f}秒")
    print()
    print(f"输出目录: {output_dir}/")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
