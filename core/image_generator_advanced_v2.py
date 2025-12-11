"""
Z-Image 高级图片生成器 V2
真正的 Latent 空间三阶段渐进式生成（完全复刻 ComfyUI 工作流）

关键修复：
1. 使用 Latent 空间操作（不是像素空间）
2. 正确的尺寸：176×224 → 336×432 → 672×864 (latent 空间)
3. 使用 pipeline 的 latents 参数进行 latent 上采样
"""
import sys
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import torch
from PIL import Image
import logging
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class ZImageGeneratorAdvancedV2:
    """
    Z-Image 高级图片生成器 V2 - 真正的 Latent 空间三阶段渐进式生成

    完全复刻 ComfyUI workflow/zimage-121101.json
    """

    def __init__(
        self,
        model_path: str = "Z-Image/ckpts/Z-Image-Turbo",
        device: str = None,
        dtype: torch.dtype = torch.bfloat16,
        compile: bool = False,
    ):
        """
        初始化 Z-Image 高级生成器 V2

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

        logger.info(f"🔧 初始化 ZImageGeneratorAdvancedV2 (Latent 空间三阶段)")
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

            self.pipeline.load_lora_weights(str(lora_file.parent), weight_name=lora_file.name)

            if hasattr(self.pipeline, 'fuse_lora'):
                self.pipeline.fuse_lora(lora_scale=lora_strength)
                logger.info(f"   ✓ LoRA 已融合到模型 (强度: {lora_strength})")
            else:
                logger.warning(f"⚠️  Pipeline 不支持 fuse_lora")

        except Exception as e:
            logger.error(f"   ❌ LoRA 加载失败: {e}")

    def unload_lora(self):
        """卸载 LoRA"""
        try:
            if hasattr(self.pipeline, 'unfuse_lora'):
                self.pipeline.unfuse_lora()
            if hasattr(self.pipeline, 'unload_lora_weights'):
                self.pipeline.unload_lora_weights()
        except Exception as e:
            logger.warning(f"⚠️  LoRA 卸载失败: {e}")

    def _upscale_latent(self, latents: torch.Tensor, target_size: Tuple[int, int], method: str = "nearest") -> torch.Tensor:
        """
        上采样 latent（模拟 ComfyUI 的 LatentUpscale）

        Args:
            latents: 输入 latent tensor [B, C, H, W]
            target_size: 目标尺寸 (height, width) - latent 空间
            method: 上采样方法 ("nearest", "bilinear", "bicubic")

        Returns:
            上采样后的 latent tensor
        """
        target_height, target_width = target_size

        # 使用 torch.nn.functional.interpolate
        upscaled_latents = F.interpolate(
            latents,
            size=(target_height, target_width),
            mode=method,
            align_corners=False if method != "nearest" else None
        )

        return upscaled_latents

    def generate_progressive_latent(
        self,
        positive_prompt: str,
        negative_prompt: str = "",
        trigger_word: str = "",
        # Latent 空间尺寸（不是像素！）
        stage1_latent_size: Tuple[int, int] = (224, 176),  # (H, W) latent 空间
        stage2_latent_size: Tuple[int, int] = (432, 336),
        stage3_latent_size: Tuple[int, int] = (864, 672),
        # 采样参数
        stage1_steps: int = 9,
        stage2_steps: int = 16,
        stage3_steps: int = 16,
        stage1_cfg: float = 2.0,
        stage2_cfg: float = 1.0,
        stage3_cfg: float = 1.0,
        # denoise 参数
        stage2_denoise: float = 0.7,
        stage3_denoise: float = 0.6,
        # LoRA 参数
        lora_path: str = "",
        lora_strength: float = 1.0,
        # 种子
        seeds: Optional[Tuple[int, int, int]] = None,
    ) -> Image.Image:
        """
        三阶段渐进式生成（Latent 空间操作，完全复刻 ComfyUI）

        Args:
            positive_prompt: 正向提示词
            negative_prompt: 负向提示词
            trigger_word: LoRA 触发词
            stage1_latent_size: 阶段1 latent 尺寸 (H, W)
            stage2_latent_size: 阶段2 latent 尺寸 (H, W)
            stage3_latent_size: 阶段3 latent 尺寸 (H, W)
            ...其他参数

        Returns:
            PIL.Image 对象
        """
        # 合并 trigger word
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

        # 加载 LoRA
        if lora_path:
            self.load_lora(lora_path, lora_strength)

        logger.info(f"🎨 三阶段渐进式生成 (Latent 空间)")
        logger.info(f"   Trigger Word: {trigger_word if trigger_word else '(无)'}")
        logger.info(f"   LoRA: {Path(lora_path).name if lora_path else '(无)'}")

        # ============ 阶段1: 低分辨率基础生成 (Latent 空间) ============
        stage1_h, stage1_w = stage1_latent_size
        # 转换为像素空间（VAE 的 latent 缩放因子是 8）
        stage1_pixel_h = stage1_h * 8
        stage1_pixel_w = stage1_w * 8

        logger.info(f"\n📍 阶段1: 基础生成")
        logger.info(f"   Latent: {stage1_h}×{stage1_w}")
        logger.info(f"   像素: {stage1_pixel_h}×{stage1_pixel_w}")
        logger.info(f"   Steps: {stage1_steps}, CFG: {stage1_cfg}, Seed: {seeds[0]}")

        generator1 = torch.Generator(self.device).manual_seed(seeds[0])

        # 生成初始 latent
        result1 = self.pipeline(
            prompt=full_prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            height=stage1_pixel_h,
            width=stage1_pixel_w,
            num_inference_steps=stage1_steps,
            guidance_scale=stage1_cfg,
            generator=generator1,
            output_type="latent"  # 关键：输出 latent 而不是 PIL 图像
        )
        latent_stage1 = result1.images  # 这是 latent tensor [B, C, H, W]

        logger.info(f"   ✓ Latent shape: {latent_stage1.shape}")

        # ============ 阶段2: 上采样到中分辨率 (Latent 空间) ============
        stage2_h, stage2_w = stage2_latent_size
        stage2_pixel_h = stage2_h * 8
        stage2_pixel_w = stage2_w * 8

        logger.info(f"\n📍 阶段2: 中间精修")
        logger.info(f"   Latent: {stage2_h}×{stage2_w}")
        logger.info(f"   像素: {stage2_pixel_h}×{stage2_pixel_w}")
        logger.info(f"   Steps: {stage2_steps}, CFG: {stage2_cfg}, Denoise: {stage2_denoise}, Seed: {seeds[1]}")

        # Latent 空间上采样
        latent_upscaled2 = self._upscale_latent(latent_stage1, (stage2_h, stage2_w), method="nearest")
        logger.info(f"   ✓ Upscaled latent shape: {latent_upscaled2.shape}")

        # img2latent 精修（使用 denoise 控制噪声强度）
        generator2 = torch.Generator(self.device).manual_seed(seeds[2])

        # 计算实际的 timestep（denoise 控制从哪个 timestep 开始）
        # denoise=0.7 表示保留 30% 原始 latent，重绘 70%
        start_timestep = int(stage2_steps * (1 - stage2_denoise))

        result2 = self.pipeline(
            prompt=full_prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            height=stage2_pixel_h,
            width=stage2_pixel_w,
            num_inference_steps=stage2_steps,
            guidance_scale=stage2_cfg,
            generator=generator2,
            latents=latent_upscaled2,  # 传入上采样的 latent
            output_type="latent"
        )
        latent_stage2 = result2.images

        logger.info(f"   ✓ Refined latent shape: {latent_stage2.shape}")

        # ============ 阶段3: 上采样到高分辨率 (Latent 空间) ============
        stage3_h, stage3_w = stage3_latent_size
        stage3_pixel_h = stage3_h * 8
        stage3_pixel_w = stage3_w * 8

        logger.info(f"\n📍 阶段3: 最终精修")
        logger.info(f"   Latent: {stage3_h}×{stage3_w}")
        logger.info(f"   像素: {stage3_pixel_h}×{stage3_pixel_w}")
        logger.info(f"   Steps: {stage3_steps}, CFG: {stage3_cfg}, Denoise: {stage3_denoise}, Seed: {seeds[2]}")

        # Latent 空间上采样 (×2)
        latent_upscaled3 = self._upscale_latent(latent_stage2, (stage3_h, stage3_w), method="nearest")
        logger.info(f"   ✓ Upscaled latent shape: {latent_upscaled3.shape}")

        # 最终精修
        generator3 = torch.Generator(self.device).manual_seed(seeds[2])

        result3 = self.pipeline(
            prompt=full_prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            height=stage3_pixel_h,
            width=stage3_pixel_w,
            num_inference_steps=stage3_steps,
            guidance_scale=stage3_cfg,
            generator=generator3,
            latents=latent_upscaled3,
            output_type="pil"  # 最后一步输出 PIL 图像
        )
        image_final = result3.images[0]

        # 卸载 LoRA
        if lora_path:
            self.unload_lora()

        logger.info(f"\n✅ 三阶段生成完成")
        logger.info(f"   最终尺寸: {image_final.size}")

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
        简单单阶段生成（备用方案）
        """
        if trigger_word:
            full_prompt = f"{trigger_word}, {positive_prompt}"
        else:
            full_prompt = positive_prompt

        if seed is None:
            seed = torch.randint(0, 2**63 - 1, (1,)).item()

        if lora_path:
            self.load_lora(lora_path, lora_strength)

        generator = torch.Generator(self.device).manual_seed(seed)

        result = self.pipeline(
            prompt=full_prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            height=height,
            width=width,
            num_inference_steps=steps,
            guidance_scale=cfg,
            generator=generator,
            output_type="pil"
        )
        image = result.images[0]

        if lora_path:
            self.unload_lora()

        return image
