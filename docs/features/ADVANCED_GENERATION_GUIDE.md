# 高级图片生成方案使用指南

## 概述

基于 ComfyUI workflow (`workflow/zimage-121101.json`) 实现的三阶段渐进式图片生成方案，作为当前系统的**优化方案**，原有单阶段生成作为**备用方案**。

## 核心特性

### 1. 三阶段渐进式生成（优化方案）

**生成流程**：
```
阶段1: 512×672 (基础生成) → CFG 2.0, Steps 9
阶段2: 640×832 (中间精修) → CFG 1.0, Steps 16, Denoise 0.7
阶段3: 768×1024 (最终精修) → CFG 1.0, Steps 16, Denoise 0.6
```

**优势**：
- ✅ 更高的图片质量（渐进式上采样保留更多细节）
- ✅ 更稳定的生成结果（低分辨率先确定构图，再逐步精修）
- ✅ 更好的真实感（配合负向提示词排除 AI 痕迹）

### 2. 中文/英文负向提示词模板

**位置**：
- 中文模板：`config/negative_prompts_zh.txt`
- 英文模板：`config/negative_prompts_en.txt`

**功能**：
- 排除动漫风格、AI 网红脸、美颜滤镜痕迹
- 排除影楼风、stock photo 感
- 排除过度修图、过度磨皮等非真实感

**默认使用**：英文模板（更好的兼容性）

### 3. Trigger Word 支持

支持在 `persona JSON` 或 `image_generation` 中指定 LoRA 触发词：

```json
{
  "persona": {
    "extensions": {
      "trigger_word": "your_lora_trigger_word"
    }
  }
}
```

或在推文批次中：

```json
{
  "tweets": [
    {
      "image_generation": {
        "trigger_word": "your_lora_trigger_word",
        "positive_prompt": "...",
        ...
      }
    }
  ]
}
```

## 配置文件

### `config/image_generation.yaml`

```yaml
# 生成模式选择
generation_mode: "advanced"  # "advanced" (优化方案) | "simple" (备用方案)

# 高级生成模式配置
advanced_generation:
  # 负向提示词
  negative_prompt:
    enabled: true
    template_file: "config/negative_prompts_en.txt"

  # 三阶段配置
  progressive:
    stage1:
      size: [512, 672]
      steps: 9
      cfg: 2.0

    stage2:
      size: [640, 832]
      steps: 16
      cfg: 1.0
      denoise: 0.7

    stage3:
      # size 由 generation.width/height 决定
      steps: 16
      cfg: 1.0
      denoise: 0.6
```

## 使用方法

### 方式1：通过配置文件切换方案

编辑 `config/image_generation.yaml`：

```yaml
# 使用优化方案（三阶段渐进式）
generation_mode: "advanced"

# 使用备用方案（单阶段生成）
generation_mode: "simple"
```

然后正常运行图片生成：

```bash
python main.py --generate-images \
  --tweets-batch output_standalone/my_character_*.json
```

### 方式2：通过代码强制指定方案

```python
from core.image_generator import ImageGenerationCoordinator

# 强制使用优化方案
coordinator = ImageGenerationCoordinator(use_advanced=True)

# 强制使用备用方案
coordinator = ImageGenerationCoordinator(use_advanced=False)

# 从配置文件读取（默认）
coordinator = ImageGenerationCoordinator(use_advanced=None)
```

### 方式3：直接调用高级生成器

```python
from core.image_generator_advanced import ZImageGeneratorAdvanced
from config.image_config import (
    get_progressive_config,
    load_negative_prompt_template
)

# 初始化生成器
generator = ZImageGeneratorAdvanced(
    model_path="Z-Image/ckpts/Z-Image-Turbo",
    device="cuda"
)

# 加载配置
progressive_config = get_progressive_config()
negative_prompt = load_negative_prompt_template()

# 生成图片（三阶段渐进式）
image = generator.generate_progressive(
    positive_prompt="photo of a woman...",
    negative_prompt=negative_prompt,
    trigger_word="",
    **progressive_config
)

# 或单阶段生成（备用方案）
image = generator.generate_simple(
    positive_prompt="photo of a woman...",
    negative_prompt=negative_prompt,
    trigger_word="",
    width=768,
    height=1024,
    steps=9,
    cfg=1.0
)
```

## 测试

### 快速测试

```bash
# 对比测试（生成两张图对比效果）
python test_advanced_generation.py --mode compare

# 只测试优化方案
python test_advanced_generation.py --mode advanced

# 只测试备用方案
python test_advanced_generation.py --mode simple
```

### 批量生成测试

```bash
# 生成 3 张测试图（使用优化方案）
python main.py --generate-images \
  --tweets-batch output_standalone/test.json \
  --max-images 3
```

## 性能对比

| 方案 | 生成时间 | 质量 | 真实感 | VRAM 占用 |
|------|----------|------|--------|-----------|
| 备用方案 (单阶段) | ~8s | 较好 | 中等 | ~8GB |
| 优化方案 (三阶段) | ~25s | 优秀 | 高 | ~8GB |

**说明**：
- 优化方案生成时间约为备用方案的 3 倍
- VRAM 占用相同（因为使用 img2img，不是 latent upscale）
- 质量和真实感显著提升

## 常见问题

### Q1: 如何切换回原来的单阶段生成？

**答**：编辑 `config/image_generation.yaml`，将 `generation_mode` 改为 `"simple"`：

```yaml
generation_mode: "simple"
```

### Q2: 负向提示词太长会影响性能吗？

**答**：不会。负向提示词只在文本编码时处理一次，不影响后续采样步骤。

### Q3: 可以自定义三阶段的尺寸吗？

**答**：可以，编辑 `config/image_generation.yaml` 中的 `advanced_generation.progressive` 部分：

```yaml
progressive:
  stage1:
    size: [512, 672]  # 修改为你想要的尺寸
  stage2:
    size: [640, 832]
  # stage3 的尺寸由 generation.width/height 决定
```

### Q4: 多 GPU 模式支持优化方案吗？

**答**：暂不支持。多 GPU 模式会自动回退到备用方案（单阶段生成）。

### Q5: 如何添加自定义负向提示词？

**答**：编辑 `config/negative_prompts_en.txt`（或 `negative_prompts_zh.txt`），添加你的负向词汇。注释行（以 `#` 开头）会被自动忽略。

### Q6: Trigger Word 从哪里读取？

**答**：优先级如下：
1. `tweet["image_generation"]["trigger_word"]`（单条推文级别）
2. `persona["extensions"]["trigger_word"]`（人设级别）
3. 如果都没有，则不使用 trigger word

## 技术细节

### 与 ComfyUI 工作流的差异

| ComfyUI 工作流 | 当前实现 | 原因 |
|----------------|----------|------|
| Latent 空间上采样 | 像素空间上采样 + img2img | Diffusers 不直接支持 latent upscale |
| FlowMatchEulerDiscreteScheduler | 默认 scheduler | 自定义 scheduler 需要深入修改 pipeline |
| Qwen CLIP 编码器 | 默认 T5 编码器 | Z-Image 默认使用 T5，切换到 Qwen 需要测试兼容性 |
| EasyCache 优化 | 无 | 性能优化功能，未实现 |

**核心保留特性**：
- ✅ 三阶段渐进式生成流程
- ✅ 每阶段的 steps、CFG、denoise 参数
- ✅ 负向提示词模板
- ✅ LoRA 支持

### 架构设计

```
config/image_generation.yaml (配置)
    ↓
config/image_config.py (配置加载)
    ↓
core/image_generator_advanced.py (高级生成器)
    ↓ (调用)
core/image_generator.py (协调器)
    ↓ (使用)
main.py (CLI 入口)
```

**关键设计**：
- 配置驱动：通过 YAML 配置切换方案，无需修改代码
- 向后兼容：原有代码无需修改，自动支持新旧方案切换
- 模块化：高级生成器独立文件，不影响原有生成器

## 后续优化方向

### 短期（已实现）
- ✅ 三阶段渐进式生成
- ✅ 负向提示词模板
- ✅ Trigger Word 支持
- ✅ 新旧方案配置切换

### 中期（待实现）
- ⏳ 多 GPU 支持优化方案
- ⏳ Latent 空间上采样（需要修改 Diffusers pipeline）
- ⏳ 自定义 Scheduler（FlowMatchEulerDiscreteScheduler）

### 长期（研究性质）
- ⏳ Qwen CLIP 集成（中文提示词增强）
- ⏳ EasyCache 优化（缓存中间计算结果）
- ⏳ 动态调整三阶段参数（根据内容自适应）

## 相关文档

- [工作流分析报告](docs/ZIMAGE_ADVANCED_WORKFLOW_ANALYSIS.md)
- [ComfyUI 原始工作流](workflow/zimage-121101.json)
- [图片生成配置文件](config/image_generation.yaml)

## 贡献者

- 基于 ComfyUI 社区的 Z-Image 工作流优化
- 适配到 Python async + Diffusers 架构
