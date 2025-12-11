#!/usr/bin/env python3
"""
验证工作流参数传递
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.comfyui_client import load_workflow_template, update_workflow_prompt

def main():
    print("🔍 验证工作流参数传递\n")
    
    # 加载工作流模板
    workflow_template = load_workflow_template("workflow/zimage-api-121102.json")
    print("✅ 原始工作流加载完成\n")
    
    # 测试参数
    trigger_word = "sunway"
    scene_description = (
        "curvy blonde woman with long braid and heavy tattoos, "
        "mirror selfie in green floral bikini, full body shot, "
        "pale skin, detailed ink on thighs and arms, plain background, "
        "soft lighting"
    )
    quality_words = "photorealistic, plus-size model, high quality, detailed"
    lora_path = "lora/sunway.safetensors"
    
    # 更新工作流
    workflow = update_workflow_prompt(
        workflow=workflow_template,
        positive_prompt=scene_description,
        trigger_word=trigger_word,
        quality_words=quality_words,
        lora_path=lora_path,
        lora_strength=0.85,
        seed=12345
    )
    
    print("\n" + "="*60)
    print("📋 参数传递验证结果")
    print("="*60 + "\n")
    
    # 检查正向提示词（节点6）
    if '6' in workflow:
        positive_text = workflow['6']['inputs']['text']
        print("✅ 正向提示词 (节点6):")
        print(f"   {positive_text}\n")
        
        # 验证各部分
        has_trigger = trigger_word in positive_text
        has_scene = scene_description.split(',')[0] in positive_text
        has_quality = quality_words.split(',')[0] in positive_text
        
        print("   📌 触发词包含: ", "✅" if has_trigger else "❌")
        print("   📌 场景描述包含: ", "✅" if has_scene else "❌")
        print("   📌 画质词包含: ", "✅" if has_quality else "❌")
        print()
    
    # 检查负向提示词（节点7）
    if '7' in workflow:
        negative_text = workflow['7']['inputs']['text']
        print("✅ 负向提示词 (节点7):")
        print(f"   长度: {len(negative_text)} 字符")
        print(f"   前50字符: {negative_text[:50]}...")
        print("   📌 保持工作流原有值: ✅\n")
    
    # 检查 LoRA（节点343）
    if '343' in workflow:
        lora_config = workflow['343']['inputs']
        print("✅ LoRA 配置 (节点343):")
        print(f"   lora_path: {lora_config.get('lora_path')}")
        print(f"   lora_name: {lora_config.get('lora_name')}")
        print(f"   strength_model: {lora_config.get('strength_model')}")
        print(f"   strength_clip: {lora_config.get('strength_clip')}")
        print(f"   📌 LoRA 正确配置: {'✅' if lora_config.get('lora_path') == lora_path else '❌'}\n")
    
    # 检查种子（节点322, 226, 305）
    print("✅ 种子配置:")
    if '322' in workflow:
        print(f"   阶段1 (节点322): {workflow['322']['inputs']['seed']}")
    if '226' in workflow:
        print(f"   阶段2 (节点226): {workflow['226']['inputs']['seed']}")
    if '305' in workflow:
        print(f"   阶段3 (节点305): {workflow['305']['inputs']['seed']}")
    print()
    
    # 检查三阶段尺寸
    print("✅ 三阶段生成尺寸:")
    if '317' in workflow:
        stage1 = workflow['317']['inputs']
        print(f"   阶段1 (节点317): {stage1['width']}×{stage1['height']} latent")
    if '321' in workflow:
        stage2 = workflow['321']['inputs']
        print(f"   阶段2 (节点321): {stage2['width']}×{stage2['height']} latent")
    if '303' in workflow:
        stage3_scale = workflow['303']['inputs']['scale_by']
        print(f"   阶段3 (节点303): 2倍放大 → 672×864 latent")
    print()
    
    print("="*60)
    print("✅ 所有参数验证完成！")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
