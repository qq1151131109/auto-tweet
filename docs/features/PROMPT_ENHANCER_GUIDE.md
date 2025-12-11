# PromptEnhancer 使用指南

为Z-Image和SDXL模型添加真实感的提示词增强系统

---

## 🎯 功能概述

`PromptEnhancer` 是一个提示词增强系统，将LLM生成的纯语义场景描述转换为模型特定的提示词，添加真实感修饰词来降低AI感，模拟手机拍摄效果。

### 核心优势

- ✅ **解耦清晰**: scene_hint (语义) 与 positive_prompt (技术) 分离
- ✅ **模型无关**: 切换Z-Image↔SDXL只需修改配置
- ✅ **可控真实感**: 3级可调 (low/medium/high)
- ✅ **智能选择**: 根据场景内容动态添加词汇
- ✅ **易于优化**: 无需重新训练LLM，直接调整词库

---

## 📦 快速开始

### 1. 基础使用

```python
from core.prompt_enhancer import create_prompt_enhancer

# 创建enhancer
enhancer = create_prompt_enhancer(
    model_type="z-image",      # "z-image" | "sdxl"
    realism_level="medium"     # "low" | "medium" | "high"
)

# LLM生成的场景描述
scene_hint = "Morning in bedroom, woman wearing casual clothes..."

# 增强提示词
result = enhancer.enhance(scene_hint)

print("增强后的positive_prompt:", result["positive_prompt"])
print("增强后的negative_prompt:", result["negative_prompt"])
```

### 2. 便捷函数

```python
from core.prompt_enhancer import enhance_prompt

# 一键增强
result = enhance_prompt(
    "Morning in bedroom, woman wearing casual clothes...",
    model_type="z-image",
    realism_level="medium"
)
```

### 3. 从配置文件使用（推荐）

```python
from config.image_config import get_enhancer_from_config

# 使用默认配置
enhancer = get_enhancer_from_config()

# 使用预设
enhancer = get_enhancer_from_config(preset="authentic")
```

---

## 🎚️ 真实感级别

### LOW (保守)
**适用场景**: 首次测试，追求高质量

**添加词汇**:
- `Raw photo`, `authentic snapshot`

**特点**: 最小化真实感修饰，保持图片质量

---

### MEDIUM (推荐) ⭐
**适用场景**: 生产环境，大部分使用场景

**添加词汇**:
- 质量词: `Raw photo`, `candid photography`
- 真实感: `authentic snapshot`, `natural moment`
- 瑕疵词: `messy background`, `uneven skin tone`, `Chromatic aberration`
- 相机词: `smartphone camera aesthetic`
- 光照词: `low lighting` (夜间场景自动添加)

**特点**: 平衡真实感和质量，智能选择

---

### HIGH (激进)
**适用场景**: 追求极致真实感，可接受部分质量牺牲

**添加词汇**:
- MEDIUM级所有词汇 +
- 更多瑕疵: `motion blur`, `slightly out of focus`
- 更多相机: `GoPro lens`, `amateur photography`, `personal photo`
- 更多光照: `overexposed`, `underexposed`
- 运动感: `in motion`
- 氛围词: `eerie atmosphere` (特定场景)

**特点**: 最大化真实感，可能产生失焦/过曝等效果

---

## 🎨 模型对比

### Z-Image模式

**优化目标**: 真实感、自然感、手机拍摄风格

**负向提示词重点避免**:
- AI感、过度完美
- 人工棚拍光效
- 过度修图

**示例**:
```python
enhancer = create_prompt_enhancer("z-image", "medium")
```

### SDXL模式

**优化目标**: 高清晰度、摄影风格、专业质感（保留自然感）

**特殊处理**:
- 添加 `photograph of` 前缀
- 添加 `high detail`, `8k uhd`, `dslr` 后缀
- 使用更专业的摄影术语

**示例**:
```python
enhancer = create_prompt_enhancer("sdxl", "medium")
```

---

## ⚙️ 配置文件

配置文件位置: `config/image_generation.yaml`

### 基础配置

```yaml
model:
  type: "z-image"  # "z-image" | "sdxl"

prompt_enhancement:
  enabled: true  # 设为false回退到原始行为

  realism:
    enabled: true
    level: "medium"  # "low" | "medium" | "high"
    variation: true  # 启用随机变化

generation:
  width: 768
  height: 1024
  steps: 9
  cfg: 1.0
```

### 预设配置

配置文件包含4个预设:

#### 1. high_quality (高质量)
```yaml
realism:
  level: "low"
  variation: false
steps: 12
```

#### 2. balanced (平衡，推荐) ⭐
```yaml
realism:
  level: "medium"
  variation: true
steps: 9
```

#### 3. authentic (真实感)
```yaml
realism:
  level: "high"
  variation: true
steps: 9
```

#### 4. sdxl (SDXL模式)
```yaml
model:
  type: "sdxl"
realism:
  level: "medium"
width: 1024
height: 1024
steps: 30
cfg: 7.0
```

### 使用预设

```python
from config.image_config import load_preset

# 加载预设
config = load_preset("authentic")

# 获取enhancer配置
from config.image_config import get_prompt_enhancer_config
enhancer_config = get_prompt_enhancer_config(config)
```

---

## 🧠 智能选择规则

PromptEnhancer会根据场景内容智能添加词汇：

### 场景检测规则

| 检测关键词 | 自动添加词汇 | 概率 |
|----------|------------|------|
| `night`, `dark`, `evening`, `dim` | `low lighting` | 100% (HIGH级) |
| `sunlight`, `bright`, `outdoor` | `overexposed` | 20% (HIGH级) |
| `shadow`, `corner`, `room` | `underexposed` | 20% (HIGH级) |
| `walking`, `running`, `moving` | `motion blur` | 100% (HIGH级) |
| `street`, `cafe`, `outdoor`, `park` | `messy background` | 100% (MEDIUM+) |
| `night`, `abandoned`, `fog` | `eerie atmosphere` | 15% (HIGH级) |

### 示例

**场景**: "Late night in dark bedroom..."
**自动添加**: `low lighting`, `underexposed` (可能), `eerie atmosphere` (可能)

**场景**: "Outdoor cafe on busy street..."
**自动添加**: `messy background`, `overexposed` (可能)

---

## 🎲 随机变化

启用 `enable_variation=True` 后:

- 70%概率: 保留所有真实感词汇
- 30%概率: 随机保留70-90%的词汇

**作用**: 避免所有图片使用相同的修饰词，增加多样性

---

## 🔧 集成到现有系统

PromptEnhancer已集成到 `core/tweet_generator.py`:

```python
# core/tweet_generator.py 的 _parse_response() 方法中

# 加载配置
config = load_image_config()
enhancer_config = get_prompt_enhancer_config(config)

# 增强提示词
if enhancer_config["enabled"]:
    enhancer = create_prompt_enhancer(
        enhancer_config["model_type"],
        enhancer_config["realism_level"]
    )
    result = enhancer.enhance(scene_hint)
    positive_prompt = result["positive_prompt"]
    negative_prompt = result["negative_prompt"]
else:
    # 增强被禁用，使用原始scene_hint
    positive_prompt = scene_hint
    negative_prompt = "ugly, deformed, noisy, blurry, low quality"
```

**使用现有系统**:

```bash
# 修改配置文件 config/image_generation.yaml
# 然后正常运行tweet生成
python main.py --persona personas/test.json --tweets 5
```

---

## 🧪 测试与验证

### 运行测试脚本

```bash
python test_prompt_enhancer.py
```

测试脚本会演示:
1. Z-Image的3个真实感级别效果
2. SDXL的3个真实感级别效果
3. 智能选择功能（不同场景）
4. 便捷函数使用

### 对比测试

生成A/B测试图片:

```bash
# 方案A: 不使用增强 (配置中设置 enabled: false)
python main.py --persona test.json --tweets 5 --output output_a

# 方案B: 使用增强 (配置中设置 enabled: true, level: medium)
python main.py --persona test.json --tweets 5 --output output_b

# 比较 output_a/*.png 和 output_b/*.png
```

---

## 📊 效果对比

### 原始系统

**positive_prompt** = scene_hint (纯语义描述)
```
"Morning in bedroom, woman wearing casual clothes, sitting on bed..."
```

### 使用PromptEnhancer (MEDIUM级)

**positive_prompt** = scene_hint + 真实感词
```
"Morning in bedroom, woman wearing casual clothes, sitting on bed...,
Raw photo, candid photography, authentic snapshot, natural moment,
messy background, uneven skin tone, Chromatic aberration,
smartphone camera aesthetic"
```

### 预期改善

- ✅ AI感降低 30-50%
- ✅ 更接近手机拍摄效果
- ✅ 肤色更自然（略微不均匀）
- ✅ 背景更真实（适度凌乱）
- ✅ 光照更自然（可能略微过曝/欠曝）

---

## 🚨 注意事项

### 1. 质量权衡

真实感 ↑ = 完美度 ↓

- LOW级: 几乎无质量损失
- MEDIUM级: 轻微质量损失（可接受）
- HIGH级: 明显质量损失（失焦/过曝风险）

### 2. 特定词汇风险

| 词汇 | 风险 | 建议 |
|------|------|------|
| `slightly out of focus` | 容易过度失焦 | 仅HIGH级，15%概率 |
| `harsh flash` | 易产生光斑 | 仅HIGH级，30%概率 |
| `overexposed` | 可能过曝严重 | 仅HIGH级，20%概率 |
| `GoPro lens` | 广角畸变 | 仅HIGH级 |
| `eerie atmosphere` | 阴森感过重 | 仅特定场景，15%概率 |

### 3. 模型兼容性

- Z-Image: 所有测试词汇均有效
- SDXL: 使用更专业的摄影术语
- 其他模型: 可能需要调整词库

---

## 🛠️ 自定义词库

在配置文件中覆盖默认词库:

```yaml
experimental:
  custom_realism_tokens:
    quality: ["手机拍摄", "原片直出"]
    authenticity: ["真实抓拍", "自然瞬间"]
    flaws: ["背景杂乱", "肤色不均"]
    camera: ["iPhone 15拍摄"]
    lighting: ["弱光环境"]
    atmosphere: ["昏暗氛围"]
```

**注意**: 自定义词库会完全替换默认值（而不是追加）

---

## 📝 常见问题

### Q1: 如何关闭增强功能？

**方法1**: 配置文件
```yaml
prompt_enhancement:
  enabled: false
```

**方法2**: 代码
```python
enhancer.enhance(scene_hint, enable_realism=False)
```

### Q2: 如何切换到SDXL？

修改配置文件:
```yaml
model:
  type: "sdxl"

generation:
  width: 1024
  height: 1024
  steps: 30
  cfg: 7.0
```

或使用预设:
```python
config = load_preset("sdxl")
```

### Q3: 真实感词会影响LoRA吗？

不会。真实感词只修饰场景/光照/质感，不影响人物外貌。LoRA仍然控制人物特征。

### Q4: 如何调整真实感强度？

三种方法:
1. 修改level: `low` → `medium` → `high`
2. 关闭variation: 减少随机性
3. 自定义词库: 精确控制每个类别的词汇

### Q5: 为什么有些图片没有某些效果词？

因为启用了智能选择和随机变化:
- 智能选择: 只在相关场景添加（如夜间才加`low lighting`）
- 随机变化: 30%概率随机省略部分词汇

---

## 📚 参考资料

- [研究报告](IMAGE_GENERATION_RESEARCH_REPORT.md) - 详细架构设计
- [测试脚本](../test_prompt_enhancer.py) - 功能演示
- [配置文件](../config/image_generation.yaml) - 完整配置说明
- [源代码](../core/prompt_enhancer.py) - 实现细节

---

**版本**: v1.0
**最后更新**: 2025-12-10
