# Native Image Generation - 实现进展总结

## 当前状态

### 已完成
- ✅ 设计文档 (`docs/NATIVE_IMAGE_GENERATION_DESIGN.md`)
- ✅ 配置文件 (`config/native_image_generation.yaml`)
- ✅ 目录结构 (`core/models/`, `core/pipelines/`)
- ✅ Z-Image模型确认可用 (`Z-Image/ckpts/Z-Image-Turbo`)

### Z-Image原生API分析

Z-Image提供了原生PyTorch API，非常简洁：

```python
# Z-Image/inference.py 核心调用
from utils import load_from_local_dir, set_attention_backend
from zimage import generate

# 加载模型
components = load_from_local_dir(model_path, device=device, dtype=dtype, compile=compile)
set_attention_backend("_native_flash")

# 生成图片
images = generate(
    prompt=prompt,
    **components,
    height=height,
    width=width,
    num_inference_steps=num_inference_steps,
    guidance_scale=guidance_scale,
    generator=torch.Generator(device).manual_seed(seed),
)
```

## 下一步实现计划

### 方案A: 直接封装Z-Image (推荐)

**优势**:
- 最简单，直接使用Z-Image的原生API
- 无需理解复杂的Diffusers实现
- 性能最优（Z-Image官方优化）

**实现步骤**:
1. 创建 `core/native_image_generator.py`，封装Z-Image API
2. 添加LoRA支持（需要查看Z-Image是否支持）
3. 实现渐进式生成（可能需要多次调用generate）

```python
# 伪代码
class NativeImageGenerator:
    def __init__(self):
        sys.path.insert(0, 'Z-Image')
        from utils import load_from_local_dir
        from zimage import generate

        self.generate_fn = generate
        self.components = load_from_local_dir(...)

    def generate(self, prompt, **kwargs):
        return self.generate_fn(
            prompt=prompt,
            **self.components,
            **kwargs
        )
```

### 方案B: 使用Diffusers

**优势**:
- 标准化，易于维护
- 内置LoRA支持
- 社区支持好

**劣势**:
- 需要转换Z-Image模型到Diffusers格式
- 可能性能不如原生

## 快速验证测试

### 测试1: Z-Image基础功能

```bash
cd Z-Image
python inference.py
```

### 测试2: 修改尺寸为672×864

修改 `Z-Image/inference.py`:
```python
height = 864
width = 672
```

### 测试3: 验证LoRA加载

查看Z-Image是否支持LoRA：
```bash
grep -r "lora" Z-Image/ --include="*.py"
```

## ComfyUI工作流三阶段渐进式生成

**问题**: Z-Image原生API似乎不支持渐进式生成

**解决方案**:
1. **简化方案**: 单次生成672×864（放弃渐进式）
   - 优点: 简单，快速
   - 缺点: 质量可能略低于三阶段

2. **完整方案**: 使用img2img实现渐进式
   - Stage 1: 生成176×224
   - Stage 2: 放大到336×432，img2img refine
   - Stage 3: 放大到672×864，img2img refine
   - 需要查看Z-Image是否支持img2img

## 建议的下一步操作

1. **立即可做**:
   - 测试Z-Image基础生成
   - 修改尺寸为672×864验证
   - 检查LoRA支持情况

2. **如果Z-Image支持LoRA**:
   - 直接封装Z-Image API
   - 创建简化版NativeImageGenerator
   - 单阶段生成即可上线

3. **如果需要渐进式或LoRA不支持**:
   - 考虑使用Diffusers
   - 或者继续使用ComfyUI作为主方案

## 性能预期

### 单阶段生成 (Z-Image直接生成672×864)
- 预计时间: ~3-5秒 (8-10 steps)
- 内存占用: ~8GB
- vs ComfyUI三阶段: 快6-10倍

### 渐进式生成 (如果实现)
- 预计时间: ~8-12秒
- 仍比ComfyUI快2-3倍

## 关键代码位置

- Z-Image API: `Z-Image/zimage/`
- Z-Image inference: `Z-Image/inference.py`
- 工作流参考: `legacy/workflow/zimage-api-121104.json`
- ComfyUI客户端: `core/comfyui_client.py` (作为对比参考)

## 待验证问题

- [ ] Z-Image是否支持LoRA？
- [ ] Z-Image是否支持img2img（渐进式生成需要）？
- [ ] Z-Image的负面提示词如何使用？
- [ ] 如何在Z-Image中控制种子？（已知：通过Generator）

## 总结

**推荐路径**:
1. 先用Z-Image原生API实现单阶段生成作为MVP
2. 测试质量是否可接受
3. 如果质量OK，直接上线（速度提升巨大）
4. 如果质量不够，再考虑渐进式或回退ComfyUI

**时间估算**:
- MVP实现: 2-3小时
- 完整测试: 1-2小时
- 总计: 半天内可完成

**风险**:
- Low: Z-Image API已验证可用
- Medium: LoRA支持未知
- High: 渐进式生成可能需要额外工作
