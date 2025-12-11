# Image Generation Research Report
# 图片生成流程研究报告与真实感优化方案

**日期**: 2025-12-10
**目标**: 分析当前图片生成流程，设计场景描述与模型提示词解耦方案，添加真实感画质词

---

## 一、当前系统架构分析

### 1.1 核心流程概览

当前系统的图片生成流程分为 **3个主要阶段**：

```
Stage 1: Tweet Generation (LLM)
  ├─ Input: persona + calendar_plan + context
  ├─ Process: LLM生成推文文本 + scene_hint
  └─ Output: tweet_text + scene_hint (自然语言场景描述)

Stage 2: Prompt Construction (代码层)
  ├─ Input: scene_hint (from Stage 1)
  ├─ Process: scene_hint → positive_prompt (直接复制)
  └─ Output: positive_prompt + negative_prompt + generation_params

Stage 3: Image Generation (Diffusers/Z-Image)
  ├─ Input: positive_prompt + negative_prompt + LoRA
  ├─ Process: Z-Image模型推理
  └─ Output: PNG图片文件
```

### 1.2 关键代码位置

**文件**: `core/tweet_generator.py`

#### 1.2.1 Scene Hint生成 (LLM阶段)

**位置**: `StandaloneTweetGenerator._build_system_prompt()` (line 81-244)

LLM被要求生成 80-150 词的自然语言场景描述，包含：
- 时间/地点
- 服装细节
- 姿势/肢体语言
- 面部表情
- 光照描述
- 相机角度
- 氛围

**示例输出** (来自实际生成的tweet):
```
"Morning in the driver's seat of a white SUV parked in suburban driveway,
soft overcast light coming through windshield, woman sitting upright wearing
pale yellow sundress with thin straps and loose cream cardigan slipping off
both shoulders, delicate gold cross necklace resting in the center of her
chest, seatbelt crossing diagonally tight between breasts pushing fabric
together, hands gripping steering wheel at 10 and 2, thighs pressed together
on warm leather seat, gentle flush on cheeks, lips slightly parted, medium
shot from passenger side showing upper body and lap, innocent eyes looking
forward with small knowing smile"
```

#### 1.2.2 Prompt构建 (代码层)

**位置**: `StandaloneTweetGenerator._parse_response()` (line 365-415)

**关键代码** (line 404-406):
```python
"image_generation": {
    "scene_hint": scene_hint,
    "positive_prompt": scene_hint,  # ⚠️ 直接复制，未做任何处理
    "negative_prompt": "ugly, deformed, noisy, blurry, low quality",
    ...
}
```

**问题识别**:
1. `positive_prompt = scene_hint` (完全相同)
2. 没有模型特定的提示词工程
3. 没有画质增强词
4. 没有真实感/自然感修饰词

#### 1.2.3 图片生成 (Diffusers层)

**文件**: `core/image_generator.py`

**位置**: `ZImageGenerator.generate_image()` (line 186-259)

```python
result = self.pipeline(
    prompt=positive_prompt,  # 直接使用从tweet_generator传来的prompt
    negative_prompt=negative_prompt,
    height=height,
    width=width,
    num_inference_steps=steps,
    guidance_scale=cfg,
    generator=generator
)
```

### 1.3 当前系统的优点

✅ **解耦良好的数据流**:
- Tweet文本 ← LLM生成
- Scene hint ← LLM生成 (作为语义描述)
- Image generation metadata ← 代码构建

✅ **灵活的输出格式**:
- JSON格式包含所有元数据
- 支持后续处理和修改

✅ **LoRA集成完善**:
- 支持动态加载/卸载
- 强度可配置

---

## 二、核心问题分析

### 2.1 耦合问题

**问题**: `scene_hint` 同时承担两个职责

| 职责 | 用途 | 理想格式 |
|------|------|---------|
| **语义场景描述** | 人类可读，理解推文配图内容 | 自然语言，80-150词 |
| **模型提示词** | 直接输入Z-Image/SDXL进行图片生成 | 模型特定格式，含画质词、风格词 |

**当前实现**: 一个`scene_hint`同时做两件事 → `positive_prompt = scene_hint`

**导致的问题**:
1. **模型迁移困难**: 如果从Z-Image换到SDXL，需要重新训练LLM生成不同风格的prompt
2. **画质词难以添加**: LLM生成的自然语言描述不包含`Raw photo`, `Shot on iPhone`等技术词汇
3. **提示词工程无法独立优化**: 无法在不改变LLM的情况下调整图片风格

### 2.2 AI感过重的原因

通过你提供的测试结果分析:

| 画质词 | 效果 | 风险 | 适用性 |
|--------|------|------|--------|
| `harsh flash` | ⭐⭐⭐ 闪光灯效果，但易产生光斑 | ⚠️ 高 | 选择性使用 |
| `messy background` | ⭐⭐⭐⭐ 背景凌乱，真实感强 | ✅ 低 | **推荐** |
| `authentic snapshot` | ⭐⭐⭐⭐⭐ 真实抓拍感 | ✅ 低 | **强烈推荐** |
| `motion blur` | ⭐⭐⭐ 运动模糊 | ⚠️ 中 (可能影响清晰度) | 少量使用 |
| `slightly out of focus` | ⭐⭐ 略微失焦 | ⚠️ 高 (容易失焦过度) | 谨慎使用 |
| `Raw photo` | ⭐⭐⭐⭐ 原始照片感 | ✅ 低 | **推荐** |
| `uneven skin tone` | ⭐⭐⭐⭐⭐ 非常有用 | ⚠️ 中 (可能肤色异常) | 推荐，需监控 |
| `Chromatic aberration` | ⭐⭐⭐ 色差效果 | ✅ 低 | 可选 |
| `Shot on iPhone` | ⭐⭐⭐⭐ 手机拍摄感 | ⚠️ 中 (可能出现手机实物) | 修改为更通用的描述 |

**根本原因**:
- 当前系统只有LLM生成的完美、文学化的场景描述
- 缺少技术层面的"瑕疵词"和"真实感修饰词"
- Z-Image默认生成"干净、完美"的AI图

---

## 三、解耦方案设计

### 3.1 架构设计

**新架构**: 分离语义层和技术层

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: Semantic Scene Description (语义层)                 │
│ ─────────────────────────────────────────────────────────   │
│ LLM生成: scene_hint (自然语言，80-150词)                      │
│ - 保持现有逻辑不变                                            │
│ - 专注语义描述：服装、姿势、环境、情绪                          │
│ - 模型无关，人类可读                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Prompt Engineering (技术层) - 新增                   │
│ ─────────────────────────────────────────────────────────   │
│ PromptEnhancer 类处理:                                        │
│   1. 场景描述 (scene_hint)                                    │
│   2. + 模型特定词 (model-specific tokens)                      │
│   3. + 画质增强词 (quality modifiers)                          │
│   4. + 真实感词 (authenticity modifiers)                       │
│   5. = 最终 positive_prompt                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: Image Generation                                    │
│ ─────────────────────────────────────────────────────────   │
│ Diffusers Pipeline (Z-Image/SDXL/etc.)                       │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心组件：PromptEnhancer

**新文件**: `core/prompt_enhancer.py`

```python
class PromptEnhancer:
    """
    提示词增强器 - 将语义场景描述转换为模型特定的提示词
    """

    def __init__(self, model_type="z-image", realism_level="medium"):
        """
        Args:
            model_type: "z-image" | "sdxl" | "flux"
            realism_level: "low" | "medium" | "high"
        """
        self.model_type = model_type
        self.realism_level = realism_level

    def enhance(self, scene_hint: str, **kwargs) -> Dict[str, str]:
        """
        增强场景描述，生成模型特定的提示词

        Returns:
            {
                "positive_prompt": "增强后的正向提示词",
                "negative_prompt": "增强后的负向提示词"
            }
        """
        # 1. 基础场景描述
        base_prompt = scene_hint

        # 2. 添加模型特定词
        model_tokens = self._get_model_specific_tokens()

        # 3. 添加真实感修饰词
        realism_tokens = self._get_realism_tokens()

        # 4. 组合
        positive_prompt = self._combine_tokens(
            base_prompt, model_tokens, realism_tokens
        )

        # 5. 增强负向提示词
        negative_prompt = self._get_enhanced_negative()

        return {
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt
        }
```

### 3.3 真实感词库设计

#### 3.3.1 分级策略

```python
REALISM_TOKENS = {
    "low": {
        # 保守：只添加基础真实感词，不影响质量
        "quality": ["Raw photo"],
        "authenticity": ["authentic snapshot"],
        "flaws": [],
        "weight": 0.3
    },

    "medium": {
        # 推荐：平衡真实感和质量
        "quality": ["Raw photo", "candid photography"],
        "authenticity": ["authentic snapshot", "natural moment"],
        "flaws": [
            "messy background",
            "uneven skin tone",
            "Chromatic aberration"
        ],
        "camera": ["smartphone camera aesthetic"],  # 避免"iPhone"实物
        "weight": 0.6
    },

    "high": {
        # 激进：最大化真实感，可能牺牲完美度
        "quality": ["Raw photo", "unedited photo", "candid shot"],
        "authenticity": [
            "authentic snapshot",
            "spontaneous moment",
            "caught off guard"
        ],
        "flaws": [
            "messy background",
            "uneven skin tone",
            "Chromatic aberration",
            "motion blur",
            "slightly out of focus",
            "harsh flash"
        ],
        "camera": [
            "smartphone camera aesthetic",
            "amateur photography",
            "personal photo"
        ],
        "weight": 0.9
    }
}
```

#### 3.3.2 智能组合规则

**规则1**: 根据场景动态选择

```python
def _select_realism_tokens_by_context(self, scene_hint: str) -> List[str]:
    """根据场景内容智能选择真实感词"""

    selected = []

    # 如果是运动场景 → 添加motion blur
    if any(word in scene_hint.lower() for word in
           ["walking", "running", "moving", "dancing"]):
        selected.append("motion blur")

    # 如果是夜间/室内昏暗 → 添加harsh flash
    if any(word in scene_hint.lower() for word in
           ["night", "dark", "dim", "evening"]):
        selected.append("harsh flash")

    # 如果是自拍/镜子 → 添加smartphone aesthetic
    if any(word in scene_hint.lower() for word in
           ["selfie", "mirror", "phone"]):
        selected.append("smartphone camera aesthetic")

    # 如果是户外/公共场所 → 添加messy background
    if any(word in scene_hint.lower() for word in
           ["street", "cafe", "outdoor", "park", "public"]):
        selected.append("messy background")

    return selected
```

**规则2**: 随机性 (避免所有图都一样)

```python
def _apply_random_variation(self, tokens: List[str]) -> List[str]:
    """随机选择部分token，增加多样性"""

    import random

    # 30%概率使用全部tokens
    if random.random() < 0.3:
        return tokens

    # 否则随机选择60-80%的tokens
    sample_size = int(len(tokens) * random.uniform(0.6, 0.8))
    return random.sample(tokens, sample_size)
```

### 3.4 模型特定适配

```python
class ZImagePromptEnhancer(PromptEnhancer):
    """Z-Image模型专用增强器"""

    def _get_model_specific_tokens(self):
        return {
            "prefix": [],  # Z-Image不需要特殊prefix
            "suffix": [
                "highly detailed",
                "professional photography"
            ]
        }

    def _get_enhanced_negative(self):
        return (
            "ugly, deformed, noisy, blurry, low quality, "
            "distorted, watermark, text, logo, "
            "artificial lighting, overexposed, oversaturated"
        )


class SDXLPromptEnhancer(PromptEnhancer):
    """SDXL模型专用增强器"""

    def _get_model_specific_tokens(self):
        return {
            "prefix": ["photograph of"],
            "suffix": [
                "8k resolution",
                "high detail",
                "cinematic lighting"
            ]
        }

    def _get_enhanced_negative(self):
        return (
            "cartoon, anime, 3d render, illustration, "
            "painting, drawing, art, sketch, "
            "ugly, deformed, blurry, low quality"
        )
```

---

## 四、实现方案

### 4.1 代码修改清单

#### 修改1: 创建 `core/prompt_enhancer.py`

```python
"""
Prompt增强器 - 将语义场景描述转换为模型特定提示词
"""
import random
from typing import Dict, List
from enum import Enum


class RealismLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PromptEnhancer:
    """提示词增强器基类"""

    def __init__(self, realism_level: RealismLevel = RealismLevel.MEDIUM):
        self.realism_level = realism_level
        self.realism_tokens = self._load_realism_tokens()

    def enhance(
        self,
        scene_hint: str,
        enable_realism: bool = True,
        enable_variation: bool = True
    ) -> Dict[str, str]:
        """
        增强场景描述

        Args:
            scene_hint: 原始场景描述（来自LLM）
            enable_realism: 是否启用真实感增强
            enable_variation: 是否启用随机变化

        Returns:
            {"positive_prompt": "...", "negative_prompt": "..."}
        """
        # 1. 基础描述
        base = scene_hint.strip()

        # 2. 模型特定tokens
        model_tokens = self._get_model_specific_tokens()

        # 3. 真实感tokens
        realism_tokens = []
        if enable_realism:
            realism_tokens = self._get_realism_tokens(scene_hint)
            if enable_variation:
                realism_tokens = self._apply_random_variation(realism_tokens)

        # 4. 组合
        positive_prompt = self._combine_prompt(
            base,
            model_tokens,
            realism_tokens
        )

        # 5. 负向提示词
        negative_prompt = self._get_enhanced_negative()

        return {
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt
        }

    def _load_realism_tokens(self) -> Dict:
        """加载真实感词库"""
        return {
            RealismLevel.LOW: {
                "quality": ["Raw photo"],
                "authenticity": ["authentic snapshot"],
                "flaws": [],
                "camera": []
            },
            RealismLevel.MEDIUM: {
                "quality": ["Raw photo", "candid photography"],
                "authenticity": ["authentic snapshot", "natural moment"],
                "flaws": [
                    "messy background",
                    "uneven skin tone",
                    "Chromatic aberration"
                ],
                "camera": ["smartphone camera aesthetic"]
            },
            RealismLevel.HIGH: {
                "quality": ["Raw photo", "unedited photo", "candid shot"],
                "authenticity": [
                    "authentic snapshot",
                    "spontaneous moment",
                    "caught off guard"
                ],
                "flaws": [
                    "messy background",
                    "uneven skin tone",
                    "Chromatic aberration",
                    "motion blur",
                    "slightly out of focus"
                ],
                "camera": [
                    "smartphone camera aesthetic",
                    "amateur photography",
                    "personal photo"
                ]
            }
        }

    def _get_realism_tokens(self, scene_hint: str) -> List[str]:
        """获取真实感tokens"""
        level_tokens = self.realism_tokens[self.realism_level]

        selected = []

        # 质量词（总是添加）
        selected.extend(level_tokens["quality"])

        # 真实感词（总是添加）
        selected.extend(level_tokens["authenticity"])

        # 相机词（总是添加）
        selected.extend(level_tokens["camera"])

        # 瑕疵词（根据场景智能选择）
        contextual_flaws = self._select_contextual_flaws(
            scene_hint,
            level_tokens["flaws"]
        )
        selected.extend(contextual_flaws)

        return selected

    def _select_contextual_flaws(
        self,
        scene_hint: str,
        available_flaws: List[str]
    ) -> List[str]:
        """根据场景内容智能选择瑕疵词"""
        scene_lower = scene_hint.lower()
        selected = []

        # motion blur: 运动场景
        if "motion blur" in available_flaws:
            if any(word in scene_lower for word in
                   ["walking", "running", "moving", "dancing", "jumping"]):
                selected.append("motion blur")

        # harsh flash: 夜间/昏暗场景
        if "harsh flash" in available_flaws:
            if any(word in scene_lower for word in
                   ["night", "dark", "dim", "evening", "low light"]):
                if random.random() < 0.3:  # 30%概率添加
                    selected.append("harsh flash")

        # messy background: 户外/公共场所
        if "messy background" in available_flaws:
            if any(word in scene_lower for word in
                   ["street", "cafe", "outdoor", "park", "public", "city"]):
                selected.append("messy background")

        # slightly out of focus: 随机添加（低概率）
        if "slightly out of focus" in available_flaws:
            if random.random() < 0.15:  # 15%概率
                selected.append("slightly out of focus")

        # 其他瑕疵词（始终添加）
        for flaw in available_flaws:
            if flaw not in selected and flaw in [
                "uneven skin tone",
                "Chromatic aberration"
            ]:
                selected.append(flaw)

        return selected

    def _apply_random_variation(self, tokens: List[str]) -> List[str]:
        """应用随机变化，增加多样性"""
        if len(tokens) <= 2:
            return tokens

        # 70%概率保留全部
        if random.random() < 0.7:
            return tokens

        # 否则随机保留70-90%
        keep_ratio = random.uniform(0.7, 0.9)
        keep_count = max(2, int(len(tokens) * keep_ratio))
        return random.sample(tokens, keep_count)

    def _combine_prompt(
        self,
        base: str,
        model_tokens: Dict,
        realism_tokens: List[str]
    ) -> str:
        """组合最终提示词"""
        parts = []

        # 前缀
        if model_tokens.get("prefix"):
            parts.extend(model_tokens["prefix"])

        # 基础描述
        parts.append(base)

        # 真实感修饰
        if realism_tokens:
            parts.append(", ".join(realism_tokens))

        # 后缀
        if model_tokens.get("suffix"):
            parts.extend(model_tokens["suffix"])

        return ", ".join(parts)

    # 以下方法由子类实现
    def _get_model_specific_tokens(self) -> Dict:
        raise NotImplementedError

    def _get_enhanced_negative(self) -> str:
        raise NotImplementedError


class ZImagePromptEnhancer(PromptEnhancer):
    """Z-Image模型专用增强器"""

    def _get_model_specific_tokens(self) -> Dict:
        return {
            "prefix": [],
            "suffix": []
        }

    def _get_enhanced_negative(self) -> str:
        return (
            "ugly, deformed, noisy, blurry, low quality, "
            "distorted, watermark, text, logo, "
            "artificial lighting, overexposed, oversaturated, "
            "perfect studio lighting, airbrushed skin"
        )


class SDXLPromptEnhancer(PromptEnhancer):
    """SDXL模型专用增强器"""

    def _get_model_specific_tokens(self) -> Dict:
        return {
            "prefix": ["photograph of"],
            "suffix": ["8k uhd", "dslr", "high quality"]
        }

    def _get_enhanced_negative(self) -> str:
        return (
            "cartoon, anime, 3d render, illustration, painting, drawing, "
            "art, sketch, ugly, deformed, blurry, low quality, "
            "artificial, airbrushed, perfect, flawless"
        )


# 工厂函数
def create_prompt_enhancer(
    model_type: str = "z-image",
    realism_level: str = "medium"
) -> PromptEnhancer:
    """
    创建提示词增强器

    Args:
        model_type: "z-image" | "sdxl"
        realism_level: "low" | "medium" | "high"
    """
    level = RealismLevel(realism_level)

    if model_type == "z-image":
        return ZImagePromptEnhancer(realism_level=level)
    elif model_type == "sdxl":
        return SDXLPromptEnhancer(realism_level=level)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
```

#### 修改2: 更新 `core/tweet_generator.py`

**在 `_parse_response()` 方法中**:

```python
def _parse_response(self, response: str, calendar_plan: Dict, persona: Dict) -> Dict:
    """解析LLM响应"""
    # ... 现有代码提取 scene_hint ...

    # ⭐ 新增：使用PromptEnhancer增强提示词
    from core.prompt_enhancer import create_prompt_enhancer

    enhancer = create_prompt_enhancer(
        model_type="z-image",  # 可配置
        realism_level="medium"  # 可配置
    )

    enhanced = enhancer.enhance(
        scene_hint=scene_hint,
        enable_realism=True,
        enable_variation=True
    )

    # ... 现有LoRA配置代码 ...

    return {
        "slot": calendar_plan.get("slot", 1),
        "time_segment": calendar_plan.get("recommended_time", ""),
        "topic_type": calendar_plan.get("topic_type", ""),
        "tweet_text": tweet_text,
        "image_generation": {
            "scene_hint": scene_hint,  # ⭐ 保留原始语义描述
            "positive_prompt": enhanced["positive_prompt"],  # ⭐ 使用增强后的提示词
            "negative_prompt": enhanced["negative_prompt"],  # ⭐ 使用增强后的负向词
            "lora_params": lora_params,
            "generation_params": {
                "width": 768,
                "height": 1024,
                "steps": 9,
                "cfg": 1.0
            }
        }
    }
```

### 4.2 配置系统

**新文件**: `config/image_generation.yaml`

```yaml
# 图片生成配置

model:
  type: "z-image"  # "z-image" | "sdxl" | "flux"
  path: "Z-Image/ckpts/Z-Image-Turbo"

prompt_enhancement:
  enabled: true
  realism:
    enabled: true
    level: "medium"  # "low" | "medium" | "high"
    variation: true  # 启用随机变化

  # 可手动覆盖tokens
  custom_tokens:
    quality: []
    authenticity: []
    flaws: []
    camera: []

generation:
  width: 768
  height: 1024
  steps: 9
  cfg: 1.0
```

加载配置:

```python
import yaml

def load_image_config():
    with open("config/image_generation.yaml") as f:
        return yaml.safe_load(f)

config = load_image_config()
enhancer = create_prompt_enhancer(
    model_type=config["model"]["type"],
    realism_level=config["prompt_enhancement"]["realism"]["level"]
)
```

---

## 五、对比分析

### 5.1 系统对比

| 维度 | 当前系统 | 新系统 |
|------|---------|--------|
| **scene_hint职责** | 语义描述 + 模型提示词 | 仅语义描述 |
| **positive_prompt来源** | 直接复制scene_hint | 经过PromptEnhancer处理 |
| **模型迁移难度** | 困难（需重新训练LLM） | 简单（只需切换Enhancer） |
| **真实感控制** | 无 | 分级可控（low/medium/high） |
| **提示词工程** | 无法独立优化 | 可独立迭代优化 |
| **多样性** | 依赖LLM随机性 | LLM随机性 + token随机采样 |

### 5.2 提示词对比示例

**原始scene_hint** (LLM生成，不变):
```
"Morning in the driver's seat of a white SUV parked in suburban driveway,
soft overcast light coming through windshield, woman sitting upright wearing
pale yellow sundress with thin straps and loose cream cardigan slipping off
both shoulders..."
```

**当前positive_prompt** (与scene_hint相同):
```
"Morning in the driver's seat of a white SUV parked in suburban driveway,
soft overcast light coming through windshield, woman sitting upright wearing
pale yellow sundress with thin straps and loose cream cardigan slipping off
both shoulders..."
```

**新系统positive_prompt** (经过增强):
```
"Morning in the driver's seat of a white SUV parked in suburban driveway,
soft overcast light coming through windshield, woman sitting upright wearing
pale yellow sundress with thin straps and loose cream cardigan slipping off
both shoulders..., Raw photo, candid photography, authentic snapshot,
natural moment, messy background, uneven skin tone, Chromatic aberration,
smartphone camera aesthetic"
```

**新系统negative_prompt** (增强版):
```
"ugly, deformed, noisy, blurry, low quality, distorted, watermark, text,
logo, artificial lighting, overexposed, oversaturated, perfect studio
lighting, airbrushed skin"
```

---

## 六、实施计划

### 6.1 Phase 1: 核心实现 (1-2天)

✅ **任务**:
1. 创建 `core/prompt_enhancer.py`
2. 实现 `ZImagePromptEnhancer` 类
3. 修改 `core/tweet_generator.py` 集成enhancer
4. 创建配置文件 `config/image_generation.yaml`

### 6.2 Phase 2: 测试与调优 (2-3天)

✅ **任务**:
1. 生成测试批次（10-20张图片）
2. 对比 `realism_level = low/medium/high` 效果
3. 调整token权重和选择规则
4. A/B测试：有无真实感词的对比

**测试脚本**:
```bash
# 生成对比测试
python main.py --test-realism \
  --persona personas/test.json \
  --levels low,medium,high \
  --samples 5
```

### 6.3 Phase 3: SDXL适配 (1天)

✅ **任务**:
1. 实现 `SDXLPromptEnhancer` 类
2. 测试SDXL模型生成效果
3. 调整SDXL专用tokens

### 6.4 Phase 4: 文档与部署 (1天)

✅ **任务**:
1. 撰写使用文档
2. 更新 CLAUDE.md
3. 添加配置示例
4. 提交到Git

---

## 七、风险与缓解

### 7.1 风险识别

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| **真实感词导致质量下降** | 中 | 高 | 1. 分级控制 (low/medium/high)<br>2. A/B测试验证<br>3. 保留关闭开关 |
| **特定token在Z-Image无效** | 中 | 中 | 1. 批量测试验证<br>2. 建立token效果库<br>3. 可配置token池 |
| **SDXL迁移后效果不理想** | 低 | 中 | 1. 独立的SDXLEnhancer<br>2. 模型专用token库 |
| **增加计算开销** | 低 | 低 | enhancer只是字符串拼接，开销可忽略 |

### 7.2 回退方案

如果新系统效果不佳，可通过配置一键回退:

```yaml
prompt_enhancement:
  enabled: false  # 关闭增强，回退到直接使用scene_hint
```

---

## 八、预期效果

### 8.1 质量提升

- ✅ **AI感降低**: 添加真实感词模拟手机拍摄
- ✅ **多样性增加**: 随机token采样避免千篇一律
- ✅ **可控性提升**: 分级控制真实感强度

### 8.2 系统优势

- ✅ **解耦清晰**: scene_hint只负责语义，prompt_engineering独立
- ✅ **易于迁移**: 切换模型只需更换Enhancer
- ✅ **便于优化**: 可独立调整真实感词库，无需重新训练LLM
- ✅ **向后兼容**: 保留scene_hint字段，不影响现有数据

---

## 九、结论与建议

### 9.1 核心结论

1. **当前系统的核心问题**: `scene_hint` 和 `positive_prompt` 完全相同，缺少模型特定的提示词工程和真实感修饰

2. **最佳解决方案**: 引入 `PromptEnhancer` 层，在LLM生成的语义描述基础上叠加模型特定词和真实感词

3. **真实感词策略**: 采用分级+智能选择+随机变化的组合策略，平衡真实感和质量

### 9.2 推荐配置

**生产环境推荐配置**:
```yaml
prompt_enhancement:
  enabled: true
  realism:
    level: "medium"  # 平衡真实感和质量
    variation: true  # 增加多样性
```

**实验性配置** (追求极致真实感):
```yaml
prompt_enhancement:
  enabled: true
  realism:
    level: "high"
    variation: true
```

### 9.3 下一步行动

1. **立即实施**: Phase 1 核心实现
2. **快速验证**: 生成50张测试图片对比效果
3. **迭代优化**: 根据效果调整token库和选择规则
4. **逐步推广**: 验证通过后全面启用

---

**报告完成时间**: 2025-12-10
**作者**: Claude Opus 4.5
**版本**: v1.0
