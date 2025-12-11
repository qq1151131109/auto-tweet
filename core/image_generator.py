"""
Z-Image图片生成器
简化版本：直接接收参数生成图片，支持批量生成
支持两种模式：
1. Diffusers模式（推荐）：使用diffusers.ZImagePipeline，原生支持LoRA
2. 原生PyTorch模式：使用Z-Image原生实现（不支持LoRA）
"""
import sys
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import torch
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ZImageGenerator:
    """
    Z-Image图片生成器 - 支持Diffusers和原生PyTorch两种模式
    """

    def __init__(
        self,
        model_path: str = "Z-Image/ckpts/Z-Image-Turbo",
        device: str = None,
        dtype: torch.dtype = torch.bfloat16,
        compile: bool = False,
        use_diffusers: bool = True  # 默认使用diffusers（支持LoRA）
    ):
        """
        初始化Z-Image生成器

        Args:
            model_path: Z-Image模型路径
            device: 设备（cuda/cpu/mps/None=自动）
            dtype: 数据类型（默认bfloat16）
            compile: 是否编译模型（默认False）
            use_diffusers: 是否使用diffusers模式（推荐True，支持LoRA）
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
        self.use_diffusers = use_diffusers

        logger.info(f"🔧 初始化ZImageGenerator")
        logger.info(f"   模式: {'Diffusers (支持LoRA)' if use_diffusers else 'PyTorch原生'}")
        logger.info(f"   模型: {model_path}")
        logger.info(f"   设备: {device}")
        logger.info(f"   类型: {dtype}")

        if use_diffusers:
            # Diffusers模式
            self._init_diffusers(model_path, device, dtype, compile)
        else:
            # 原生PyTorch模式
            self._init_native(model_path, device, dtype, compile)

        logger.info(f"   ✓ 模型加载完成\n")

    def _init_diffusers(self, model_path: str, device: str, dtype: torch.dtype, compile: bool):
        """初始化diffusers模式"""
        try:
            from diffusers import ZImagePipeline

            logger.info("   加载ZImagePipeline...")
            self.pipeline = ZImagePipeline.from_pretrained(
                model_path,
                torch_dtype=dtype,
                low_cpu_mem_usage=False
            )
            self.pipeline.to(device)

            # 可选：设置attention backend
            if hasattr(self.pipeline.transformer, 'set_attention_backend'):
                try:
                    self.pipeline.transformer.set_attention_backend("flash")
                    logger.info("   ✓ 使用Flash Attention")
                except:
                    pass

            # 可选：编译模型
            if compile:
                logger.info("   编译模型...")
                self.pipeline.transformer.compile()

            self.pipeline.set_progress_bar_config(disable=True)

        except ImportError:
            logger.error("❌ diffusers未安装，请运行: pip install diffusers")
            logger.info("   回退到原生PyTorch模式（不支持LoRA）")
            self.use_diffusers = False
            self._init_native(model_path, device, dtype, compile)

    def _init_native(self, model_path: str, device: str, dtype: torch.dtype, compile: bool):
        """初始化原生PyTorch模式"""
        # 添加Z-Image路径
        sys.path.insert(0, str(Path(__file__).parent.parent / "Z-Image" / "src"))

        from utils.loader import load_from_local_dir
        from utils.helpers import set_attention_backend

        logger.info("   加载原生PyTorch组件...")
        self.components = load_from_local_dir(
            model_path,
            device=device,
            dtype=dtype,
            compile=compile,
            verbose=False
        )

        # 设置attention backend
        set_attention_backend("_native_flash")

    def load_lora(self, lora_path: str, lora_strength: float = 1.0):
        """
        加载LoRA（仅diffusers模式支持）
        使用fuse_lora方案，简单可靠，避免adapter命名冲突

        Args:
            lora_path: LoRA文件路径
            lora_strength: LoRA强度
        """
        if not lora_path or not lora_path.strip():
            return

        lora_path = lora_path.strip()

        if not self.use_diffusers:
            logger.warning(f"⚠️  原生PyTorch模式不支持LoRA: {lora_path}")
            return

        lora_file = Path(lora_path)
        if not lora_file.exists():
            logger.warning(f"⚠️  LoRA文件不存在: {lora_path}")
            return

        try:
            logger.info(f"🔧 加载LoRA: {lora_file.name}")
            logger.info(f"   强度: {lora_strength}")

            # 加载LoRA权重
            self.pipeline.load_lora_weights(str(lora_file.parent), weight_name=lora_file.name)

            # 使用fuse_lora直接融合到模型权重中
            # 这种方式比adapter方式更简单可靠，避免adapter命名冲突
            if hasattr(self.pipeline, 'fuse_lora'):
                self.pipeline.fuse_lora(lora_scale=lora_strength)
                logger.info(f"   ✓ LoRA已融合到模型 (强度: {lora_strength})")
            else:
                logger.warning(f"⚠️  Pipeline不支持fuse_lora，LoRA可能无法正常工作")

        except Exception as e:
            logger.error(f"   ❌ LoRA加载失败: {e}")

    def unload_lora(self):
        """
        卸载LoRA
        先unfuse恢复原始权重，再unload释放LoRA权重
        """
        if not self.use_diffusers:
            return

        try:
            # 先unfuse恢复原始模型权重
            if hasattr(self.pipeline, 'unfuse_lora'):
                self.pipeline.unfuse_lora()
                logger.info("✓ LoRA已从模型中解除融合")

            # 再unload释放LoRA权重
            if hasattr(self.pipeline, 'unload_lora_weights'):
                self.pipeline.unload_lora_weights()
                logger.info("✓ LoRA权重已卸载")

        except Exception as e:
            logger.warning(f"⚠️  LoRA卸载失败: {e}")
    def generate_image(
        self,
        positive_prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 9,
        cfg: float = 0.0,
        seed: int = None,
        lora_path: str = "",
        lora_strength: float = 1.0
    ) -> Image.Image:
        """
        生成单张图片

        Args:
            positive_prompt: 正向提示词
            negative_prompt: 负向提示词
            width: 宽度
            height: 高度
            steps: 推理步数（Z-Image-Turbo推荐8-9）
            cfg: CFG scale（Z-Image-Turbo推荐0.0）
            seed: 随机种子（None=随机）
            lora_path: LoRA路径（仅diffusers模式支持）
            lora_strength: LoRA强度

        Returns:
            PIL.Image对象
        """
        # 生成种子
        if seed is None:
            seed = torch.randint(0, 2**63 - 1, (1,)).item()

        # 加载LoRA（如果指定）
        if lora_path:
            self.load_lora(lora_path, lora_strength)

        # 创建generator
        generator = torch.Generator(self.device).manual_seed(seed)

        if self.use_diffusers:
            # Diffusers模式
            result = self.pipeline(
                prompt=positive_prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                height=height,
                width=width,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator
            )
            image = result.images[0]

            # 卸载LoRA（避免影响下一次生成）
            if lora_path:
                self.unload_lora()

        else:
            # 原生PyTorch模式
            from zimage.pipeline import generate

            images = generate(
                prompt=positive_prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                height=height,
                width=width,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
                **self.components
            )
            image = images[0]

        return image


async def generate_batch_images_single_gpu(
    tweets_batch: Dict,
    output_dir: str,
    model_path: str,
    device: str = "cuda",
    start_slot: int = 0,
    max_images: Optional[int] = None,
    use_diffusers: bool = True,
    use_advanced: bool = False  # 是否使用高级生成器
) -> List[Dict]:
    """
    单GPU批量生成图片

    Args:
        tweets_batch: 推文批次JSON
        output_dir: 输出目录
        model_path: Z-Image模型路径
        device: 设备
        start_slot: 起始slot
        max_images: 最大生成数量
        use_diffusers: 是否使用diffusers模式（支持LoRA）
        use_advanced: 是否使用高级生成器（三阶段渐进式）

    Returns:
        生成结果列表
    """
    # 根据配置选择生成器
    if use_advanced:
        from core.image_generator_advanced import generate_batch_images_advanced
        from config.image_config import load_image_config, get_generation_mode, load_negative_prompt_template

        # 加载配置
        config = load_image_config()
        generation_mode = get_generation_mode(config)
        negative_prompt_template = load_negative_prompt_template(config)

        # 使用高级生成器
        use_progressive = (generation_mode == "advanced")

        return await generate_batch_images_advanced(
            tweets_batch=tweets_batch,
            output_dir=output_dir,
            model_path=model_path,
            device=device,
            use_progressive=use_progressive,
            negative_prompt_template=negative_prompt_template,
            start_slot=start_slot,
            max_images=max_images
        )

    # 使用原有生成器（备用方案）
    generator = ZImageGenerator(model_path=model_path, device=device, use_diffusers=use_diffusers)

    tweets = tweets_batch["tweets"]
    persona_name = tweets_batch["persona"]["name"]
    day_offset = tweets_batch.get("daily_plan", {}).get("day_offset", None)  # 获取day信息
    total = len(tweets)
    end_slot = min(total, start_slot + max_images) if max_images else total

    logger.info(f"📊 单GPU批量生成")
    logger.info(f"   人设: {persona_name}")
    logger.info(f"   范围: slot {start_slot} ~ {end_slot-1}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for i in range(start_slot, end_slot):
        tweet = tweets[i]
        img_gen = tweet["image_generation"]

        # 提取参数（安全访问）
        positive_prompt = img_gen.get("positive_prompt", "")
        negative_prompt = img_gen.get("negative_prompt", "")

        # LoRA参数（可选）
        lora_params = img_gen.get("lora_params", {})
        lora_path = lora_params.get("model_path", "")
        lora_strength = lora_params.get("strength", 1.0)

        # 生成参数（使用默认值）
        gen_params = img_gen.get("generation_params", {})
        width = gen_params.get("width", 1024)
        height = gen_params.get("height", 1024)
        steps = gen_params.get("steps", 9)
        cfg = gen_params.get("cfg", 0.0)

        # 生成文件名（包含day信息）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if day_offset is not None:
            filename = f"{persona_name}_day{day_offset}_slot{i}_{timestamp}.png"
        else:
            filename = f"{persona_name}_slot{i}_{timestamp}.png"
        output_path = output_dir / filename

        logger.info(f"🎨 生成 slot {i+1}/{total}: {tweet['topic_type']}")

        try:
            # 生成图片
            image = generator.generate_image(
                positive_prompt=positive_prompt,
                negative_prompt=negative_prompt,
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
                "tweet_text": tweet["tweet_text"]
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


# ============ 多GPU并发生成 ============

import torch.multiprocessing as mp
from queue import Empty


def _worker_generate_images(
    gpu_id: int,
    task_queue: mp.Queue,
    result_queue: mp.Queue,
    model_path: str,
    tweets_batch: Dict,
    output_dir: str,
    use_diffusers: bool = True
):
    """
    多GPU worker进程 - 在指定GPU上生成图片

    Args:
        gpu_id: GPU编号
        task_queue: 任务队列（接收slot索引）
        result_queue: 结果队列
        model_path: 模型路径
        tweets_batch: 推文批次
        output_dir: 输出目录
        use_diffusers: 是否使用diffusers模式
    """
    # 设置当前进程使用的GPU
    device = f"cuda:{gpu_id}"
    torch.cuda.set_device(gpu_id)

    # 初始化生成器
    generator = ZImageGenerator(model_path=model_path, device=device, use_diffusers=use_diffusers)

    tweets = tweets_batch["tweets"]
    persona_name = tweets_batch["persona"]["name"]
    day_offset = tweets_batch.get("daily_plan", {}).get("day_offset", None)  # 获取day信息
    output_dir = Path(output_dir)

    print(f"✓ GPU {gpu_id} worker 启动")

    while True:
        try:
            # 从队列获取任务（超时1秒）
            slot_idx = task_queue.get(timeout=1)

            if slot_idx is None:  # 结束信号
                break

            tweet = tweets[slot_idx]
            img_gen = tweet["image_generation"]

            # 提取参数（安全访问）
            positive_prompt = img_gen.get("positive_prompt", "")
            negative_prompt = img_gen.get("negative_prompt", "")

            # LoRA参数（可选）
            lora_params = img_gen.get("lora_params", {})
            lora_path = lora_params.get("model_path", "")
            lora_strength = lora_params.get("strength", 1.0)

            # 生成参数（使用默认值）
            gen_params = img_gen.get("generation_params", {})
            width = gen_params.get("width", 1024)
            height = gen_params.get("height", 1024)
            steps = gen_params.get("steps", 9)
            cfg = gen_params.get("cfg", 0.0)

            # 生成文件名（包含day信息）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if day_offset is not None:
                filename = f"{persona_name}_day{day_offset}_slot{slot_idx}_{timestamp}.png"
            else:
                filename = f"{persona_name}_slot{slot_idx}_{timestamp}.png"
            output_path = output_dir / filename

            print(f"🎨 GPU {gpu_id} 生成 slot {slot_idx}: {tweet['topic_type']}")

            try:
                # 生成图片
                image = generator.generate_image(
                    positive_prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    steps=steps,
                    cfg=cfg,
                    lora_path=lora_path,
                    lora_strength=lora_strength
                )

                # 保存
                image.save(output_path)

                result_queue.put({
                    "slot": slot_idx,
                    "gpu": gpu_id,
                    "status": "success",
                    "output_path": str(output_path),
                    "tweet_text": tweet["tweet_text"]
                })

                print(f"   ✓ GPU {gpu_id} 完成 slot {slot_idx}")

            except Exception as e:
                print(f"   ❌ GPU {gpu_id} 失败 slot {slot_idx}: {e}")
                result_queue.put({
                    "slot": slot_idx,
                    "gpu": gpu_id,
                    "status": "failed",
                    "error": str(e)
                })

        except Empty:
            continue
        except Exception as e:
            print(f"❌ GPU {gpu_id} worker异常: {e}")
            break

    print(f"✓ GPU {gpu_id} worker 结束")


async def generate_batch_images_multi_gpu(
    tweets_batch: Dict,
    output_dir: str,
    model_path: str,
    num_gpus: int = None,
    start_slot: int = 0,
    max_images: Optional[int] = None,
    use_diffusers: bool = True
) -> List[Dict]:
    """
    多GPU并发批量生成图片

    Args:
        tweets_batch: 推文批次JSON
        output_dir: 输出目录
        model_path: Z-Image模型路径
        num_gpus: 使用的GPU数量（None=自动检测全部GPU）
        start_slot: 起始slot
        max_images: 最大生成数量
        use_diffusers: 是否使用diffusers模式（支持LoRA）

    Returns:
        生成结果列表
    """
    # 检测可用GPU
    if not torch.cuda.is_available():
        logger.warning("⚠️  CUDA不可用，回退到单GPU模式")
        return await generate_batch_images_single_gpu(
            tweets_batch, output_dir, model_path, "cpu", start_slot, max_images, use_diffusers
        )

    total_gpus = torch.cuda.device_count()
    if num_gpus is None:
        num_gpus = total_gpus
    else:
        num_gpus = min(num_gpus, total_gpus)

    if num_gpus == 1:
        logger.info("使用单GPU模式")
        return await generate_batch_images_single_gpu(
            tweets_batch, output_dir, model_path, "cuda:0", start_slot, max_images, use_diffusers
        )

    logger.info(f"🚀 多GPU并发生成模式")
    logger.info(f"   可用GPU: {total_gpus}")
    logger.info(f"   使用GPU: {num_gpus}")

    tweets = tweets_batch["tweets"]
    total = len(tweets)
    end_slot = min(total, start_slot + max_images) if max_images else total

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 创建任务队列和结果队列
    mp.set_start_method('spawn', force=True)
    task_queue = mp.Queue()
    result_queue = mp.Queue()

    # 填充任务队列
    for i in range(start_slot, end_slot):
        task_queue.put(i)

    # 添加结束信号
    for _ in range(num_gpus):
        task_queue.put(None)

    # 启动worker进程
    processes = []
    for gpu_id in range(num_gpus):
        p = mp.Process(
            target=_worker_generate_images,
            args=(gpu_id, task_queue, result_queue, model_path, tweets_batch, output_dir, use_diffusers)
        )
        p.start()
        processes.append(p)

    logger.info(f"   ✓ 启动 {num_gpus} 个GPU worker")

    # 收集结果
    results = []
    expected_count = end_slot - start_slot

    while len(results) < expected_count:
        try:
            result = result_queue.get(timeout=300)  # 5分钟超时
            results.append(result)
            logger.info(f"   进度: {len(results)}/{expected_count}")
        except Empty:
            logger.warning("⚠️  结果队列超时")
            break

    # 等待所有进程结束
    for p in processes:
        p.join(timeout=10)
        if p.is_alive():
            p.terminate()

    # 按slot排序
    results.sort(key=lambda x: x["slot"])

    success_count = sum(1 for r in results if r["status"] == "success")
    logger.info(f"\n✅ 多GPU生成完成")
    logger.info(f"   成功: {success_count}/{expected_count}")
    logger.info(f"   输出: {output_dir}\n")

    return results


class ImageGenerationCoordinator:
    """图片生成协调器 - 支持单GPU和多GPU模式，支持LoRA，支持新旧方案切换"""

    def __init__(
        self,
        model_path: str = "Z-Image/ckpts/Z-Image-Turbo",
        num_gpus: int = None,
        use_diffusers: bool = True,
        use_advanced: bool = None  # None=从配置读取，True=强制使用高级模式，False=强制使用备用模式
    ):
        self.model_path = model_path
        self.num_gpus = num_gpus
        self.use_diffusers = use_diffusers

        # 决定是否使用高级模式
        if use_advanced is None:
            # 从配置文件读取
            from config.image_config import load_image_config, get_generation_mode
            config = load_image_config()
            generation_mode = get_generation_mode(config)
            self.use_advanced = (generation_mode == "advanced")
        else:
            self.use_advanced = use_advanced

        logger.info(f"🔧 ImageGenerationCoordinator 初始化")
        logger.info(f"   生成模式: {'高级模式 (三阶段渐进式)' if self.use_advanced else '备用模式 (单阶段生成)'}")

    async def generate_from_tweets_batch(
        self,
        tweets_batch_file: str,
        output_dir: str = "output_images",
        start_slot: int = 0,
        max_images: Optional[int] = None,
        use_multi_gpu: bool = True
    ) -> List[Dict]:
        """
        从推文批次文件生成图片

        Args:
            tweets_batch_file: 推文批次JSON文件
            output_dir: 输出目录
            start_slot: 起始slot
            max_images: 最大生成数量
            use_multi_gpu: 是否使用多GPU（默认True）

        Returns:
            生成结果列表
        """
        import json

        # 加载推文批次
        with open(tweets_batch_file, 'r', encoding='utf-8') as f:
            tweets_batch = json.load(f)

        logger.info(f"📂 从推文批次生成图片")
        logger.info(f"   文件: {tweets_batch_file}")
        logger.info(f"   人设: {tweets_batch['persona']['name']}")
        logger.info(f"   推文数: {len(tweets_batch['tweets'])}")
        logger.info(f"   模式: {'Diffusers (支持LoRA)' if self.use_diffusers else 'PyTorch原生'}")
        logger.info(f"   生成方案: {'高级 (三阶段渐进式)' if self.use_advanced else '备用 (单阶段)'}")

        # 选择生成模式
        if use_multi_gpu and torch.cuda.is_available() and torch.cuda.device_count() > 1:
            # 多GPU模式暂不支持高级生成器，使用备用方案
            if self.use_advanced:
                logger.warning("⚠️  多GPU模式暂不支持高级生成器，使用备用方案")
                use_advanced_for_this_run = False
            else:
                use_advanced_for_this_run = False

            results = await generate_batch_images_multi_gpu(
                tweets_batch=tweets_batch,
                output_dir=output_dir,
                model_path=self.model_path,
                num_gpus=self.num_gpus,
                start_slot=start_slot,
                max_images=max_images,
                use_diffusers=self.use_diffusers
            )
        else:
            results = await generate_batch_images_single_gpu(
                tweets_batch=tweets_batch,
                output_dir=output_dir,
                model_path=self.model_path,
                device="cuda" if torch.cuda.is_available() else "cpu",
                start_slot=start_slot,
                max_images=max_images,
                use_diffusers=self.use_diffusers,
                use_advanced=self.use_advanced  # 传递高级模式标志
            )

        return results
