# Native Image Generation Design

## 概述

将ComfyUI工作流转换为项目原生实现，使用Diffusers库直接调用模型，消除对ComfyUI的依赖。

## 工作流分析

### ComfyUI工作流 (zimage-api-121104.json)

**三阶段渐进式生成**:

1. **Stage 1 - 初始生成** (176×224 latent)
   - Model: Z-Image (z_image_turbo_bf16.safetensors)
   - CLIP: Qwen 3.4B (qwen_3_4b.safetensors)
   - VAE: ae.safetensors
   - LoRA: 可选 (hollyjai.safetensors, 强度0.8)
   - Sampler: EulerAncestral
   - Scheduler: FlowMatchEulerDiscreteScheduler
   - Steps: 9
   - CFG: 2

2. **Stage 2 - 第一次放大** (336×432 latent)
   - Upscale: LatentUpscale (nearest-exact, 2x from Stage 1)
   - Sampler: KSampler (euler_ancestral)
   - Scheduler: FlowMatchEulerDiscreteScheduler
   - Steps: 16
   - CFG: 1
   - Denoise: 0.7
   - EasyCache: reuse_threshold=0.37, start=0.45, end=0.95

3. **Stage 3 - 第二次放大** (672×864 latent)
   - Upscale: LatentUpscaleBy (nearest-exact, 2x from Stage 2)
   - Sampler: SamplerCustom (dpmpp_sde)
   - Scheduler: BasicScheduler (beta)
   - Steps: 16
   - CFG: 1
   - Denoise: 0.6
   - EasyCache: reuse_threshold=0.12, start=0.7, end=0.95
   - VAE Decode: 最终输出 672×864 PNG

### 关键节点映射

| ComfyUI节点 | 功能 | Diffusers实现 |
|------------|------|--------------|
| UNETLoader | 加载模型 | `AutoPipelineForText2Image.from_pretrained()` |
| CLIPLoaderGGUF | 加载CLIP | `AutoTokenizer` + `CLIPTextModel` |
| VAELoader | 加载VAE | `AutoencoderKL.from_pretrained()` |
| LorapathLoader | 加载LoRA | `pipe.load_lora_weights()` |
| CLIPTextEncode | 文本编码 | `tokenizer` + `text_encoder` |
| KSampler | 采样器 | `pipe(..., num_inference_steps, guidance_scale)` |
| ModelSamplingAuraFlow | 时间步调度 | `FlowMatchEulerDiscreteScheduler` |
| EasyCache | 特征缓存优化 | 需要自定义实现 |
| LatentUpscale | Latent放大 | `torch.nn.functional.interpolate()` |
| VAEDecode | VAE解码 | `vae.decode()` |

## 原生实现方案

### 架构设计

```python
core/
├── native_image_generator.py      # 主生成器
├── models/
│   ├── __init__.py
│   ├── model_loader.py            # 模型加载器
│   ├── lora_manager.py            # LoRA管理
│   └── scheduler_config.py        # 调度器配置
└── pipelines/
    ├── __init__.py
    ├── zimage_pipeline.py         # Z-Image专用Pipeline
    └── progressive_pipeline.py    # 渐进式生成Pipeline
```

### 核心类设计

```python
class NativeImageGenerator:
    """
    原生图片生成器 - 无需ComfyUI
    """

    def __init__(
        self,
        model_path: str = "models/z_image_turbo_bf16",
        vae_path: str = "models/ae.safetensors",
        clip_path: str = "models/qwen_3_4b.safetensors",
        device: str = "cuda",
        torch_dtype: torch.dtype = torch.bfloat16
    ):
        self.device = device
        self.dtype = torch_dtype

        # 加载模型
        self.pipe = self._load_pipeline(model_path, vae_path, clip_path)
        self.lora_manager = LoRAManager(self.pipe)

    def _load_pipeline(self, model_path, vae_path, clip_path):
        """加载Diffusion Pipeline"""
        # 实现类似ComfyUI的模型加载
        pass

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        lora_path: str = None,
        lora_strength: float = 0.8,
        trigger_word: str = "",
        num_inference_steps: int = 9,
        guidance_scale: float = 2.0,
        seed: int = None,
        progressive: bool = True
    ) -> Image.Image:
        """
        生成图片

        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            lora_path: LoRA模型路径
            lora_strength: LoRA强度
            trigger_word: 触发词
            num_inference_steps: 推理步数
            guidance_scale: CFG强度
            seed: 随机种子
            progressive: 是否使用渐进式生成

        Returns:
            PIL Image (672×864)
        """
        # 加载LoRA
        if lora_path:
            self.lora_manager.load_lora(lora_path, lora_strength)

        # 设置种子
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        else:
            generator = None

        # 组装提示词
        full_prompt = f"{trigger_word}, {prompt}".strip(", ")

        if progressive:
            # 三阶段渐进式生成
            image = self._progressive_generate(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                generator=generator
            )
        else:
            # 单阶段直接生成
            image = self.pipe(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
                height=864,
                width=672
            ).images[0]

        # 卸载LoRA
        if lora_path:
            self.lora_manager.unload_lora()

        return image

    def _progressive_generate(
        self,
        prompt: str,
        negative_prompt: str,
        generator: torch.Generator
    ) -> Image.Image:
        """
        三阶段渐进式生成

        复现ComfyUI工作流的渐进式生成逻辑
        """
        # Stage 1: 176×224 → latent
        latent_1 = self._stage1_generate(
            prompt, negative_prompt, generator
        )

        # Stage 2: 336×432 → latent (upscale + refine)
        latent_2 = self._stage2_refine(
            latent_1, prompt, negative_prompt, generator
        )

        # Stage 3: 672×864 → image (upscale + refine + decode)
        image = self._stage3_refine(
            latent_2, prompt, negative_prompt, generator
        )

        return image
```

### 三阶段实现细节

```python
def _stage1_generate(self, prompt, negative_prompt, generator):
    """
    Stage 1: 初始生成 176×224

    对应ComfyUI节点: 316 (SamplerCustom)
    """
    # 配置调度器
    scheduler = FlowMatchEulerDiscreteScheduler(
        num_train_timesteps=1000,
        shift=3.0,
        # ... 其他参数见workflow
    )

    # 生成latent
    latent = self.pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        height=224,
        width=176,
        num_inference_steps=9,
        guidance_scale=2.0,
        generator=generator,
        output_type="latent"  # 返回latent而非图片
    ).images[0]

    return latent

def _stage2_refine(self, latent_1, prompt, negative_prompt, generator):
    """
    Stage 2: 第一次放大 336×432

    对应ComfyUI节点: 321 (LatentUpscale) + 276 (KSampler)
    """
    # Latent upscale (nearest-exact, 2x)
    latent_upscaled = F.interpolate(
        latent_1,
        size=(432 // 8, 336 // 8),  # VAE latent space = pixel / 8
        mode='nearest-exact'
    )

    # Refine with img2img
    latent_2 = self.pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=latent_upscaled,  # 使用upscaled latent作为输入
        strength=0.7,  # denoise=0.7
        num_inference_steps=16,
        guidance_scale=1.0,
        generator=generator,
        output_type="latent"
    ).images[0]

    return latent_2

def _stage3_refine(self, latent_2, prompt, negative_prompt, generator):
    """
    Stage 3: 第二次放大 672×864

    对应ComfyUI节点: 303 (LatentUpscaleBy) + 325 (SamplerCustom) + 328 (VAEDecode)
    """
    # Latent upscale by 2x
    latent_upscaled = F.interpolate(
        latent_2,
        scale_factor=2.0,
        mode='nearest-exact'
    )

    # Final refine with img2img
    image = self.pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=latent_upscaled,
        strength=0.6,  # denoise=0.6
        num_inference_steps=16,
        guidance_scale=1.0,
        generator=generator,
        output_type="pil"  # 最终解码为图片
    ).images[0]

    return image
```

## 依赖库

```txt
# requirements_native_image.txt
torch>=2.0.0
diffusers>=0.25.0
transformers>=4.36.0
accelerate>=0.25.0
safetensors>=0.4.0
pillow>=10.0.0
```

## 优势对比

| 特性 | ComfyUI方案 | 原生方案 |
|-----|------------|---------|
| 启动时间 | 需要启动4个ComfyUI实例 (~30s) | 直接加载模型 (~5s) |
| 内存占用 | 4个实例 × 8GB = 32GB | 单实例 8GB |
| 稳定性 | WebSocket可能断连/超时 | 直接调用,无网络层 |
| 并发性能 | 4实例并行,需要端口管理 | torch多GPU原生并行 |
| 调试难度 | 黑盒,需要看ComfyUI日志 | 完全可控,Python调试 |
| 维护成本 | 依赖ComfyUI版本 | 仅依赖Diffusers |

## 迁移计划

### Phase 1: 基础实现 (1-2天)
- [x] 分析ComfyUI工作流
- [ ] 实现NativeImageGenerator基础类
- [ ] 实现单阶段生成
- [ ] 测试LoRA加载

### Phase 2: 渐进式生成 (2-3天)
- [ ] 实现三阶段渐进式生成
- [ ] 复现调度器配置
- [ ] 实现EasyCache优化 (可选)
- [ ] 质量对比测试

### Phase 3: 集成测试 (1天)
- [ ] 替换core/comfyui_client.py中的调用
- [ ] 端到端测试
- [ ] 性能基准测试
- [ ] 回退ComfyUI作为备用方案

## 测试策略

```python
# test_native_generation.py
def test_single_stage():
    """测试单阶段生成"""
    generator = NativeImageGenerator()
    image = generator.generate(
        prompt="test prompt",
        progressive=False
    )
    assert image.size == (672, 864)

def test_progressive():
    """测试三阶段渐进式生成"""
    generator = NativeImageGenerator()
    image = generator.generate(
        prompt="test prompt",
        progressive=True
    )
    assert image.size == (672, 864)

def test_lora_loading():
    """测试LoRA加载"""
    generator = NativeImageGenerator()
    image = generator.generate(
        prompt="sunway, test prompt",
        lora_path="lora/hollyjai.safetensors",
        lora_strength=0.8,
        trigger_word="sunway"
    )
    assert image is not None

def test_quality_comparison():
    """ComfyUI vs 原生方案质量对比"""
    # 使用相同参数生成,对比SSIM/LPIPS
    pass
```

## 配置文件

```yaml
# native_image_config.yaml
model:
  path: "models/z_image_turbo_bf16"
  vae_path: "models/ae.safetensors"
  clip_path: "models/qwen_3_4b.safetensors"
  torch_dtype: "bfloat16"
  device: "cuda"

generation:
  progressive: true
  num_inference_steps: 9
  guidance_scale: 2.0

  stage1:
    height: 224
    width: 176
    steps: 9
    cfg: 2.0

  stage2:
    height: 432
    width: 336
    steps: 16
    cfg: 1.0
    denoise: 0.7

  stage3:
    height: 864
    width: 672
    steps: 16
    cfg: 1.0
    denoise: 0.6

lora:
  default_strength: 0.8
  cache_models: true

performance:
  enable_model_cpu_offload: false
  enable_vae_slicing: false
  enable_vae_tiling: false
```

## 回退方案

保留ComfyUI作为备用方案,通过配置切换:

```python
# core/image_generator_factory.py
def create_image_generator(backend: str = "native"):
    if backend == "native":
        return NativeImageGenerator()
    elif backend == "comfyui":
        return ComfyUIImageGenerator()
    else:
        raise ValueError(f"Unknown backend: {backend}")
```

## 参考资料

- Diffusers文档: https://huggingface.co/docs/diffusers
- Z-Image模型: https://huggingface.co/stabilityai/stable-diffusion-3-medium
- FlowMatchEulerDiscreteScheduler: https://github.com/huggingface/diffusers/blob/main/src/diffusers/schedulers/scheduling_flow_match_euler_discrete.py
- LoRA加载: https://huggingface.co/docs/diffusers/training/lora
