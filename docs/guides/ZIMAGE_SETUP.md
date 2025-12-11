# Z-Image 环境配置完成 ✅

## 📋 配置概览

Z-Image-Turbo 图片生成环境已成功配置！

## ✅ 已完成的配置

### 1. 依赖安装
- ✅ PyTorch 2.9.1 + CUDA 12.8
- ✅ Transformers 4.57.3
- ✅ Diffusers 0.36.0.dev0（支持 Z-Image）
- ✅ Safetensors、Pillow、Accelerate 等依赖

### 2. 模型下载
- ✅ Z-Image-Turbo 模型已下载
- 📍 位置：`Z-Image/ckpts/Z-Image-Turbo`
- 💾 大小：约 30.58 GB（7个权重文件）
- 🔧 配置文件：model_index.json, text_encoder, transformer, vae

### 3. 硬件环境
- 🖥️ **GPU**: 8x NVIDIA GeForce RTX 4090
- 💾 **显存**: 每个 23.64 GB（总计约 189 GB）
- 🚀 **CUDA**: 12.8
- 🐍 **Python**: 3.11.13

## 🎨 使用方法

### 快速测试

```bash
# 测试环境（不加载模型，快速检查）
python test_zimage.py --skip-model-loading

# 生成测试图片（会加载模型）
python quick_test_zimage.py
```

### 完整工作流：推文生成 + 图片生成

```bash
# 1. 生成推文批次（带图片元数据）
python main.py \
  --persona personas/character.json \
  --calendar calendars/character_2024-12.json \
  --tweets 10

# 2. 从推文批次生成图片
python main.py \
  --generate-images \
  --tweets-batch output_standalone/character_20241207_153045.json \
  --num-gpus 8  # 使用所有8个GPU
```

### 图片生成选项

**单GPU模式：**
```bash
python main.py \
  --generate-images \
  --tweets-batch output_standalone/xxx.json \
  --single-gpu
```

**多GPU并发模式（推荐）：**
```bash
python main.py \
  --generate-images \
  --tweets-batch output_standalone/xxx.json \
  --num-gpus 8  # 或指定数量
```

**限制生成数量：**
```bash
python main.py \
  --generate-images \
  --tweets-batch output_standalone/xxx.json \
  --max-images 5  # 只生成前5张
  --start-slot 0  # 从第0个slot开始
```

## 📂 文件结构

```
auto-tweet-generator/
├── Z-Image/
│   └── ckpts/
│       └── Z-Image-Turbo/       # 模型文件（30GB）
│           ├── model_index.json
│           ├── text_encoder/
│           ├── transformer/
│           └── vae/
│
├── download_zimage_model.py     # 模型下载脚本
├── test_zimage.py               # 环境测试脚本
├── quick_test_zimage.py         # 快速生成测试图片
├── core/
│   └── image_generator.py       # Z-Image 生成器
└── output_images/               # 生成的图片保存目录
```

## 🚀 性能优化

### 多GPU并发
- 8个 RTX 4090 可以并发生成8张图片
- 每张图片约 8 步生成，约 1-2 秒
- 理论吞吐量：~240 图片/分钟（8 GPU × 30 图/分钟）

### 显存优化
- 使用 `bfloat16` 数据类型（减少显存使用）
- 支持 Flash Attention 2/3（如果可用）
- 可选模型编译（首次运行较慢，后续加速）

### Diffusers 模式优势
- ✅ 原生支持 LoRA
- ✅ 自动管理显存
- ✅ 更好的稳定性
- ✅ 社区支持完善

## ⚠️ 注意事项

1. **首次加载**：首次加载模型需要约 1-2 分钟，请耐心等待
2. **显存使用**：单个模型约占用 14-16 GB 显存（bfloat16）
3. **并发数量**：建议不超过 GPU 数量，避免显存溢出
4. **模型位置**：不要移动 `Z-Image/ckpts/Z-Image-Turbo` 目录

## 🐛 常见问题

### Q: 提示 "CUDA out of memory"
A: 减少并发数量或使用 `--single-gpu` 模式

### Q: 生成速度慢
A:
- 确保使用 `bfloat16` 数据类型
- 启用 Flash Attention（自动检测）
- 使用多GPU并发模式

### Q: 模型加载失败
A:
- 检查模型文件是否完整：`python test_zimage.py`
- 确保 diffusers 版本正确：`pip install git+https://github.com/huggingface/diffusers`

## 📚 相关文档

- [Z-Image 官方文档](https://github.com/Tongyi-MAI/Z-Image)
- [Diffusers 文档](https://huggingface.co/docs/diffusers)
- [项目 README](README.md)

## 🎉 下一步

1. ✅ 环境配置完成
2. ⏭️ 测试推文生成：`python main.py --persona ... --tweets 5`
3. ⏭️ 测试图片生成：`python main.py --generate-images --tweets-batch ...`
4. ⏭️ 完整工作流测试：推文 → 图片 → 输出

---

配置完成时间：2025-12-07
Python 版本：3.11.13
PyTorch 版本：2.9.1+cu128
GPU 配置：8x RTX 4090 (23.64 GB 每个)
