"""
Prompt增强器 - 将语义场景描述转换为模型特定提示词

核心设计：
1. scene_hint (LLM生成) = 纯语义描述，模型无关
2. PromptEnhancer = 添加模型特定的画质词、真实感词
3. positive_prompt = scene_hint + 增强词

支持模型：
- Z-Image: 优化真实感、手机拍摄感
- SDXL: 优化高清质感、摄影风格
"""
import random
from typing import Dict, List, Optional
from enum import Enum


class RealismLevel(Enum):
    """真实感级别"""
    LOW = "low"          # 保守：基础真实感，不影响质量
    MEDIUM = "medium"    # 推荐：平衡真实感和质量
    HIGH = "high"        # 激进：最大化真实感，可能牺牲完美度


class PromptEnhancer:
    """提示词增强器基类"""

    def __init__(self, realism_level: RealismLevel = RealismLevel.MEDIUM):
        """
        Args:
            realism_level: 真实感级别 (LOW/MEDIUM/HIGH)
        """
        self.realism_level = realism_level
        self.realism_tokens = self._load_realism_tokens()

    def enhance(
        self,
        scene_hint: str,
        enable_realism: bool = True,
        enable_variation: bool = True
    ) -> Dict[str, str]:
        """
        增强场景描述，生成模型特定的提示词

        Args:
            scene_hint: 原始场景描述（来自LLM，纯语义）
            enable_realism: 是否启用真实感增强
            enable_variation: 是否启用随机变化（避免千篇一律）

        Returns:
            {
                "positive_prompt": "增强后的正向提示词",
                "negative_prompt": "增强后的负向提示词"
            }
        """
        # 1. 基础描述（保持不变）
        base = scene_hint.strip()

        # 2. 模型特定tokens
        model_tokens = self._get_model_specific_tokens()

        # 3. 真实感tokens
        realism_tokens = []
        if enable_realism:
            realism_tokens = self._get_realism_tokens(scene_hint)
            if enable_variation:
                realism_tokens = self._apply_random_variation(realism_tokens)

        # 4. 组合最终提示词
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

    def _load_realism_tokens(self) -> Dict[RealismLevel, Dict[str, List[str]]]:
        """
        加载真实感词库

        Returns:
            {
                RealismLevel.LOW: {
                    "quality": [...],
                    "authenticity": [...],
                    "flaws": [...],
                    "camera": [...]
                },
                ...
            }
        """
        return {
            RealismLevel.LOW: {
                "quality": ["Raw photo"],
                "authenticity": ["authentic snapshot"],
                "flaws": [],
                "camera": [],
                "lighting": [],
                "atmosphere": []
            },
            RealismLevel.MEDIUM: {
                "quality": ["Raw photo", "candid photography"],
                "authenticity": ["authentic snapshot", "natural moment"],
                "flaws": [
                    "messy background",
                    "uneven skin tone",
                    "Chromatic aberration"
                ],
                "camera": ["smartphone camera aesthetic"],
                "lighting": ["low lighting"],  # 低光照环境
                "atmosphere": []
            },
            RealismLevel.HIGH: {
                "quality": ["Raw photo", "unedited photo", "candid shot"],
                "authenticity": [
                    "authentic snapshot",
                    "spontaneous moment",
                    "caught off guard",
                    "in motion"  # 运动中拍摄
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
                    "personal photo",
                    "GoPro lens"  # 广角镜头效果
                ],
                "lighting": [
                    "low lighting",
                    "overexposed",     # 过曝
                    "underexposed"     # 欠曝
                ],
                "atmosphere": ["eerie atmosphere"]  # 神秘/怪异氛围（特定场景）
            }
        }

    def _get_realism_tokens(self, scene_hint: str) -> List[str]:
        """
        获取真实感tokens

        Args:
            scene_hint: 场景描述（用于智能选择）

        Returns:
            选中的真实感token列表
        """
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

        # 光照词（根据场景智能选择）
        contextual_lighting = self._select_contextual_lighting(
            scene_hint,
            level_tokens["lighting"]
        )
        selected.extend(contextual_lighting)

        # 氛围词（根据场景智能选择）
        contextual_atmosphere = self._select_contextual_atmosphere(
            scene_hint,
            level_tokens["atmosphere"]
        )
        selected.extend(contextual_atmosphere)

        return selected

    def _select_contextual_flaws(
        self,
        scene_hint: str,
        available_flaws: List[str]
    ) -> List[str]:
        """
        根据场景内容智能选择瑕疵词

        Args:
            scene_hint: 场景描述
            available_flaws: 当前级别可用的瑕疵词

        Returns:
            根据场景选中的瑕疵词
        """
        scene_lower = scene_hint.lower()
        selected = []

        # motion blur: 运动场景
        if "motion blur" in available_flaws:
            if any(word in scene_lower for word in
                   ["walking", "running", "moving", "dancing", "jumping", "action"]):
                selected.append("motion blur")

        # harsh flash: 夜间/昏暗场景（低概率，避免过度使用）
        if "harsh flash" in available_flaws:
            if any(word in scene_lower for word in
                   ["night", "dark", "dim", "evening", "low light", "club"]):
                if random.random() < 0.3:  # 30%概率添加
                    selected.append("harsh flash")

        # messy background: 户外/公共场所
        if "messy background" in available_flaws:
            if any(word in scene_lower for word in
                   ["street", "cafe", "outdoor", "park", "public", "city", "restaurant"]):
                selected.append("messy background")

        # slightly out of focus: 随机添加（低概率，避免过度失焦）
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

    def _select_contextual_lighting(
        self,
        scene_hint: str,
        available_lighting: List[str]
    ) -> List[str]:
        """
        根据场景内容智能选择光照词

        Args:
            scene_hint: 场景描述
            available_lighting: 当前级别可用的光照词

        Returns:
            根据场景选中的光照词
        """
        if not available_lighting:
            return []

        scene_lower = scene_hint.lower()
        selected = []

        # low lighting: 夜间/昏暗场景
        if "low lighting" in available_lighting:
            if any(word in scene_lower for word in
                   ["night", "dark", "dim", "evening", "dusk", "late", "club", "bar"]):
                selected.append("low lighting")

        # overexposed: 强光/户外日光场景（随机添加）
        if "overexposed" in available_lighting:
            if any(word in scene_lower for word in
                   ["sunlight", "bright", "window", "outdoor", "sunny", "daylight"]):
                if random.random() < 0.2:  # 20%概率
                    selected.append("overexposed")

        # underexposed: 阴影/室内场景（随机添加）
        if "underexposed" in available_lighting:
            if any(word in scene_lower for word in
                   ["shadow", "corner", "indoor", "room", "hallway"]):
                if random.random() < 0.2:  # 20%概率
                    selected.append("underexposed")

        return selected

    def _select_contextual_atmosphere(
        self,
        scene_hint: str,
        available_atmosphere: List[str]
    ) -> List[str]:
        """
        根据场景内容智能选择氛围词

        Args:
            scene_hint: 场景描述
            available_atmosphere: 当前级别可用的氛围词

        Returns:
            根据场景选中的氛围词
        """
        if not available_atmosphere:
            return []

        scene_lower = scene_hint.lower()
        selected = []

        # eerie atmosphere: 夜间/诡异/神秘场景（低概率）
        if "eerie atmosphere" in available_atmosphere:
            if any(word in scene_lower for word in
                   ["night", "dark", "abandoned", "empty", "alone", "fog", "shadow", "eerie"]):
                if random.random() < 0.15:  # 15%概率，避免过度使用
                    selected.append("eerie atmosphere")

        return selected

    def _apply_random_variation(self, tokens: List[str]) -> List[str]:
        """
        应用随机变化，增加图片多样性

        策略：70%保留全部，30%随机保留70-90%

        Args:
            tokens: 原始token列表

        Returns:
            应用随机变化后的token列表
        """
        if len(tokens) <= 2:
            return tokens

        # 70%概率保留全部tokens
        if random.random() < 0.7:
            return tokens

        # 否则随机保留70-90%
        keep_ratio = random.uniform(0.7, 0.9)
        keep_count = max(2, int(len(tokens) * keep_ratio))
        return random.sample(tokens, keep_count)

    def _combine_prompt(
        self,
        base: str,
        model_tokens: Dict[str, List[str]],
        realism_tokens: List[str]
    ) -> str:
        """
        组合最终提示词

        格式: [prefix] + base_description + realism_tokens + [suffix]

        Args:
            base: 基础场景描述
            model_tokens: 模型特定tokens {"prefix": [...], "suffix": [...]}
            realism_tokens: 真实感tokens

        Returns:
            组合后的完整提示词
        """
        parts = []

        # 前缀（模型特定）
        if model_tokens.get("prefix"):
            parts.extend(model_tokens["prefix"])

        # 基础描述（来自LLM）
        parts.append(base)

        # 真实感修饰
        if realism_tokens:
            parts.append(", ".join(realism_tokens))

        # 后缀（模型特定）
        if model_tokens.get("suffix"):
            parts.extend(model_tokens["suffix"])

        return ", ".join(parts)

    # ============ 子类需要实现的方法 ============

    def _get_model_specific_tokens(self) -> Dict[str, List[str]]:
        """
        获取模型特定tokens

        Returns:
            {"prefix": [...], "suffix": [...]}
        """
        raise NotImplementedError

    def _get_enhanced_negative(self) -> str:
        """
        获取增强后的负向提示词

        Returns:
            负向提示词字符串
        """
        raise NotImplementedError


class ZImagePromptEnhancer(PromptEnhancer):
    """
    Z-Image模型专用增强器

    优化目标：
    - 真实感、自然感
    - 手机拍摄风格
    - 避免过度完美的AI感
    """

    def _get_model_specific_tokens(self) -> Dict[str, List[str]]:
        """
        Z-Image模型特定tokens

        Z-Image特点：
        - 不需要特殊prefix（直接描述即可）
        - 不需要过多后缀修饰
        - 强调自然、真实
        """
        return {
            "prefix": [],  # Z-Image不需要prefix
            "suffix": []   # 真实感词已经在realism_tokens中
        }

    def _get_enhanced_negative(self) -> str:
        """
        Z-Image专用负向提示词

        重点避免：
        - AI感、过度完美
        - 人工棚拍光效
        - 过度修图
        """
        return (
            "ugly, deformed, noisy, blurry, low quality, "
            "distorted, watermark, text, logo, "
            "artificial lighting, oversaturated, "
            "perfect studio lighting, airbrushed skin, "
            "flawless complexion, professional makeup, "
            "CGI, 3d render, anime"
        )


class SDXLPromptEnhancer(PromptEnhancer):
    """
    SDXL模型专用增强器

    优化目标：
    - 高清晰度、高细节
    - 摄影风格
    - 专业质感（但保留自然感）
    """

    def _load_realism_tokens(self) -> Dict[RealismLevel, Dict[str, List[str]]]:
        """
        SDXL专用真实感词库

        SDXL特点：
        - 更强调摄影质感
        - 支持更复杂的提示词
        - 需要平衡"高质量"和"真实感"
        """
        return {
            RealismLevel.LOW: {
                "quality": ["photography", "natural lighting"],
                "authenticity": ["candid shot"],
                "flaws": [],
                "camera": ["35mm photograph"],
                "lighting": [],
                "atmosphere": []
            },
            RealismLevel.MEDIUM: {
                "quality": [
                    "photography",
                    "natural lighting",
                    "raw photograph"
                ],
                "authenticity": [
                    "candid shot",
                    "authentic moment",
                    "unposed"
                ],
                "flaws": [
                    "environmental background",
                    "natural skin texture",
                    "lens chromatic aberration"
                ],
                "camera": [
                    "shot on iPhone",
                    "amateur photography",
                    "handheld camera"
                ],
                "lighting": ["available light"],  # 现场光
                "atmosphere": []
            },
            RealismLevel.HIGH: {
                "quality": [
                    "photography",
                    "natural lighting",
                    "raw unedited photograph",
                    "no post-processing"
                ],
                "authenticity": [
                    "candid shot",
                    "authentic moment",
                    "unposed",
                    "caught in the moment",
                    "spontaneous",
                    "in motion"  # 运动中
                ],
                "flaws": [
                    "environmental background",
                    "natural skin texture",
                    "visible pores",
                    "lens chromatic aberration",
                    "slight motion blur",
                    "bokeh imperfections",
                    "natural shadows"
                ],
                "camera": [
                    "shot on iPhone",
                    "amateur photography",
                    "handheld camera",
                    "personal photo",
                    "wide angle lens",  # 广角（类似GoPro效果）
                    "phone camera"
                ],
                "lighting": [
                    "available light",
                    "low light",
                    "overexposed highlights",  # 高光过曝
                    "underexposed shadows"     # 阴影欠曝
                ],
                "atmosphere": [
                    "moody atmosphere",    # 情绪化氛围
                    "atmospheric haze"     # 大气朦胧感
                ]
            }
        }

    def _get_model_specific_tokens(self) -> Dict[str, List[str]]:
        """
        SDXL模型特定tokens

        SDXL特点：
        - 需要明确"photograph"前缀
        - 支持技术参数描述
        - 强调细节和质量
        """
        return {
            "prefix": ["photograph of"],  # SDXL需要明确类型
            "suffix": [
                "high detail",
                "8k uhd",
                "dslr"
            ]
        }

    def _get_enhanced_negative(self) -> str:
        """
        SDXL专用负向提示词

        重点避免：
        - 非摄影类型（绘画、3D等）
        - AI感、过度处理
        """
        return (
            "cartoon, anime, 3d render, illustration, painting, drawing, "
            "art, sketch, digital art, cgi, "
            "ugly, deformed, blurry, low quality, "
            "artificial, airbrushed, plastic skin, "
            "perfect flawless, heavy makeup, "
            "studio lighting, professional photoshoot, "
            "watermark, text, signature"
        )


# ============ 工厂函数 ============

def create_prompt_enhancer(
    model_type: str = "z-image",
    realism_level: str = "medium"
) -> PromptEnhancer:
    """
    创建提示词增强器（工厂函数）

    Args:
        model_type: 模型类型
            - "z-image": Z-Image模型（推荐用于快速生成）
            - "sdxl": SDXL模型（推荐用于高质量生成）
        realism_level: 真实感级别
            - "low": 保守，基础真实感
            - "medium": 推荐，平衡真实感和质量
            - "high": 激进，最大化真实感

    Returns:
        对应的PromptEnhancer实例

    Raises:
        ValueError: 不支持的模型类型

    Examples:
        >>> # Z-Image，中等真实感（推荐）
        >>> enhancer = create_prompt_enhancer("z-image", "medium")
        >>> result = enhancer.enhance(scene_hint)

        >>> # SDXL，低真实感（高质量）
        >>> enhancer = create_prompt_enhancer("sdxl", "low")
        >>> result = enhancer.enhance(scene_hint)
    """
    level = RealismLevel(realism_level)

    if model_type == "z-image":
        return ZImagePromptEnhancer(realism_level=level)
    elif model_type == "sdxl":
        return SDXLPromptEnhancer(realism_level=level)
    else:
        raise ValueError(
            f"Unsupported model type: {model_type}. "
            f"Supported: 'z-image', 'sdxl'"
        )


# ============ 便捷函数 ============

def enhance_prompt(
    scene_hint: str,
    model_type: str = "z-image",
    realism_level: str = "medium",
    enable_realism: bool = True,
    enable_variation: bool = True
) -> Dict[str, str]:
    """
    一键增强提示词（便捷函数）

    Args:
        scene_hint: 原始场景描述
        model_type: 模型类型 ("z-image" | "sdxl")
        realism_level: 真实感级别 ("low" | "medium" | "high")
        enable_realism: 是否启用真实感增强
        enable_variation: 是否启用随机变化

    Returns:
        {"positive_prompt": "...", "negative_prompt": "..."}

    Examples:
        >>> result = enhance_prompt(
        ...     "Woman sitting in cafe, wearing casual clothes...",
        ...     model_type="z-image",
        ...     realism_level="medium"
        ... )
        >>> print(result["positive_prompt"])
    """
    enhancer = create_prompt_enhancer(model_type, realism_level)
    return enhancer.enhance(scene_hint, enable_realism, enable_variation)
