"""
Modified Z-Image Pipeline with img2img Support

This module extends Z-Image's native pipeline to support:
1. Initial latent input for img2img generation
2. Denoise strength control
3. Progressive generation (3-stage upscaling)
"""

import sys
import os
from pathlib import Path
from typing import List, Optional, Union

import torch
import torch.nn.functional as F
from PIL import Image
from loguru import logger

# Add Z-Image to sys.path
project_root = Path(__file__).parent.parent.parent
zimage_path = project_root / "Z-Image" / "src"
if str(zimage_path) not in sys.path:
    sys.path.insert(0, str(zimage_path))

from zimage.pipeline import calculate_shift, retrieve_timesteps


@torch.no_grad()
def generate_with_img2img(
    transformer,
    vae,
    text_encoder,
    tokenizer,
    scheduler,
    prompt: Union[str, List[str]],
    height: int,
    width: int,
    num_inference_steps: int = 20,
    guidance_scale: float = 3.5,
    negative_prompt: Optional[Union[str, List[str]]] = None,
    num_images_per_prompt: int = 1,
    generator: Optional[torch.Generator] = None,
    cfg_normalization: bool = False,
    cfg_truncation: float = 1.0,
    max_sequence_length: int = 256,
    output_type: str = "pil",
    initial_latent: Optional[torch.Tensor] = None,
    strength: float = 1.0,
):
    """
    Generate images with optional initial latent (img2img).

    Args:
        transformer: Z-Image transformer model
        vae: VAE model
        text_encoder: Text encoder (Qwen)
        tokenizer: Text tokenizer
        scheduler: Noise scheduler
        prompt: Text prompt(s)
        height: Output height
        width: Output width
        num_inference_steps: Total denoising steps
        guidance_scale: CFG scale
        negative_prompt: Negative prompt(s)
        num_images_per_prompt: Batch size
        generator: Random generator for reproducibility
        cfg_normalization: Whether to normalize CFG
        cfg_truncation: CFG truncation threshold
        max_sequence_length: Max text sequence length
        output_type: "pil", "latent", or "pt" (tensor)
        initial_latent: Optional initial latent for img2img (shape: [B, C, H, W])
        strength: Denoise strength (0.0-1.0). 1.0 = full denoise, 0.5 = half steps

    Returns:
        Generated image(s) or latent(s)
    """
    device = next(transformer.parameters()).device

    # Calculate VAE scale factor
    if hasattr(vae, "config") and hasattr(vae.config, "block_out_channels"):
        vae_scale_factor = 2 ** (len(vae.config.block_out_channels) - 1)
    else:
        vae_scale_factor = 8
    vae_scale = vae_scale_factor * 2

    # Validate dimensions
    if height % vae_scale != 0:
        raise ValueError(f"Height must be divisible by {vae_scale} (got {height}).")
    if width % vae_scale != 0:
        raise ValueError(f"Width must be divisible by {vae_scale} (got {width}).")

    # Handle prompt batching
    if isinstance(prompt, str):
        batch_size = 1
        prompt = [prompt]
    else:
        batch_size = len(prompt)

    do_classifier_free_guidance = guidance_scale > 1.0
    logger.info(
        f"Generating: {height}x{width}, steps={num_inference_steps}, "
        f"cfg={guidance_scale}, strength={strength}, "
        f"img2img={initial_latent is not None}"
    )

    # Encode prompts
    formatted_prompts = []
    for p in prompt:
        messages = [{"role": "user", "content": p}]
        formatted_prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True,
        )
        formatted_prompts.append(formatted_prompt)

    text_inputs = tokenizer(
        formatted_prompts,
        padding="max_length",
        max_length=max_sequence_length,
        truncation=True,
        return_tensors="pt",
    )

    text_input_ids = text_inputs.input_ids.to(device)
    prompt_masks = text_inputs.attention_mask.to(device).bool()

    prompt_embeds = text_encoder(
        input_ids=text_input_ids,
        attention_mask=prompt_masks,
        output_hidden_states=True,
    ).hidden_states[-2]

    prompt_embeds_list = []
    for i in range(len(prompt_embeds)):
        prompt_embeds_list.append(prompt_embeds[i][prompt_masks[i]])

    # Encode negative prompts
    negative_prompt_embeds_list = []
    if do_classifier_free_guidance:
        if negative_prompt is None:
            negative_prompt = ["" for _ in prompt]
        elif isinstance(negative_prompt, str):
            negative_prompt = [negative_prompt]

        neg_formatted = []
        for p in negative_prompt:
            messages = [{"role": "user", "content": p}]
            formatted_prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=True,
            )
            neg_formatted.append(formatted_prompt)

        neg_inputs = tokenizer(
            neg_formatted,
            padding="max_length",
            max_length=max_sequence_length,
            truncation=True,
            return_tensors="pt",
        )

        neg_input_ids = neg_inputs.input_ids.to(device)
        neg_masks = neg_inputs.attention_mask.to(device).bool()

        neg_embeds = text_encoder(
            input_ids=neg_input_ids,
            attention_mask=neg_masks,
            output_hidden_states=True,
        ).hidden_states[-2]

        for i in range(len(neg_embeds)):
            negative_prompt_embeds_list.append(neg_embeds[i][neg_masks[i]])

    if num_images_per_prompt > 1:
        prompt_embeds_list = [pe for pe in prompt_embeds_list for _ in range(num_images_per_prompt)]
        if do_classifier_free_guidance:
            negative_prompt_embeds_list = [
                npe for npe in negative_prompt_embeds_list for _ in range(num_images_per_prompt)
            ]

    # Prepare latents
    height_latent = 2 * (int(height) // vae_scale)
    width_latent = 2 * (int(width) // vae_scale)
    shape = (batch_size * num_images_per_prompt, transformer.in_channels, height_latent, width_latent)

    if initial_latent is not None:
        # img2img mode: use provided latent
        if initial_latent.shape != shape:
            # Resize if needed
            logger.warning(
                f"Resizing initial_latent from {initial_latent.shape} to {shape}"
            )
            initial_latent = F.interpolate(
                initial_latent,
                size=(height_latent, width_latent),
                mode='nearest-exact'
            )
        latents = initial_latent.to(device, dtype=torch.float32)
    else:
        # txt2img mode: create random latent
        latents = torch.randn(shape, generator=generator, device=device, dtype=torch.float32)

    actual_batch_size = batch_size * num_images_per_prompt
    image_seq_len = (latents.shape[2] // 2) * (latents.shape[3] // 2)

    # Configure scheduler
    mu = calculate_shift(
        image_seq_len,
        scheduler.config.get("base_image_seq_len", 256),
        scheduler.config.get("max_image_seq_len", 4096),
        scheduler.config.get("base_shift", 0.5),
        scheduler.config.get("max_shift", 1.15),
    )
    scheduler.sigma_min = 0.0
    scheduler_kwargs = {"mu": mu}
    timesteps, num_inference_steps = retrieve_timesteps(
        scheduler,
        num_inference_steps,
        device,
        sigmas=None,
        **scheduler_kwargs,
    )

    # Apply strength for img2img
    # For Flow Matching img2img:
    # 1. Add noise to initial_latent based on strength
    # 2. Start denoising from that noise level (use fewer timesteps)
    if initial_latent is not None and strength < 1.0:
        # Calculate how many steps to skip
        # strength=0.7 means start from 30% into the process (skip first 30% steps)
        init_timestep = int(num_inference_steps * (1 - strength))
        init_timestep = min(init_timestep, num_inference_steps - 1)

        # Get the timestep at which to start
        t_start = timesteps[init_timestep]

        # Add noise to latent based on this timestep
        # For Flow Matching: noise_level = t / 1000
        noise = torch.randn(latents.shape, device=device, generator=generator, dtype=latents.dtype)
        noise_level = t_start.float() / 1000.0

        # Blend initial latent with noise: latent_noisy = (1-t) * latent + t * noise
        latents = (1.0 - noise_level) * latents + noise_level * noise

        # Use only the remaining timesteps
        timesteps = timesteps[init_timestep:]
        actual_steps = len(timesteps)

        logger.info(
            f"img2img: Added noise at level {noise_level:.3f}, "
            f"using {actual_steps}/{num_inference_steps} steps (strength={strength:.2f})"
        )

    # Denoising loop
    from tqdm import tqdm

    for i, t in enumerate(tqdm(timesteps, desc="Denoising", total=len(timesteps))):
        # Skip last step if t=0
        if t == 0 and i == len(timesteps) - 1:
            logger.debug(f"Step {i+1}/{len(timesteps)} | t: {t.item():.2f} | Skipping last step")
            continue

        timestep = t.expand(latents.shape[0])
        timestep = (1000 - timestep) / 1000
        t_norm = timestep[0].item()

        current_guidance_scale = guidance_scale
        if do_classifier_free_guidance and cfg_truncation is not None and float(cfg_truncation) <= 1:
            if t_norm > cfg_truncation:
                current_guidance_scale = 0.0

        apply_cfg = do_classifier_free_guidance and current_guidance_scale > 0

        if apply_cfg:
            latents_typed = latents.to(
                transformer.dtype if hasattr(transformer, "dtype") else next(transformer.parameters()).dtype
            )
            latent_model_input = latents_typed.repeat(2, 1, 1, 1)
            prompt_embeds_model_input = prompt_embeds_list + negative_prompt_embeds_list
            timestep_model_input = timestep.repeat(2)
        else:
            latent_model_input = latents.to(next(transformer.parameters()).dtype)
            prompt_embeds_model_input = prompt_embeds_list
            timestep_model_input = timestep

        latent_model_input = latent_model_input.unsqueeze(2)
        latent_model_input_list = list(latent_model_input.unbind(dim=0))

        model_out_list = transformer(
            latent_model_input_list,
            timestep_model_input,
            prompt_embeds_model_input,
        )[0]

        if apply_cfg:
            pos_out = model_out_list[:actual_batch_size]
            neg_out = model_out_list[actual_batch_size:]
            noise_pred = []
            for j in range(actual_batch_size):
                pos = pos_out[j].float()
                neg = neg_out[j].float()
                pred = pos + current_guidance_scale * (pos - neg)

                if cfg_normalization and float(cfg_normalization) > 0.0:
                    ori_pos_norm = torch.linalg.vector_norm(pos)
                    new_pos_norm = torch.linalg.vector_norm(pred)
                    max_new_norm = ori_pos_norm * float(cfg_normalization)
                    if new_pos_norm > max_new_norm:
                        pred = pred * (max_new_norm / new_pos_norm)
                noise_pred.append(pred)
            noise_pred = torch.stack(noise_pred, dim=0)
        else:
            noise_pred = torch.stack([t.float() for t in model_out_list], dim=0)

        noise_pred = -noise_pred.squeeze(2)
        latents = scheduler.step(noise_pred.to(torch.float32), t, latents, return_dict=False)[0]
        assert latents.dtype == torch.float32

    # Return latent or decode to image
    if output_type == "latent":
        return latents

    # Decode latents to images
    shift_factor = getattr(vae.config, "shift_factor", 0.0) or 0.0
    latents = (latents.to(vae.dtype) / vae.config.scaling_factor) + shift_factor
    image = vae.decode(latents, return_dict=False)[0]

    if output_type == "pil":
        image = (image / 2 + 0.5).clamp(0, 1)
        image = image.cpu().permute(0, 2, 3, 1).float().numpy()
        image = (image * 255).round().astype("uint8")
        image = [Image.fromarray(img) for img in image]

    return image


def upscale_latent(latent: torch.Tensor, scale_factor: float = 2.0, mode: str = 'nearest-exact') -> torch.Tensor:
    """
    Upscale latent tensor using interpolation.

    Args:
        latent: Input latent tensor [B, C, H, W]
        scale_factor: Upscale factor (e.g., 2.0 for 2x)
        mode: Interpolation mode ('nearest-exact', 'bilinear', etc.)

    Returns:
        Upscaled latent tensor
    """
    return F.interpolate(
        latent,
        scale_factor=scale_factor,
        mode=mode,
    )
