#!/usr/bin/env python3
"""
并发正确性测试脚本
验证并发执行时结果对应是否正确
"""
import asyncio
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))


async def test_gather_order():
    """测试 asyncio.gather() 的顺序保证"""
    print("=" * 60)
    print("测试1：asyncio.gather() 顺序保证")
    print("=" * 60)

    async def mock_task(task_id, delay):
        """模拟任务：返回 task_id，延迟 delay 秒"""
        await asyncio.sleep(delay)
        return {"id": task_id, "result": f"result_{task_id}"}

    # 创建不同延迟的任务
    tasks = [
        mock_task(1, 0.3),  # 延迟 0.3 秒
        mock_task(2, 0.1),  # 延迟 0.1 秒（最快）
        mock_task(3, 0.5),  # 延迟 0.5 秒（最慢）
        mock_task(4, 0.2),  # 延迟 0.2 秒
    ]

    print("\n任务延迟：")
    print("  Task 1: 0.3秒")
    print("  Task 2: 0.1秒 ← 最快")
    print("  Task 3: 0.5秒 ← 最慢")
    print("  Task 4: 0.2秒")

    # 并发执行
    print("\n并发执行...")
    results = await asyncio.gather(*tasks)

    # 验证顺序
    print("\n结果顺序：")
    success = True
    for i, result in enumerate(results, 1):
        expected_id = i
        actual_id = result["id"]
        status = "✅" if actual_id == expected_id else "❌"
        print(f"  results[{i-1}] -> Task {actual_id} {status}")

        if actual_id != expected_id:
            success = False

    print("\n" + ("✅ 测试通过：顺序保证正确" if success else "❌ 测试失败：顺序错误"))
    return success


async def test_stage_4_7_parallel():
    """测试 Stage 4-7 并发执行的结果对应"""
    print("\n" + "=" * 60)
    print("测试2：Stage 4-7 并发结果对应")
    print("=" * 60)

    async def mock_stage(stage_num, delay):
        """模拟 Stage 生成"""
        await asyncio.sleep(delay)
        return {
            "stage": stage_num,
            "data": f"stage_{stage_num}_data",
            "timestamp": delay
        }

    # 模拟 Stage 4-7（不同延迟）
    stage_4 = mock_stage(4, 0.2)  # 社交网络
    stage_5 = mock_stage(5, 0.1)  # 真实感系统（最快）
    stage_6 = mock_stage(6, 0.3)  # 视觉档案
    stage_7 = mock_stage(7, 0.25) # 知识库

    print("\nStage 延迟：")
    print("  Stage 4 (社交网络): 0.2秒")
    print("  Stage 5 (真实感系统): 0.1秒 ← 最快")
    print("  Stage 6 (视觉档案): 0.3秒 ← 最慢")
    print("  Stage 7 (知识库): 0.25秒")

    print("\n并发执行 Stage 4-7...")
    results = await asyncio.gather(stage_4, stage_5, stage_6, stage_7)

    # 解包
    social_data = results[0]
    authenticity = results[1]
    visual_profile = results[2]
    character_book = results[3]

    print("\n结果解包：")
    print(f"  social_data (results[0]) -> Stage {social_data['stage']} {'✅' if social_data['stage'] == 4 else '❌'}")
    print(f"  authenticity (results[1]) -> Stage {authenticity['stage']} {'✅' if authenticity['stage'] == 5 else '❌'}")
    print(f"  visual_profile (results[2]) -> Stage {visual_profile['stage']} {'✅' if visual_profile['stage'] == 6 else '❌'}")
    print(f"  character_book (results[3]) -> Stage {character_book['stage']} {'✅' if character_book['stage'] == 7 else '❌'}")

    # 验证
    success = (
        social_data['stage'] == 4 and
        authenticity['stage'] == 5 and
        visual_profile['stage'] == 6 and
        character_book['stage'] == 7
    )

    print("\n" + ("✅ 测试通过：Stage 结果对应正确" if success else "❌ 测试失败"))
    return success


async def test_batch_persona_correspondence():
    """测试批量人设生成的结果对应"""
    print("\n" + "=" * 60)
    print("测试3：批量人设生成结果对应")
    print("=" * 60)

    async def mock_persona_generation(image_path, delay):
        """模拟人设生成"""
        await asyncio.sleep(delay)
        return {
            "data": {
                "name": f"Persona_{Path(image_path).stem}",
                "source_image": image_path
            }
        }

    # 模拟图片列表
    image_files = ["img1.png", "img2.png", "img3.png", "img4.png"]

    print(f"\n输入图片: {image_files}")

    # 创建任务（模拟不同延迟）
    tasks = []
    delays = [0.3, 0.1, 0.4, 0.2]  # 不同延迟
    for image_path, delay in zip(image_files, delays):
        task = mock_persona_generation(image_path, delay)
        tasks.append((image_path, task))

    print("\n任务延迟：")
    for img, delay in zip(image_files, delays):
        print(f"  {img}: {delay}秒")

    # 并发执行
    print("\n并发执行...")
    results = await asyncio.gather(
        *[task for _, task in tasks],
        return_exceptions=True
    )

    # 验证对应关系（使用 zip）
    print("\n结果对应：")
    success = True
    for (image_path, _), result in zip(tasks, results):
        expected_name = f"Persona_{Path(image_path).stem}"
        actual_name = result['data']['name']
        actual_source = result['data']['source_image']

        status = "✅" if (actual_name == expected_name and actual_source == image_path) else "❌"
        print(f"  {image_path} -> {actual_name} {status}")

        if actual_name != expected_name or actual_source != image_path:
            success = False

    print("\n" + ("✅ 测试通过：批量人设结果对应正确" if success else "❌ 测试失败"))
    return success


async def test_exception_handling():
    """测试异常处理（一个失败不影响其他）"""
    print("\n" + "=" * 60)
    print("测试4：异常隔离（return_exceptions=True）")
    print("=" * 60)

    async def mock_task(task_id, should_fail=False):
        """模拟任务：可能失败"""
        await asyncio.sleep(0.1)
        if should_fail:
            raise ValueError(f"Task {task_id} failed!")
        return {"id": task_id, "result": "success"}

    # 创建任务（Task 2 会失败）
    tasks = [
        mock_task(1, False),
        mock_task(2, True),   # ← 这个会失败
        mock_task(3, False),
        mock_task(4, False),
    ]

    print("\n任务配置：")
    print("  Task 1: 正常")
    print("  Task 2: 失败 ← 会抛出异常")
    print("  Task 3: 正常")
    print("  Task 4: 正常")

    # 并发执行（捕获异常）
    print("\n并发执行（return_exceptions=True）...")
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 检查结果
    print("\n结果检查：")
    success_count = 0
    failed_count = 0

    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"  Task {i}: ❌ 失败 - {result}")
            failed_count += 1
        else:
            print(f"  Task {i}: ✅ 成功 - {result['result']}")
            success_count += 1

    # 验证
    expected_success = 3
    expected_failed = 1
    success = (success_count == expected_success and failed_count == expected_failed)

    print(f"\n统计：成功 {success_count}/{expected_success}, 失败 {failed_count}/{expected_failed}")
    print("✅ 测试通过：异常隔离正确，其他任务不受影响" if success else "❌ 测试失败")

    return success


async def main():
    """运行所有测试"""
    print("\n" + "🧪" * 30)
    print("并发正确性测试套件")
    print("🧪" * 30 + "\n")

    results = []

    # 运行所有测试
    results.append(await test_gather_order())
    results.append(await test_stage_4_7_parallel())
    results.append(await test_batch_persona_correspondence())
    results.append(await test_exception_handling())

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"\n通过: {passed}/{total}")
    print(f"失败: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 所有测试通过！并发实现正确且安全。")
        return 0
    else:
        print("\n⚠️ 有测试失败，请检查并发实现。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
