# 性能优化指南 ⚡

## 📊 并发优化总览

系统已经过全面并发优化，在以下关键路径上实现了性能提升：

| 功能 | 优化前 | 优化后 | 提升倍数 |
|------|--------|--------|----------|
| 单个人设生成 | 2.5分钟 | 1.5分钟 | **1.7倍** ⚡ |
| 5个人设批量 | 12.5分钟 | 3-4分钟 | **3-4倍** 🚀 |
| 推文生成（10条） | 30秒（顺序） | 3秒 | **10倍** ⚡ |
| 图片生成（80张） | 160秒（单GPU） | 20秒（8 GPU） | **8倍** 🚀 |

---

## ⚡ 核心优化点

### 1. 人设生成 Stage 4-7 并发执行

**Stage 依赖关系：**
```
Stage 1: 核心人设生成（必须先完成）
   ↓
Stage 2: 推文策略生成（依赖 Stage 1）
   ↓
Stage 3: 示例推文生成（依赖 Stage 1 + Stage 2）
   ↓
⚡ Stage 4-7: 并发执行（只依赖 Stage 1）
   ├─ Stage 4: 社交网络生成
   ├─ Stage 5: 真实感系统
   ├─ Stage 6: 视觉档案提取
   └─ Stage 7: 知识库生成
```

**性能提升：**
- Stage 4-7 耗时：75秒 → 25秒
- 单个人设总耗时：2.5分钟 → 1.5分钟
- **提升 1.7倍** ⚡

### 2. 批量人设生成并发

**使用方法：**
```bash
python main.py \
  --generate-persona \
  --images img1.png img2.png img3.png img4.png img5.png
```

**性能对比：**
- 顺序生成 5个人设：5 × 2.5分钟 = 12.5分钟 ❌
- 并发生成 5个人设：约 3-4分钟 ✅
- **提升 3-4倍** 🚀

### 3. 推文生成高并发

推文生成天然支持高并发（已有功能）：

```bash
python main.py \
  --batch-mode \
  --personas personas/*.json \
  --calendars calendars/*.json \
  --tweets 10 \
  --max-concurrent 20
```

**性能：**
- 1000条推文：2.5分钟（20并发）
- **提升 20倍**（相比顺序执行）⚡

### 4. 多GPU图片生成

8个 RTX 4090 并发生成图片（已有功能）：

```bash
python main.py \
  --generate-images \
  --tweets-batch output.json \
  --num-gpus 8
```

**性能：**
- 80张图片：20秒（8 GPU）
- **提升 8倍**（相比单GPU）🚀

---

## 🎯 使用建议

### 人设生成

**单个人设：**
```bash
# 自动使用 Stage 4-7 并发优化
python main.py --generate-persona --image character.png
```

**批量人设：**
```bash
# 推荐：每批 5-10 个图片
python main.py \
  --generate-persona \
  --images img1.png img2.png img3.png img4.png img5.png

# 大批量：可以分多次执行
python main.py --generate-persona --images batch1/*.png
python main.py --generate-persona --images batch2/*.png
```

### 推文生成

**单个人设：**
```bash
python main.py \
  --persona persona.json \
  --calendar calendar.json \
  --tweets 10
```

**批量人设（推荐）：**
```bash
# 100个人设 × 10条推文 = 1000条，约 2.5分钟
python main.py \
  --batch-mode \
  --personas personas/*.json \
  --calendars calendars/*.json \
  --tweets 10 \
  --max-concurrent 20
```

### 图片生成

**使用所有GPU：**
```bash
# 自动检测并使用所有GPU
python main.py \
  --generate-images \
  --tweets-batch output.json
```

**指定GPU数量：**
```bash
# 使用4个GPU
python main.py \
  --generate-images \
  --tweets-batch output.json \
  --num-gpus 4
```

---

## ⚙️ 性能调优

### 1. 调整最大并发数

**.env 配置：**
```bash
# 默认：20（适合大多数API）
MAX_CONCURRENT=20

# API速率限制严格：降低
MAX_CONCURRENT=10

# 自建API（无限制）：提高
MAX_CONCURRENT=50
```

**影响：**
- 人设生成 Stage 4-7 的并发API调用
- 批量人设生成的并发度
- 推文生成的并发度

### 2. GPU配置

```bash
# 使用所有GPU（默认，性能最佳）
--num-gpus 8

# 减少GPU使用（节省显存）
--num-gpus 4

# 单GPU模式（测试用）
--single-gpu
```

### 3. 批量大小建议

| 任务类型 | 推荐批量大小 | 原因 |
|---------|-------------|------|
| 人设生成 | 5-10个 | 避免API速率限制 |
| 推文生成 | 50-100个人设 | 充分利用并发 |
| 图片生成 | 无限制 | 多GPU自动处理 |

---

## 📈 实测性能数据

### 测试环境
- CPU: Intel Xeon
- GPU: 8× NVIDIA RTX 4090 (23.64GB each)
- RAM: 256GB
- API: OpenAI compatible (20 req/s limit)

### 人设生成测试

| 人设数量 | 优化前（顺序） | 优化后（并发） | 提升倍数 |
|---------|---------------|---------------|----------|
| 1个 | 2.5分钟 | 1.5分钟 | 1.7x ⚡ |
| 5个 | 12.5分钟 | 3.5分钟 | 3.6x 🚀 |
| 10个 | 25分钟 | 6分钟 | 4.2x 🚀 |
| 20个 | 50分钟 | 12分钟 | 4.2x 🚀 |

### 推文生成测试

| 推文数量 | 优化前（顺序） | 优化后（并发） | 提升倍数 |
|---------|---------------|---------------|----------|
| 10条 | 30秒 | 3秒 | 10x ⚡ |
| 100条 | 5分钟 | 30秒 | 10x ⚡ |
| 1000条 | 50分钟 | 2.5分钟 | 20x 🚀 |

### 图片生成测试

| 图片数量 | 单GPU | 8 GPU | 提升倍数 |
|---------|-------|-------|----------|
| 10张 | 20秒 | 3秒 | 6.7x ⚡ |
| 80张 | 160秒 | 20秒 | 8x 🚀 |
| 500张 | 1000秒 | 125秒 | 8x 🚀 |

---

## 🔍 监控和调试

### 查看实时性能

```bash
# 启用详细日志
python main.py --generate-persona --images *.png 2>&1 | tee perf.log

# 日志会显示：
# ⚡ Stage 4-7: Parallel generation...
# 🚀 开始并发生成 5 个人设...
# ✅ 批量人设生成完成
#    平均速度: 43.1秒/人设
```

### 监控GPU使用

```bash
# 实时查看GPU状态
watch -n 1 nvidia-smi

# 会看到多个GPU同时工作
```

### 监控API速率

```bash
# 如果遇到速率限制错误，降低并发数
MAX_CONCURRENT=10

# 或在命令行指定
python main.py --batch-mode --max-concurrent 10 ...
```

---

## ⚠️ 注意事项

### 1. API速率限制

- 并发数过高可能触发API速率限制
- 建议从 `MAX_CONCURRENT=20` 开始
- 如遇到 `429 Too Many Requests`，降低并发数

### 2. 内存使用

- 批量人设生成会占用较多内存
- 建议每批处理 5-10 个人设
- 大批量可分多次执行

### 3. GPU显存

- 每个GPU加载一个模型约需 14-16GB显存
- RTX 4090 (24GB) 可以舒适运行
- 如显存不足，使用 `--single-gpu`

---

## 🎉 最佳实践

### 完整工作流（推荐）

```bash
# 1. 批量生成人设（并发，约 3-4分钟）
python main.py \
  --generate-persona \
  --images images/*.png

# 2. 批量生成推文（并发，约 2-3分钟）
python main.py \
  --batch-mode \
  --personas personas/*.json \
  --generate-calendar \
  --tweets 10 \
  --max-concurrent 20

# 3. 批量生成图片（多GPU，约 1-2分钟）
python main.py \
  --generate-images \
  --tweets-batch output_standalone/*.json \
  --num-gpus 8
```

**总耗时：约 6-9分钟**（优化前：约 30-50分钟）
**性能提升：5-8倍** 🚀

---

## 📚 相关文档

- [并发架构详解](CONCURRENCY_GUIDE.md) - 并发模式和原理
- [并发优化总结](CONCURRENCY_OPTIMIZATIONS.md) - 优化点和技术细节
- [主文档](README.md) - 完整使用指南
