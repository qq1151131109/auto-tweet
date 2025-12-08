"""
LoRA支持模块
支持两种模式：
1. Diffusers模式（推荐）：使用diffusers.ZImagePipeline，原生支持LoRA
2. 手动merge模式：加载LoRA权重手动merge到transformer
"""
from pathlib import Path
from typing import Optional, Dict
import torch
from safetensors.torch import load_file
import logging

logger = logging.getLogger(__name__)


def load_lora_diffusers(pipeline, lora_path: str, lora_strength: float = 1.0):
    """
    使用diffusers加载LoRA（推荐方案）

    Args:
        pipeline: ZImagePipeline实例
        lora_path: LoRA文件路径
        lora_strength: LoRA强度
    """
    try:
        # Diffusers支持直接加载LoRA
        pipeline.load_lora_weights(lora_path)

        # 设置LoRA强度（如果支持）
        if hasattr(pipeline, 'set_adapters'):
            pipeline.set_adapters(["default"], adapter_weights=[lora_strength])

        logger.info(f"✓ LoRA加载成功（diffusers）: {lora_path}")
        return True

    except Exception as e:
        logger.error(f"❌ LoRA加载失败: {e}")
        return False


def merge_lora_to_transformer(
    transformer,
    lora_path: str,
    lora_strength: float = 1.0,
    device: str = "cuda"
) -> torch.nn.Module:
    """
    手动merge LoRA权重到transformer（备选方案）

    Args:
        transformer: Transformer模型
        lora_path: LoRA safetensors文件路径
        lora_strength: LoRA强度（alpha值）
        device: 设备

    Returns:
        合并后的transformer
    """
    lora_path = Path(lora_path)

    if not lora_path.exists():
        logger.warning(f"⚠️  LoRA文件不存在: {lora_path}")
        return transformer

    try:
        logger.info(f"🔧 手动merge LoRA: {lora_path.name}")
        logger.info(f"   强度: {lora_strength}")

        # 加载LoRA权重
        lora_state_dict = load_file(str(lora_path), device=str(device))

        # LoRA格式通常是: {layer_name}.lora_A.weight, {layer_name}.lora_B.weight
        # 需要找到对应的transformer层并merge

        transformer_state = transformer.state_dict()
        merged_count = 0

        # 提取LoRA层对
        lora_pairs = {}
        for key in lora_state_dict.keys():
            if '.lora_A.' in key:
                base_name = key.replace('.lora_A.weight', '')
                if base_name not in lora_pairs:
                    lora_pairs[base_name] = {}
                lora_pairs[base_name]['A'] = lora_state_dict[key]
            elif '.lora_B.' in key:
                base_name = key.replace('.lora_B.weight', '')
                if base_name not in lora_pairs:
                    lora_pairs[base_name] = {}
                lora_pairs[base_name]['B'] = lora_state_dict[key]

        # Merge LoRA到原始权重
        for base_name, lora_weights in lora_pairs.items():
            if 'A' not in lora_weights or 'B' not in lora_weights:
                continue

            # 找到对应的transformer层
            target_key = base_name + '.weight'
            if target_key in transformer_state:
                # LoRA公式: W' = W + alpha * (B @ A)
                lora_A = lora_weights['A'].to(device)
                lora_B = lora_weights['B'].to(device)

                delta_weight = lora_strength * (lora_B @ lora_A)
                transformer_state[target_key] += delta_weight

                merged_count += 1

        # 加载合并后的权重
        transformer.load_state_dict(transformer_state)

        logger.info(f"   ✓ 成功merge {merged_count} 个LoRA层")
        return transformer

    except Exception as e:
        logger.error(f"   ❌ LoRA merge失败: {e}")
        return transformer


def get_lora_metadata(lora_path: str) -> Dict:
    """
    读取LoRA元数据

    Args:
        lora_path: LoRA文件路径

    Returns:
        元数据字典
    """
    try:
        from safetensors import safe_open

        metadata = {}
        with safe_open(lora_path, framework="pt") as f:
            metadata = f.metadata() if hasattr(f, 'metadata') else {}

        return metadata

    except Exception as e:
        logger.warning(f"⚠️  无法读取LoRA元数据: {e}")
        return {}


class LoRAManager:
    """LoRA管理器 - 统一管理LoRA加载和卸载"""

    def __init__(self, use_diffusers: bool = True):
        """
        Args:
            use_diffusers: 是否使用diffusers模式（推荐True）
        """
        self.use_diffusers = use_diffusers
        self.loaded_loras = {}

    def load(
        self,
        model_or_pipeline,
        lora_path: str,
        lora_strength: float = 1.0,
        device: str = "cuda"
    ):
        """
        加载LoRA

        Args:
            model_or_pipeline: Transformer或Pipeline
            lora_path: LoRA路径
            lora_strength: 强度
            device: 设备
        """
        if not lora_path or not Path(lora_path).exists():
            logger.warning(f"⚠️  跳过LoRA加载: {lora_path}")
            return model_or_pipeline

        lora_key = str(lora_path)

        # 检查是否已加载
        if lora_key in self.loaded_loras:
            logger.info(f"✓ LoRA已加载（缓存）: {Path(lora_path).name}")
            return model_or_pipeline

        # 选择加载方式
        if self.use_diffusers and hasattr(model_or_pipeline, 'load_lora_weights'):
            # Diffusers模式
            success = load_lora_diffusers(model_or_pipeline, lora_path, lora_strength)
            if success:
                self.loaded_loras[lora_key] = {
                    "strength": lora_strength,
                    "mode": "diffusers"
                }
        else:
            # 手动merge模式
            model_or_pipeline = merge_lora_to_transformer(
                model_or_pipeline, lora_path, lora_strength, device
            )
            self.loaded_loras[lora_key] = {
                "strength": lora_strength,
                "mode": "manual"
            }

        return model_or_pipeline

    def unload_all(self, pipeline_or_model):
        """卸载所有LoRA"""
        if hasattr(pipeline_or_model, 'unload_lora_weights'):
            pipeline_or_model.unload_lora_weights()
            logger.info("✓ 卸载所有LoRA（diffusers）")

        self.loaded_loras.clear()
