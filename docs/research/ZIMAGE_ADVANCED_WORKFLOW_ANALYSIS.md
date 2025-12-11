# Z-Image 高级工作流分析 (zimage-121101.json)

## 工作流概览

这是一个基于 Z-Image 的三阶段生成流程，实现了从低分辨率到高分辨率的渐进式图片生成。

## 核心架构

### 1. 模型加载组件

```
组件                            路径/配置                          用途
---------------------------------------------------------------------------------------------
UNETLoader (节点16)             z_image_turbo_bf16.safetensors    主扩散模型
VAELoader (节点17)              ae.safetensors                    VAE解码器
CLIPLoader (节点146)            qwen_3_4b.safetensors             文本编码器 (GGUF格式，Lumina2类型)
LoraLoader (节点270)            zimage_lora__avrupali_turkler_    LoRA权重 (强度: 1.0)
```

**关键发现**：
- 使用 `qwen_3_4b.safetensors` 作为 CLIP 文本编码器（GGUF 格式，Lumina2 类型）
- LoRA 强度设为 **1.0**（满强度），直接作用于 UNet
- 使用 `CLIPLoaderGGUF` 节点，支持量化模型

### 2. 提示词配置

#### 正向提示词 (节点340)
```
sunway, redhead woman lying on bed, wearing black fishnet bodystocking
fully open at crotch, exposing herself, orange hair, colorful tattoos,
ear gauges, seductive pose, bedroom setting, highly detailed, explicit,
photorealistic.
```

#### Trigger Word (节点232)
```
Deedeemegadoodo photo, topless woman, extreme breast sagging on huge breasts,
large erect nipples, 硕大凸起的乳头, unidealized.
```

**关键发现**：
- Trigger word 包含 **中文词汇**，说明 CLIP 模型（Qwen）支持多语言
- 使用 LoRA 特定触发词 `Deedeemegadoodo photo`

#### 负向提示词 (节点7)
超长的中文负向提示词库（~2000+ 字符），包含：
- 动漫风格排除：动漫风, 二次元, 漫画风, 插画风...
- 技术缺陷排除：低清晰度, 模糊, 失焦, 噪点严重...
- AI痕迹排除：网红脸, AI网红脸, 完美对称脸, 磨皮过度...
- 商业模板排除：影楼风, 广告硬照, stock photo...

**关键发现**：
- 使用 **全中文** 负向提示词，说明 Qwen CLIP 的中文理解能力
- 比英文 negative prompt 更精细的语义控制

### 3. 三阶段生成流程

#### 阶段1：低分辨率基础生成 (节点316)
```yaml
输入latent尺寸: 176×224 (EmptySD3LatentImage)
Sampler: SamplerCustom + EulerAncestral
Scheduler: FlowMatchEulerDiscreteScheduler (Custom)
参数:
  steps: 9
  cfg: 2.0
  seed: 905124181980574
  eta: 1.0
  s_noise: 1.0

Scheduler配置:
  shift: 3
  time_shift_type: "exponential"
  base_shift: 0.5
  max_shift: 1.15
  num_train_timesteps: 1000
```

**关键发现**：
- 使用 **EmptySD3LatentImage** 初始化 latent（Z-Image 兼容 SD3 latent 空间）
- 使用 **FlowMatchEulerDiscreteScheduler**（Flow Matching 调度器）
- `shift=3` 用于控制时间步分布

#### 阶段2：中分辨率上采样 (节点321 + 节点276)
```yaml
上采样: LatentUpscale (nearest-exact)
  从 176×224 → 336×432 (约1.9倍)

KSampler参数:
  steps: 16
  cfg: 1.0
  denoise: 0.7
  sampler_name: "euler_ancestral"
  scheduler: "FlowMatchEulerDiscreteScheduler"
  seed: 182450993364532

模型增强:
  ModelSamplingAuraFlow (shift=7)
  EasyCache (reuse_threshold=0.37, start=0.45, end=0.95)
```

**关键发现**：
- 使用 **denoise=0.7** 进行部分重绘（保留70%的原始latent）
- **ModelSamplingAuraFlow** 调整采样流程（shift=7）
- **EasyCache** 缓存模型计算结果（优化性能）

#### 阶段3：高分辨率精修 (节点303 + 节点325)
```yaml
上采样: LatentUpscaleBy (scale_by=2)
  从 336×432 → 672×864 (2倍)

SamplerCustom参数:
  steps: 16
  cfg: 1.0
  denoise: 0.6
  sampler_name: "dpmpp_sde"
  scheduler: "beta"
  seed: 894355038471848

模型增强:
  ModelSamplingAuraFlow (shift=7)
  EasyCache (reuse_threshold=0.12, start=0.7, end=0.95)
```

**关键发现**：
- 使用 **DPM++ SDE** sampler（更高质量）
- **denoise=0.6** 降低重绘强度（保留更多细节）
- **beta scheduler** 替代 FlowMatch（用于精修阶段）

### 4. 输出流程

```
阶段1输出 → PreviewImage (节点338)
阶段2输出 → PreviewImage (节点310)
阶段3输出 → SaveImage (节点307, 文件名前缀: "2025-12-11/ComfyUI_Image")
```

## 与现有项目的对比

### 现有实现 (`core/image_generator.py`)
```python
# 单阶段生成
pipeline(
    prompt=positive_prompt,
    negative_prompt=negative_prompt,
    height=1024,
    width=768,
    num_inference_steps=9,
    guidance_scale=1.0,
)
```

### ComfyUI 工作流优势
1. **渐进式生成**：低→中→高分辨率，每阶段优化不同细节
2. **自定义调度器**：FlowMatchEulerDiscreteScheduler + ModelSamplingAuraFlow
3. **EasyCache 优化**：缓存中间计算结果
4. **多种 Sampler**：EulerAncestral (基础) → DPM++ SDE (精修)
5. **中文 CLIP**：Qwen 3.4B 支持中英混合提示词

## 实现建议

### 方案1：完全迁移到 Diffusers

在现有 `ZImageGenerator` 基础上扩展：

```python
class ZImageGeneratorAdvanced(ZImageGenerator):
    def generate_multistage(
        self,
        positive_prompt: str,
        negative_prompt: str,
        trigger_word: str = "",
        stage1_size: tuple = (176, 224),  # latent size
        stage2_size: tuple = (336, 432),
        stage3_size: tuple = (672, 864),
        stage1_steps: int = 9,
        stage2_steps: int = 16,
        stage3_steps: int = 16,
        stage1_cfg: float = 2.0,
        stage2_cfg: float = 1.0,
        stage3_cfg: float = 1.0,
        stage2_denoise: float = 0.7,
        stage3_denoise: float = 0.6,
        seeds: tuple = None,
    ) -> Image.Image:
        """
        三阶段渐进式生成
        """
        # 阶段1：低分辨率基础生成
        latent1 = self._stage1_generate(...)

        # 阶段2：上采样到中分辨率
        latent2 = self._upscale_latent(latent1, stage2_size)
        latent2 = self._stage2_refine(latent2, ...)

        # 阶段3：上采样到高分辨率
        latent3 = self._upscale_latent(latent2, stage3_size)
        image = self._stage3_refine(latent3, ...)

        return image
```

**难点**：
- Diffusers 的 `ZImagePipeline` 不直接支持 latent 操作
- 需要手动实现 `FlowMatchEulerDiscreteScheduler`
- `ModelSamplingAuraFlow` 和 `EasyCache` 需要修改 pipeline 内部逻辑

### 方案2：集成 ComfyUI Custom Nodes

**优势**：
- 直接复用 ComfyUI 节点实现（FlowMatch scheduler, EasyCache 等）
- 不需要重新实现复杂逻辑

**劣势**：
- 引入 ComfyUI 依赖（违背"完全解耦"原则）
- 需要处理 ComfyUI 节点加载和执行逻辑

### 方案3：提取关键组件（推荐）

**分阶段实现**：

#### Phase 1：基础能力（立即可实现）
```python
# 1. 支持 Qwen CLIP 文本编码器
class ZImageGeneratorQwen(ZImageGenerator):
    def _init_diffusers(self, model_path, ...):
        from transformers import AutoTokenizer, AutoModel

        # 加载 Qwen CLIP
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/...")
        self.text_encoder = AutoModel.from_pretrained("Qwen/...")

        # 替换 pipeline 的 text_encoder
        self.pipeline.text_encoder = self.text_encoder

# 2. 支持中文 negative prompt
# 已支持，无需修改

# 3. 支持 trigger word
def generate_with_trigger(
    self,
    positive_prompt: str,
    trigger_word: str = "",
    **kwargs
):
    # 合并 trigger word 到 prompt
    full_prompt = f"{trigger_word}, {positive_prompt}" if trigger_word else positive_prompt
    return self.generate_image(positive_prompt=full_prompt, **kwargs)
```

#### Phase 2：渐进式上采样（中等难度）
```python
# 使用 img2img 模拟多阶段生成
def generate_progressive(
    self,
    positive_prompt: str,
    negative_prompt: str,
    stages: List[Dict],  # [{size, steps, cfg, denoise}, ...]
):
    # 阶段1：txt2img 生成低分辨率
    image = self.pipeline(
        prompt=positive_prompt,
        height=stages[0]['size'][1],
        width=stages[0]['size'][0],
        num_inference_steps=stages[0]['steps'],
        guidance_scale=stages[0]['cfg'],
    ).images[0]

    # 阶段2-N：img2img 上采样精修
    for stage in stages[1:]:
        image = image.resize((stage['size'][0], stage['size'][1]), Image.LANCZOS)
        image = self.pipeline(
            prompt=positive_prompt,
            image=image,
            strength=stage['denoise'],  # denoise=0.7 → strength=0.7
            num_inference_steps=stage['steps'],
            guidance_scale=stage['cfg'],
        ).images[0]

    return image
```

**限制**：
- Diffusers 的 img2img 使用 `strength` 参数（与 ComfyUI 的 `denoise` 类似但不完全相同）
- 无法精确复制 FlowMatch scheduler 的行为

#### Phase 3：自定义 Scheduler（高难度）
```python
# 实现 FlowMatchEulerDiscreteScheduler
# 需要深入理解 Flow Matching 原理和 Z-Image 的时间步采样策略
```

## 配置文件扩展

在 `config/image_generation.yaml` 中添加：

```yaml
# 高级生成模式
advanced:
  enabled: false  # 是否启用多阶段生成

  clip:
    model: "qwen_3_4b"  # "default" | "qwen_3_4b"
    support_chinese: true

  progressive_generation:
    enabled: true
    stages:
      - name: "base"
        latent_size: [176, 224]
        steps: 9
        cfg: 2.0
        sampler: "euler_ancestral"

      - name: "refine"
        latent_size: [336, 432]
        steps: 16
        cfg: 1.0
        denoise: 0.7
        sampler: "euler_ancestral"

      - name: "upscale"
        latent_size: [672, 864]
        steps: 16
        cfg: 1.0
        denoise: 0.6
        sampler: "dpmpp_sde"

  trigger_word:
    enabled: true
    default: ""  # 可在 persona JSON 中指定
```

## 实现优先级建议

### 🔴 高优先级（立即实现）
1. **Trigger Word 支持**：在 `ZImageGenerator.generate_image()` 中添加 `trigger_word` 参数
2. **中文 Negative Prompt**：已支持，但需要在 `image_generation.yaml` 中添加默认中文 negative prompt 模板

### 🟡 中优先级（下周实现）
3. **渐进式上采样（简化版）**：使用 img2img 实现两阶段生成（512→1024）
4. **配置文件扩展**：添加 `advanced` 配置项

### 🟢 低优先级（研究性质）
5. **Qwen CLIP 集成**：需要测试 Qwen CLIP 与 Z-Image 的兼容性
6. **自定义 Scheduler**：深入研究 Flow Matching 实现

## 风险评估

### 高风险
- **Qwen CLIP 兼容性**：Z-Image 默认使用 T5 text encoder，切换到 Qwen 可能导致效果下降
- **Scheduler 实现**：FlowMatchEulerDiscreteScheduler 的参数（shift, time_shift_type 等）需要精确实现

### 中风险
- **img2img vs latent upscale**：Diffusers 的 img2img 在像素空间操作，ComfyUI 的 LatentUpscale 在 latent 空间，效果可能有差异

### 低风险
- **Trigger Word**：直接字符串拼接，无兼容性问题
- **中文 Negative Prompt**：已验证可用

## 下一步行动

### 建议的实现路径
1. **快速验证**：先实现 trigger word + 中文 negative prompt（工作量：1小时）
2. **测试效果**：生成对比图（当前单阶段 vs 添加 trigger word 后）
3. **评估收益**：如果 trigger word 效果显著，再考虑实现渐进式生成
4. **逐步增强**：根据效果决定是否实现更复杂的多阶段生成

### 测试计划
```bash
# 测试1：添加 trigger word
python main.py --generate-images \
  --tweets-batch output_standalone/test.json \
  --trigger-word "Deedeemegadoodo photo, unidealized"

# 测试2：中文 negative prompt
python main.py --generate-images \
  --tweets-batch output_standalone/test.json \
  --negative-prompt-file config/negative_prompts_zh.txt

# 测试3：渐进式生成（如果实现）
python main.py --generate-images \
  --tweets-batch output_standalone/test.json \
  --progressive-mode \
  --stages 3
```

## 总结

**核心价值**：
- ✅ **Trigger Word**：简单且高效（推荐优先实现）
- ✅ **中文 Negative Prompt**：已支持，需要整理默认模板
- ⚠️ **渐进式生成**：复杂度高，需要先验证收益
- ❌ **自定义 Scheduler**：需要深入研究，投入产出比待评估

**推荐方案**：先实现 trigger word 和中文 negative prompt，生成测试图后再决定是否投入渐进式生成。
