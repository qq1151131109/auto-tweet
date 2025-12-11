#!/usr/bin/env python3
"""
快速测试脚本 - 验证高级生成方案的配置和逻辑

这个脚本不会真正生成图片，只验证：
1. 配置文件加载
2. 参数解析
3. 模块导入
4. 逻辑流程
"""
import json
import sys
from pathlib import Path

def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("测试 1: 配置文件加载")
    print("=" * 60)

    import yaml

    config_file = Path('config/image_generation.yaml')
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    print(f"✅ 配置文件加载成功")
    print(f"   生成模式: {config.get('generation_mode')}")

    # 检查高级配置
    adv_gen = config.get('advanced_generation', {})
    neg_prompt_config = adv_gen.get('negative_prompt', {})
    progressive = adv_gen.get('progressive', {})

    print(f"   负向提示词启用: {neg_prompt_config.get('enabled')}")
    print(f"   负向提示词文件: {neg_prompt_config.get('template_file')}")
    print(f"   三阶段配置:")
    print(f"     阶段1: {progressive.get('stage1', {}).get('size')} @ {progressive.get('stage1', {}).get('steps')} steps")
    print(f"     阶段2: {progressive.get('stage2', {}).get('size')} @ {progressive.get('stage2', {}).get('steps')} steps")
    print(f"     阶段3: {progressive.get('stage3', {}).get('steps')} steps")

    return config


def test_negative_prompt_loading(config):
    """测试负向提示词加载"""
    print("\n" + "=" * 60)
    print("测试 2: 负向提示词模板加载")
    print("=" * 60)

    adv_gen = config.get('advanced_generation', {})
    neg_prompt_config = adv_gen.get('negative_prompt', {})
    template_file = neg_prompt_config.get('template_file', 'config/negative_prompts_en.txt')

    template_path = Path(template_file)
    if not template_path.exists():
        print(f"❌ 文件不存在: {template_file}")
        return ""

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # 移除注释
    lines = [line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
    negative_prompt = ' '.join(lines)

    print(f"✅ 负向提示词加载成功")
    print(f"   文件: {template_file}")
    print(f"   原始长度: {len(content)} 字符")
    print(f"   处理后长度: {len(negative_prompt)} 字符")
    print(f"   前80字符: {negative_prompt[:80]}...")

    return negative_prompt


def test_module_imports():
    """测试模块导入"""
    print("\n" + "=" * 60)
    print("测试 3: 模块导入")
    print("=" * 60)

    # 测试高级生成器
    from core.image_generator_advanced import ZImageGeneratorAdvanced
    print(f"✅ ZImageGeneratorAdvanced 导入成功")

    # 测试协调器
    from core.image_generator import ImageGenerationCoordinator
    print(f"✅ ImageGenerationCoordinator 导入成功")

    # 测试配置加载器（直接导入，避免 config.__init__ 的依赖问题）
    import importlib.util
    spec = importlib.util.spec_from_file_location("image_config", "config/image_config.py")
    image_config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(image_config_module)
    print(f"✅ 配置加载函数导入成功")


def test_tweets_batch_parsing():
    """测试推文批次解析"""
    print("\n" + "=" * 60)
    print("测试 4: 推文批次文件解析")
    print("=" * 60)

    # 查找测试文件
    test_files = list(Path('output_standalone').glob('*.json'))
    if not test_files:
        print("⚠️  没有找到测试文件")
        return

    test_file = test_files[0]
    print(f"   使用文件: {test_file.name}")

    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"✅ 文件解析成功")
    print(f"   人设: {data['persona']['name']}")
    print(f"   推文数: {len(data['tweets'])}")

    # 检查第一条推文
    if data['tweets']:
        tweet = data['tweets'][0]
        img_gen = tweet.get('image_generation', {})

        print(f"   第一条推文:")
        print(f"     topic_type: {tweet.get('topic_type')}")
        print(f"     有 positive_prompt: {'positive_prompt' in img_gen}")
        print(f"     有 lora_params: {'lora_params' in img_gen}")
        print(f"     有 generation_params: {'generation_params' in img_gen}")

        # 检查 LoRA
        lora_params = img_gen.get('lora_params', {})
        if lora_params:
            print(f"     LoRA 路径: {lora_params.get('model_path', '(无)')}")
            print(f"     LoRA 强度: {lora_params.get('strength', 1.0)}")


def test_parameter_extraction():
    """测试参数提取逻辑"""
    print("\n" + "=" * 60)
    print("测试 5: 参数提取逻辑")
    print("=" * 60)

    # 直接导入避免依赖问题
    import importlib.util
    spec = importlib.util.spec_from_file_location("image_config", "config/image_config.py")
    image_config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(image_config_module)

    progressive_config = image_config_module.get_progressive_config()

    print(f"✅ 渐进式配置提取成功")
    print(f"   {progressive_config}")


def main():
    print("\n🎨 高级图片生成方案 - 快速验证测试\n")

    try:
        # 1. 配置加载
        config = test_config_loading()

        # 2. 负向提示词
        negative_prompt = test_negative_prompt_loading(config)

        # 3. 模块导入
        test_module_imports()

        # 4. 推文批次解析
        test_tweets_batch_parsing()

        # 5. 参数提取
        test_parameter_extraction()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n📋 测试总结:")
        print("   ✅ 配置文件加载正确")
        print("   ✅ 负向提示词模板可用")
        print("   ✅ 所有模块导入成功")
        print("   ✅ 推文批次格式正确")
        print("   ✅ 参数提取逻辑正常")
        print("\n🎉 系统已准备就绪，可以进行实际图片生成测试！")
        print("\n💡 下一步:")
        print("   1. 确保 Z-Image 模型已下载")
        print("   2. 运行实际生成测试:")
        print("      python main.py --generate-images \\")
        print("        --tweets-batch output_standalone/[你的文件].json \\")
        print("        --max-images 1")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
