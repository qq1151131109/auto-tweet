"""
Z-Image 高级图片生成器
基于 ComfyUI workflow/zimage-121101.json 的优化方案

核心特性：
1. 三阶段渐进式生成（低分辨率 → 中分辨率 → 高分辨率）
2. Trigger Word 支持（LoRA 专属触发词）
3. 中文 Negative Prompt 支持
4. 多种 Sampler 和 Scheduler 策略
"""
import sys
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import torch
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ZImageGeneratorAdvanced:
    """
    Z-Image 高级图片生成器 - 三阶段渐进式生成

    基于 ComfyUI 工作流的优化方案，使用 img2img 模拟 latent upscale
    """

    def __init__(
        self,
        model_path: str = "Z-Image/ckpts/Z-Image-Turbo",
        device: str = None,
        dtype: torch.dtype = torch.bfloat16,
        compile: bool = False,
    ):
        """
        初始化 Z-Image 高级生成器

        Args:
            model_path: Z-Image 模型路径
            device: 设备（cuda/cpu/mps/None=自动）
            dtype: 数据类型（默认bfloat16）
            compile: 是否编译模型（默认False）
        """
        # 自动选择设备
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self.device = device
        self.dtype = dtype

        logger.info(f"🔧 初始化 ZImageGeneratorAdvanced (三阶段渐进式生成)")
        logger.info(f"   模型: {model_path}")
        logger.info(f"   设备: {device}")
        logger.info(f"   类型: {dtype}")

        self._init_pipeline(model_path, device, dtype, compile)

        logger.info(f"   ✓ 模型加载完成\n")

    def _init_pipeline(self, model_path: str, device: str, dtype: torch.dtype, compile: bool):
        """初始化 Diffusers pipeline"""
        try:
            from diffusers import ZImagePipeline

            logger.info("   加载 ZImagePipeline...")
            self.pipeline = ZImagePipeline.from_pretrained(
                model_path,
                torch_dtype=dtype,
                low_cpu_mem_usage=False
            )
            self.pipeline.to(device)

            # 可选：设置 attention backend
            if hasattr(self.pipeline.transformer, 'set_attention_backend'):
                try:
                    self.pipeline.transformer.set_attention_backend("flash")
                    logger.info("   ✓ 使用 Flash Attention")
                except:
                    pass

            # 可选：编译模型
            if compile:
                logger.info("   编译模型...")
                self.pipeline.transformer.compile()

            self.pipeline.set_progress_bar_config(disable=True)

        except ImportError:
            logger.error("❌ diffusers 未安装，请运行: pip install diffusers")
            raise

    def load_lora(self, lora_path: str, lora_strength: float = 1.0):
        """
        加载 LoRA
        使用 fuse_lora 方案，简单可靠，避免 adapter 命名冲突

        Args:
            lora_path: LoRA 文件路径
            lora_strength: LoRA 强度
        """
        if not lora_path or not lora_path.strip():
            return

        lora_path = lora_path.strip()
        lora_file = Path(lora_path)

        if not lora_file.exists():
            logger.warning(f"⚠️  LoRA 文件不存在: {lora_path}")
            return

        try:
            logger.info(f"🔧 加载 LoRA: {lora_file.name}")
            logger.info(f"   强度: {lora_strength}")

            # 加载 LoRA 权重
            self.pipeline.load_lora_weights(str(lora_file.parent), weight_name=lora_file.name)

            # 使用 fuse_lora 直接融合到模型权重中
            if hasattr(self.pipeline, 'fuse_lora'):
                self.pipeline.fuse_lora(lora_scale=lora_strength)
                logger.info(f"   ✓ LoRA 已融合到模型 (强度: {lora_strength})")
            else:
                logger.warning(f"⚠️  Pipeline 不支持 fuse_lora，LoRA 可能无法正常工作")

        except Exception as e:
            logger.error(f"   ❌ LoRA 加载失败: {e}")

    def unload_lora(self):
        """
        卸载 LoRA
        先 unfuse 恢复原始权重，再 unload 释放 LoRA 权重
        """
        try:
            # 先 unfuse 恢复原始模型权重
            if hasattr(self.pipeline, 'unfuse_lora'):
                self.pipeline.unfuse_lora()
                logger.info("✓ LoRA 已从模型中解除融合")

            # 再 unload 释放 LoRA 权重
            if hasattr(self.pipeline, 'unload_lora_weights'):
                self.pipeline.unload_lora_weights()
                logger.info("✓ LoRA 权重已卸载")

        except Exception as e:
            logger.warning(f"⚠️  LoRA 卸载失败: {e}")

    def generate_progressive(
        self,
        positive_prompt: str,
        negative_prompt: str = "",
        trigger_word: str = "",
        # 阶段配置
        stage1_size: Tuple[int, int] = (512, 672),  # 基础生成尺寸
        stage2_size: Tuple[int, int] = (640, 832),  # 中间精修尺寸
        stage3_size: Tuple[int, int] = (768, 1024), # 最终输出尺寸
        # 采样参数
        stage1_steps: int = 9,
        stage2_steps: int = 16,
        stage3_steps: int = 16,
        stage1_cfg: float = 2.0,
        stage2_cfg: float = 1.0,
        stage3_cfg: float = 1.0,
        # denoise 参数（用于 img2img）
        stage2_denoise: float = 0.7,
        stage3_denoise: float = 0.6,
        # LoRA 参数
        lora_path: str = "",
        lora_strength: float = 1.0,
        # 种子
        seeds: Optional[Tuple[int, int, int]] = None,
    ) -> Image.Image:
        """
        三阶段渐进式生成（模拟 ComfyUI workflow）

        Args:
            positive_prompt: 正向提示词
            negative_prompt: 负向提示词（支持中文）
            trigger_word: LoRA 触发词（如 "Deedeemegadoodo photo"）
            stage1_size: 阶段1尺寸（基础生成）
            stage2_size: 阶段2尺寸（中间精修）
            stage3_size: 阶段3尺寸（最终输出）
            stage1_steps: 阶段1步数
            stage2_steps: 阶段2步数
            stage3_steps: 阶段3步数
            stage1_cfg: 阶段1 CFG
            stage2_cfg: 阶段2 CFG
            stage3_cfg: 阶段3 CFG
            stage2_denoise: 阶段2重绘强度
            stage3_denoise: 阶段3重绘强度
            lora_path: LoRA 路径
            lora_strength: LoRA 强度
            seeds: 三个阶段的随机种子（None=自动生成）

        Returns:
            PIL.Image 对象
        """
        # 合并 trigger word 到 prompt
        if trigger_word:
            full_prompt = f"{trigger_word}, {positive_prompt}"
        else:
            full_prompt = positive_prompt

        # 生成种子
        if seeds is None:
            seeds = (
                torch.randint(0, 2**63 - 1, (1,)).item(),
                torch.randint(0, 2**63 - 1, (1,)).item(),
                torch.randint(0, 2**63 - 1, (1,)).item(),
            )

        # 加载 LoRA（如果指定）
        if lora_path:
            self.load_lora(lora_path, lora_strength)

        logger.info(f"🎨 三阶段渐进式生成")
        logger.info(f"   Trigger Word: {trigger_word if trigger_word else '(无)'}")
        logger.info(f"   LoRA: {Path(lora_path).name if lora_path else '(无)'}")

        # ============ 阶段1：低分辨率基础生成 ============
        logger.info(f"\n📍 阶段1: 基础生成 {stage1_size[0]}×{stage1_size[1]}")
        logger.info(f"   Steps: {stage1_steps}, CFG: {stage1_cfg}, Seed: {seeds[0]}")

        generator1 = torch.Generator(self.device).manual_seed(seeds[0])
        image_stage1 = self.pipeline(
            prompt=full_prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            height=stage1_size[1],
            width=stage1_size[0],
            num_inference_steps=stage1_steps,
            guidance_scale=stage1_cfg,
            generator=generator1
        ).images[0]

        # ============ 阶段2：上采样到中分辨率 ============
        logger.info(f"\n📍 阶段2: 中间精修 {stage2_size[0]}×{stage2_size[1]}")
        logger.info(f"   Steps: {stage2_steps}, CFG: {stage2_cfg}, Denoise: {stage2_denoise}, Seed: {seeds[1]}")

        # 上采样
        image_upscaled2 = image_stage1.resize(stage2_size, Image.LANCZOS)

        # img2img 精修
        generator2 = torch.Generator(self.device).manual_seed(seeds[1])
        image_stage2 = self.pipeline(
            prompt=full_prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            image=image_upscaled2,
            strength=stage2_denoise,  # denoise 强度
            num_inference_steps=stage2_steps,
            guidance_scale=stage2_cfg,
            generator=generator2
        ).images[0]

        # ============ 阶段3：上采样到高分辨率 ============
        logger.info(f"\n📍 阶段3: 最终精修 {stage3_size[0]}×{stage3_size[1]}")
        logger.info(f"   Steps: {stage3_steps}, CFG: {stage3_cfg}, Denoise: {stage3_denoise}, Seed: {seeds[2]}")

        # 上采样
        image_upscaled3 = image_stage2.resize(stage3_size, Image.LANCZOS)

        # img2img 精修
        generator3 = torch.Generator(self.device).manual_seed(seeds[2])
        image_final = self.pipeline(
            prompt=full_prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            image=image_upscaled3,
            strength=stage3_denoise,  # denoise 强度
            num_inference_steps=stage3_steps,
            guidance_scale=stage3_cfg,
            generator=generator3
        ).images[0]

        # 卸载 LoRA（避免影响下一次生成）
        if lora_path:
            self.unload_lora()

        logger.info(f"\n✅ 三阶段生成完成")

        return image_final

    def generate_simple(
        self,
        positive_prompt: str,
        negative_prompt: str = "",
        trigger_word: str = "",
        width: int = 768,
        height: int = 1024,
        steps: int = 9,
        cfg: float = 1.0,
        seed: int = None,
        lora_path: str = "",
        lora_strength: float = 1.0
    ) -> Image.Image:
        """
        简单单阶段生成（备用方案，兼容原有接口）

        Args:
            positive_prompt: 正向提示词
            negative_prompt: 负向提示词
            trigger_word: LoRA 触发词
            width: 宽度
            height: 高度
            steps: 推理步数
            cfg: CFG scale
            seed: 随机种子
            lora_path: LoRA 路径
            lora_strength: LoRA 强度

        Returns:
            PIL.Image 对象
        """
        # 合并 trigger word 到 prompt
        if trigger_word:
            full_prompt = f"{trigger_word}, {positive_prompt}"
        else:
            full_prompt = positive_prompt

        # 生成种子
        if seed is None:
            seed = torch.randint(0, 2**63 - 1, (1,)).item()

        # 加载 LoRA（如果指定）
        if lora_path:
            self.load_lora(lora_path, lora_strength)

        # 创建 generator
        generator = torch.Generator(self.device).manual_seed(seed)

        # 单阶段生成
        result = self.pipeline(
            prompt=full_prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            height=height,
            width=width,
            num_inference_steps=steps,
            guidance_scale=cfg,
            generator=generator
        )
        image = result.images[0]

        # 卸载 LoRA（避免影响下一次生成）
        if lora_path:
            self.unload_lora()

        return image


# ============ 批量生成函数 ============

async def generate_batch_images_advanced(
    tweets_batch: Dict,
    output_dir: str,
    model_path: str,
    device: str = "cuda",
    use_progressive: bool = True,
    negative_prompt_template: str = "",
    start_slot: int = 0,
    max_images: Optional[int] = None,
) -> List[Dict]:
    """
    使用高级生成器批量生成图片

    Args:
        tweets_batch: 推文批次 JSON
        output_dir: 输出目录
        model_path: Z-Image 模型路径
        device: 设备
        use_progressive: 是否使用渐进式生成（True=新方案，False=备用方案）
        negative_prompt_template: 负向提示词模板（可选，支持中文）
        start_slot: 起始 slot
        max_images: 最大生成数量

    Returns:
        生成结果列表
    """
    generator = ZImageGeneratorAdvanced(model_path=model_path, device=device)

    tweets = tweets_batch["tweets"]
    persona_name = tweets_batch["persona"]["name"]
    day_offset = tweets_batch.get("daily_plan", {}).get("day_offset", None)
    total = len(tweets)
    end_slot = min(total, start_slot + max_images) if max_images else total

    logger.info(f"📊 高级批量生成")
    logger.info(f"   人设: {persona_name}")
    logger.info(f"   范围: slot {start_slot} ~ {end_slot-1}")
    logger.info(f"   模式: {'渐进式生成 (优化)' if use_progressive else '单阶段生成 (备用)'}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for i in range(start_slot, end_slot):
        tweet = tweets[i]
        img_gen = tweet["image_generation"]

        # 提取参数
        positive_prompt = img_gen.get("positive_prompt", "")
        negative_prompt = img_gen.get("negative_prompt", negative_prompt_template)

        # Trigger Word（从 persona 或 img_gen 中获取）
        trigger_word = img_gen.get("trigger_word", "")
        if not trigger_word and "extensions" in tweets_batch.get("persona", {}):
            trigger_word = tweets_batch["persona"]["extensions"].get("trigger_word", "")

        # LoRA 参数
        lora_params = img_gen.get("lora_params", {})
        lora_path = lora_params.get("model_path", "")
        lora_strength = lora_params.get("strength", 1.0)

        # 生成参数
        gen_params = img_gen.get("generation_params", {})
        width = gen_params.get("width", 768)
        height = gen_params.get("height", 1024)
        steps = gen_params.get("steps", 9)
        cfg = gen_params.get("cfg", 1.0)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if day_offset is not None:
            filename = f"{persona_name}_day{day_offset}_slot{i}_{timestamp}.png"
        else:
            filename = f"{persona_name}_slot{i}_{timestamp}.png"
        output_path = output_dir / filename

        logger.info(f"\n🎨 生成 slot {i+1}/{total}: {tweet['topic_type']}")

        try:
            if use_progressive:
                # 渐进式生成（新方案）
                image = generator.generate_progressive(
                    positive_prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                    trigger_word=trigger_word,
                    stage3_size=(width, height),  # 最终尺寸
                    lora_path=lora_path,
                    lora_strength=lora_strength
                )
            else:
                # 单阶段生成（备用方案）
                image = generator.generate_simple(
                    positive_prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                    trigger_word=trigger_word,
                    width=width,
                    height=height,
                    steps=steps,
                    cfg=cfg,
                    lora_path=lora_path,
                    lora_strength=lora_strength
                )

            # 保存
            image.save(output_path)

            results.append({
                "slot": i,
                "status": "success",
                "output_path": str(output_path),
                "tweet_text": tweet["tweet_text"],
                "generation_mode": "progressive" if use_progressive else "simple"
            })

            logger.info(f"   ✓ 保存至: {output_path}")

        except Exception as e:
            logger.error(f"   ❌ 失败: {e}")
            results.append({
                "slot": i,
                "status": "failed",
                "error": str(e)
            })

    return results
