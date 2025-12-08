# 并发模式详解

## 📊 系统并发架构

本系统采用**混合并发模式**：
- **人设生成**：顺序执行（7个阶段有依赖关系）
- **推文生成**：高并发执行（支持20+并发）
- **图片生成**：多GPU并发执行（8个GPU可并发生成8张图片）

---

## 1️⃣ 人设生成流程（顺序执行）

### ❌ 为什么不并发？

人设生成的7个阶段**必须顺序执行**，因为存在**数据依赖关系**：

```
Stage 1: 核心人设生成
   ↓ (需要核心人设的结果)
Stage 2: 推文策略生成
   ↓ (需要核心人设 + 策略的结果)
Stage 3: 示例推文生成（8条）
   ↓ (需要核心人设的结果)
Stage 4: 社交网络生成
   ↓ (需要核心人设的结果)
Stage 5: 真实感系统生成
   ↓ (需要核心人设的结果)
Stage 6: 视觉档案提取
   ↓ (需要核心人设的结果)
Stage 7: 知识库生成
   ↓
最终合并所有组件
```

### 执行流程（代码层面）

```python
# core/persona_generator.py

async def generate_from_image(self, image_path, ...):
    # Stage 1 - 必须先完成
    core_persona = await self._generate_core_persona(...)

    # Stage 2 - 依赖 Stage 1 的结果
    strategy = await self._generate_tweet_strategy(core_persona, ...)

    # Stage 3 - 依赖 Stage 1 和 Stage 2 的结果
    tweets = await self._generate_example_tweets(core_persona, strategy, ...)

    # Stage 4 - 依赖 Stage 1 的结果
    social_data = await self._generate_social_network(core_persona, ...)

    # Stage 5 - 依赖 Stage 1 的结果
    authenticity = await self._generate_authenticity(core_persona, ...)

    # Stage 6 - 依赖 Stage 1 的结果
    visual_profile = await self._extract_visual_profile(core_persona, ...)

    # Stage 7 - 依赖 Stage 1 的结果
    character_book = await self._generate_character_book(core_persona, ...)

    # 最终合并
    complete_persona = self._merge_persona_components(...)

    return complete_persona
```

### ⏱️ 预计耗时

- **单个人设生成**：约 2-5 分钟（7个阶段）
  - 每个阶段 1-3 次 LLM API 调用
  - 总计约 10-15 次 LLM 调用
  - 取决于模型速度和响应时间

---

## 2️⃣ 推文生成流程（高并发）

### ✅ 支持并发！

推文生成**完全支持高并发**，可以同时生成多条推文：

```python
# core/tweet_generator.py

class BatchTweetGenerator:
    async def generate_batch(self, persona, calendar, tweets_count, context=None):
        """批量生成推文 - 高并发"""

        # 提取日历中的N天计划
        days = list(calendar_data["calendar"].items())[:tweets_count]

        # 创建并发任务列表
        tasks = []
        for slot, (date, plan) in enumerate(days, 1):
            # 为每一天创建一个独立的async任务
            task = self.single_generator.generate_single_tweet(
                persona=persona,
                calendar_plan=plan,
                context=context,
                ...
            )
            tasks.append(task)

        # 🚀 关键：使用 asyncio.gather() 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results
```

### 🔒 并发控制（速率限制）

使用 `asyncio.Semaphore` 限制并发数量，避免超过 API 限额：

```python
# utils/llm_client.py

class LLMClientPool:
    def __init__(self, max_concurrent=20):
        # 信号量：最多同时执行20个API调用
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def generate(self, messages, ...):
        # 获取信号量（如果已有20个在运行，会等待）
        async with self.semaphore:
            # 调用 LLM API
            response = await self.client.chat.completions.create(...)
            return response
```

### 📈 性能优势

**示例：生成10条推文**

- **顺序执行**（不并发）：
  - 每条推文 3 秒
  - 总耗时：10 × 3 = 30 秒 ❌

- **并发执行**（20并发）：
  - 10条推文同时生成
  - 总耗时：约 3-5 秒 ✅
  - **速度提升 6-10 倍**

---

## 3️⃣ 批量人设/推文生成（超高并发）

### 多个人设同时处理

```python
# main.py - HighConcurrencyCoordinator

async def generate_batch_tweets(self, persona_files, calendar_files, tweets_count):
    """批量模式：同时处理多个人设"""

    tasks = []
    for persona_file, calendar_file in zip(persona_files, calendar_files):
        # 为每个人设创建独立任务
        task = self.generate_single_persona_tweets(
            persona_file, calendar_file, tweets_count
        )
        tasks.append(task)

    # 🚀 并发执行所有人设的推文生成
    # 假设有 100 个人设，每个生成 10 条推文
    # = 1000 条推文同时在生成（受 max_concurrent=20 限制）
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return results
```

### 🎯 实际并发情况

假设：
- 100 个人设
- 每个人设生成 10 条推文
- `max_concurrent = 20`

**执行流程：**
1. 创建 100 个人设任务（每个任务内部有 10 条推文）
2. 所有任务并发启动
3. 在任意时刻，最多有 20 个 LLM API 调用在执行
4. 当一个 API 调用完成，立即启动下一个
5. 像流水线一样持续处理，直到全部完成

**预计耗时：**
- 总计 1000 条推文
- 每条 3 秒
- 并发数 20
- 总耗时：(1000 × 3) / 20 = 150 秒 ≈ **2.5 分钟**

如果不并发（顺序执行）：
- 总耗时：1000 × 3 = 3000 秒 ≈ **50 分钟** ❌

**速度提升：20 倍** 🚀

---

## 4️⃣ 图片生成（多GPU并发）

### 多GPU并发架构

```python
# core/image_generator.py

def generate_batch_images_multi_gpu(tweets_batch, num_gpus=8):
    """多GPU并发生成图片"""

    # 创建任务队列
    task_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()

    # 为每个GPU创建一个worker进程
    processes = []
    for gpu_id in range(num_gpus):
        p = multiprocessing.Process(
            target=gpu_worker,
            args=(gpu_id, task_queue, result_queue)
        )
        processes.append(p)
        p.start()

    # 分发任务到队列
    for slot, tweet in enumerate(tweets):
        task_queue.put((slot, tweet))

    # 等待所有任务完成
    results = []
    for _ in range(len(tweets)):
        result = result_queue.get()  # 阻塞等待
        results.append(result)

    return results
```

### 🖼️ 性能示例

**生成 80 张图片：**

- **单GPU**：
  - 每张 2 秒
  - 总耗时：80 × 2 = 160 秒 ≈ 2.7 分钟 ❌

- **8个GPU并发**：
  - 8个GPU同时生成
  - 总耗时：(80 × 2) / 8 = 20 秒 ✅
  - **速度提升：8 倍**

---

## 📊 完整工作流性能对比

### 场景：100个人设 × 10条推文 × 带图片

**不并发（顺序执行）：**
```
人设生成：100 × 3分钟 = 300分钟（5小时）
推文生成：1000 × 3秒 = 3000秒（50分钟）
图片生成：1000 × 2秒 = 2000秒（33分钟）
总耗时：6小时23分钟 ❌
```

**高并发模式：**
```
人设生成：100 × 3分钟（顺序，但可分批）= 300分钟（5小时）
推文生成：1000推文 / 20并发 × 3秒 = 150秒（2.5分钟）✅
图片生成：1000图片 / 8 GPU × 2秒 = 250秒（4分钟）✅
总耗时：5小时6.5分钟
```

**如果分批处理人设生成：**
```
将100个人设分成10批，每批10个
每批生成人设：10 × 3分钟 = 30分钟（并发生成推文和图片）
总耗时：10批 × 30分钟 = 5小时
```

---

## ⚙️ 并发参数配置

### 在 .env 中配置

```bash
# 推文生成最大并发数（默认：20）
MAX_CONCURRENT=20

# 如果遇到API速率限制，降低并发数
# MAX_CONCURRENT=10

# 如果使用本地LLM（无速率限制），可以提高
# MAX_CONCURRENT=50
```

### 命令行参数

```bash
# 推文生成并发数
python main.py \
  --batch-mode \
  --personas personas/*.json \
  --max-concurrent 20  # 调整这个值

# 图片生成GPU数量
python main.py \
  --generate-images \
  --tweets-batch output.json \
  --num-gpus 8  # 使用8个GPU并发
```

---

## 🎯 最佳实践建议

### 1. 推文生成并发数

| 场景 | 推荐并发数 | 原因 |
|------|----------|------|
| OpenAI API | 10-20 | 有速率限制 |
| 自建API（无限制） | 50-100 | 可以更高并发 |
| 免费API | 5-10 | 速率限制严格 |

### 2. 人设生成优化

虽然单个人设的7个阶段必须顺序执行，但可以：
- ✅ **批量生成多个人设**（多个人设并发）
- ❌ 无法加速单个人设的生成（阶段有依赖）

```bash
# 同时生成5个人设（5个人设并发，每个内部顺序执行7阶段）
python main.py --generate-persona --image img1.png &
python main.py --generate-persona --image img2.png &
python main.py --generate-persona --image img3.png &
python main.py --generate-persona --image img4.png &
python main.py --generate-persona --image img5.png &
```

### 3. 图片生成优化

- ✅ 使用所有可用GPU：`--num-gpus 8`
- ✅ 使用 bfloat16 数据类型（减少显存）
- ✅ 启用 Flash Attention（自动检测）

---

## 🔍 监控并发状态

### 查看日志输出

```bash
python main.py --batch-mode ... 2>&1 | tee output.log

# 日志会显示：
# [INFO] 协调器初始化完成
# [INFO]   最大并发: 20
# [INFO] 🔄 批量模式：处理 100 个人设
# [INFO]   ✓ 成功: 98
# [INFO]   ✗ 失败: 2
```

### 实时监控GPU使用

```bash
# 实时查看GPU使用情况
watch -n 1 nvidia-smi

# 会看到8个GPU都在工作
```

---

## 📝 总结

| 功能 | 并发模式 | 并发数量 | 速度提升 |
|------|---------|---------|---------|
| **人设生成（单个）** | ❌ 顺序执行 | 1 | 无法并发 |
| **人设生成（批量）** | ✅ 多个人设并发 | 可配置 | N倍（N=人设数量） |
| **推文生成** | ✅ 高并发 | 20（可配置） | 20倍 |
| **图片生成（单GPU）** | ❌ 顺序执行 | 1 | 无 |
| **图片生成（多GPU）** | ✅ 多GPU并发 | 8（可配置） | 8倍 |

**关键点：**
1. ✅ 推文生成是高并发的（20+并发）
2. ❌ 单个人设生成的7个阶段必须顺序执行（有依赖关系）
3. ✅ 多个人设可以同时生成（批量模式）
4. ✅ 图片生成支持多GPU并发（8个GPU可并发生成8张）

**推荐工作流：**
```bash
# 1. 批量生成人设（可以开多个终端并行）
# 2. 批量生成推文（使用高并发模式 --max-concurrent 20）
# 3. 批量生成图片（使用多GPU --num-gpus 8）
```
