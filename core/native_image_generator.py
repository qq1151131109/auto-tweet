"""
Native Image Generator - Z-Image Progressive Generation

Implements ComfyUI workflow's three-stage progressive generation using Z-Image's native API.
Eliminates ComfyUI dependency while preserving generation quality.
"""

import os
from pathlib import Path
from typing import Optional, Union, List
import yaml

import torch
from PIL import Image
from loguru import logger

from core.models.model_loader import ZImageModelLoader
from core.models.lora_manager import LoRAManager
from core.pipelines.zimage_progressive import generate_with_img2img, upscale_latent


class NativeImageGenerator:
    """
    Native Image Generator using Z-Image

    Implements three-stage progressive generation matching ComfyUI workflow:
    - Stage 1: Generate 176×224 latent
    - Stage 2: Upscale to 336×432, refine with img2img (denoise=0.7)
    - Stage 3: Upscale to 672×864, final refine with img2img (denoise=0.6)
    """

    def __init__(
        self,
        config_path: str = "config/native_image_generation.yaml",
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        dtype: Optional[str] = None,
    ):
        """
        Initialize native image generator.

        Args:
            config_path: Path to configuration YAML
            model_path: Override model path from config
            device: Override device from config
            dtype: Override dtype from config
        """
        # Load configuration
        config_file = Path(__file__).parent.parent / config_path
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)

        # Override config if specified
        if model_path:
            self.config['model']['unet_path'] = model_path
        if device:
            self.config['model']['device'] = device
        if dtype:
            self.config['model']['torch_dtype'] = dtype

        # Initialize model loader
        self.model_loader = ZImageModelLoader(
            model_path=self.config['model']['unet_path'],
            device=self.config['model']['device'],
            dtype=self._get_torch_dtype(),
            compile=self.config['performance'].get('compile_unet', False),
        )

        # Load models
        self.components = self.model_loader.load()

        # Initialize LoRA manager
        self.lora_manager = LoRAManager(self.components['transformer'])

        logger.info("NativeImageGenerator initialized successfully")

    def _get_torch_dtype(self):
        """Convert dtype string to torch.dtype."""
        dtype_str = self.config['model']['torch_dtype']
        dtype_map = {
            'bfloat16': torch.bfloat16,
            'float16': torch.float16,
            'float32': torch.float32,
        }
        return dtype_map.get(dtype_str, torch.bfloat16)

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        lora_path: Optional[str] = None,
        lora_strength: float = 0.8,
        trigger_word: str = "",
        seed: Optional[int] = None,
        progressive: Optional[bool] = None,
    ) -> Image.Image:
        """
        Generate image with optional progressive generation.

        Args:
            prompt: Positive prompt
            negative_prompt: Negative prompt
            lora_path: Optional LoRA model path
            lora_strength: LoRA strength (0.0-1.0)
            trigger_word: LoRA trigger word
            seed: Random seed for reproducibility
            progressive: Use progressive generation (default from config)

        Returns:
            PIL Image (672×864)
        """
        # Use config default if not specified
        if progressive is None:
            progressive = self.config['generation']['progressive']

        # Load LoRA if specified
        if lora_path:
            self.lora_manager.load_lora(lora_path, lora_strength)

        # Combine trigger word with prompt
        full_prompt = f"{trigger_word}, {prompt}".strip(", ") if trigger_word else prompt

        # Setup generator
        device = self.config['model']['device']
        generator = torch.Generator(device).manual_seed(seed) if seed is not None else None

        logger.info(
            f"Generating image: prompt_len={len(full_prompt)}, "
            f"progressive={progressive}, seed={seed}"
        )

        try:
            if progressive:
                # Three-stage progressive generation
                image = self._progressive_generate(
                    prompt=full_prompt,
                    negative_prompt=negative_prompt,
                    generator=generator
                )
            else:
                # Single-stage direct generation
                image = self._single_stage_generate(
                    prompt=full_prompt,
                    negative_prompt=negative_prompt,
                    generator=generator
                )

            return image

        finally:
            # Always unload LoRA after generation
            if lora_path and self.config['lora'].get('auto_unload', True):
                self.lora_manager.unload_lora()

    def _single_stage_generate(
        self,
        prompt: str,
        negative_prompt: str,
        generator: Optional[torch.Generator]
    ) -> Image.Image:
        """
        Single-stage direct generation to 672×864.

        Args:
            prompt: Positive prompt
            negative_prompt: Negative prompt
            generator: Random generator

        Returns:
            PIL Image (672×864)
        """
        config = self.config['generation']['single_stage']

        logger.info(
            f"Single-stage generation: {config['width']}×{config['height']}, "
            f"steps={config['num_inference_steps']}, cfg={config['guidance_scale']}"
        )

        images = generate_with_img2img(
            **self.components,
            prompt=prompt,
            negative_prompt=negative_prompt,
            height=config['height'],
            width=config['width'],
            num_inference_steps=config['num_inference_steps'],
            guidance_scale=config['guidance_scale'],
            generator=generator,
            output_type="pil",
        )

        return images[0]

    def _progressive_generate(
        self,
        prompt: str,
        negative_prompt: str,
        generator: Optional[torch.Generator]
    ) -> Image.Image:
        """
        Three-stage progressive generation.

        Replicates ComfyUI workflow:
        - Stage 1: Generate 176×224 → latent
        - Stage 2: Upscale to 336×432, refine (denoise=0.7) → latent
        - Stage 3: Upscale to 672×864, final refine (denoise=0.6) → image

        Args:
            prompt: Positive prompt
            negative_prompt: Negative prompt
            generator: Random generator

        Returns:
            PIL Image (672×864)
        """
        logger.info("Starting three-stage progressive generation")

        # Stage 1: Initial generation 176×224
        latent_1 = self._stage1_generate(prompt, negative_prompt, generator)

        # Stage 2: Upscale to 336×432 and refine
        latent_2 = self._stage2_refine(latent_1, prompt, negative_prompt, generator)

        # Stage 3: Upscale to 672×864 and final refine
        image = self._stage3_refine(latent_2, prompt, negative_prompt, generator)

        logger.info("Progressive generation completed successfully")
        return image

    def _stage1_generate(
        self,
        prompt: str,
        negative_prompt: str,
        generator: Optional[torch.Generator]
    ) -> torch.Tensor:
        """
        Stage 1: Initial generation at 176×224.

        ComfyUI nodes: 317 (EmptyLatent) + 316 (SamplerCustom)
        - Sampler: EulerAncestral
        - Scheduler: FlowMatchEulerDiscreteScheduler
        - Steps: 9
        - CFG: 2.0

        Returns:
            Latent tensor [1, C, H, W]
        """
        config = self.config['generation']['progressive_stages']['stage1']

        logger.info(
            f"Stage 1: Generating {config['width']}×{config['height']}, "
            f"steps={config['num_inference_steps']}, cfg={config['guidance_scale']}"
        )

        latent = generate_with_img2img(
            **self.components,
            prompt=prompt,
            negative_prompt=negative_prompt,
            height=config['height'],
            width=config['width'],
            num_inference_steps=config['num_inference_steps'],
            guidance_scale=config['guidance_scale'],
            generator=generator,
            output_type="latent",  # Return latent for next stage
        )

        logger.info(f"Stage 1 complete: latent shape = {latent.shape}")
        return latent

    def _stage2_refine(
        self,
        latent_1: torch.Tensor,
        prompt: str,
        negative_prompt: str,
        generator: Optional[torch.Generator]
    ) -> torch.Tensor:
        """
        Stage 2: Upscale to 336×432 and refine.

        ComfyUI nodes: 321 (LatentUpscale) + 276 (KSampler)
        - Upscale: nearest-exact, 2x from Stage 1
        - Steps: 16
        - CFG: 1.0
        - Denoise: 0.7

        Args:
            latent_1: Latent from Stage 1

        Returns:
            Refined latent tensor
        """
        config = self.config['generation']['progressive_stages']['stage2']

        # Upscale latent (nearest-exact, 2x)
        latent_upscaled = upscale_latent(
            latent_1,
            scale_factor=2.0,
            mode=config.get('upscale_mode', 'nearest-exact')
        )

        logger.info(
            f"Stage 2: Refining {config['width']}×{config['height']}, "
            f"steps={config['num_inference_steps']}, cfg={config['guidance_scale']}, "
            f"denoise={config['strength']}"
        )

        # Refine with img2img
        latent_2 = generate_with_img2img(
            **self.components,
            prompt=prompt,
            negative_prompt=negative_prompt,
            height=config['height'],
            width=config['width'],
            num_inference_steps=config['num_inference_steps'],
            guidance_scale=config['guidance_scale'],
            initial_latent=latent_upscaled,
            strength=config['strength'],  # denoise strength
            generator=generator,
            output_type="latent",  # Return latent for next stage
        )

        logger.info(f"Stage 2 complete: latent shape = {latent_2.shape}")
        return latent_2

    def _stage3_refine(
        self,
        latent_2: torch.Tensor,
        prompt: str,
        negative_prompt: str,
        generator: Optional[torch.Generator]
    ) -> Image.Image:
        """
        Stage 3: Upscale to 672×864 and final refine.

        ComfyUI nodes: 303 (LatentUpscaleBy) + 325 (SamplerCustom) + 328 (VAEDecode)
        - Upscale: nearest-exact, 2x from Stage 2
        - Steps: 16
        - CFG: 1.0
        - Denoise: 0.6
        - Final VAE decode to PIL Image

        Args:
            latent_2: Latent from Stage 2

        Returns:
            Final PIL Image (672×864)
        """
        config = self.config['generation']['progressive_stages']['stage3']

        # Upscale latent (nearest-exact, 2x)
        latent_upscaled = upscale_latent(
            latent_2,
            scale_factor=2.0,
            mode=config.get('upscale_mode', 'nearest-exact')
        )

        logger.info(
            f"Stage 3: Final refine {config['width']}×{config['height']}, "
            f"steps={config['num_inference_steps']}, cfg={config['guidance_scale']}, "
            f"denoise={config['strength']}"
        )

        # Final refine and decode to image
        images = generate_with_img2img(
            **self.components,
            prompt=prompt,
            negative_prompt=negative_prompt,
            height=config['height'],
            width=config['width'],
            num_inference_steps=config['num_inference_steps'],
            guidance_scale=config['guidance_scale'],
            initial_latent=latent_upscaled,
            strength=config['strength'],  # denoise strength
            generator=generator,
            output_type="pil",  # Final output as PIL Image
        )

        logger.info("Stage 3 complete: image generated")
        return images[0]

    def unload(self):
        """Unload models and free GPU memory."""
        logger.info("Unloading NativeImageGenerator")
        self.lora_manager.unload_lora()
        self.model_loader.unload()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.unload()
