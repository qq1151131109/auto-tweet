# 独立高并发推文生成器

**完全解耦于 ComfyUI 的独立程序，直接调用 LLM API 生成推文**

## ✨ 特性

- ✅ **完全独立**: 不依赖 ComfyUI 运行，可单独部署
- ⚡ **超高并发**: 推文生成 20+并发、人设 Stage 4-7 并发、批量人设并发、多GPU 图片生成
- ✅ **零改动**: 完全保留你调好的 Prompt 和生成逻辑
- ✅ **纯 Python**: 简单直接，易于调试和扩展

## 📦 安装依赖

```bash
cd auto-tweet-generator

# 安装基础依赖
pip install -r requirements.txt

# ⭐ 如果需要使用图片生成功能，确保 Z-Image 已配置
# Z-Image 依赖已包含在 requirements.txt 中
```

## 🖼️ 配置 Z-Image（图片生成）

如果需要使用图片生成功能，需要下载 Z-Image-Turbo 模型：

```bash
# 1. 下载模型（约30GB，需要几分钟）
python download_zimage_model.py

# 香港服务器可以不使用镜像：
python download_zimage_model.py

# 国内服务器可以使用镜像加速：
python download_zimage_model.py --use-mirror

# 2. 测试环境配置
python test_zimage.py --skip-model-loading

# 3. 快速测试（生成一张图片）
python quick_test_zimage.py
```

**硬件要求：**
- GPU: NVIDIA GPU with 16GB+ VRAM（推荐 RTX 4090）
- 磁盘: 约 35GB 空间用于模型存储
- 多GPU: 自动检测并使用所有可用GPU进行并发生成

## ⚙️ 配置密钥

**推荐方式：使用 .env 文件（安全、方便）**

```bash
# 1. 复制示例文件
cp .env.example .env

# 2. 编辑 .env 文件，填入你的密钥
# 主要配置：
#   - API_KEY：LLM API 密钥（必填）
#   - API_BASE：API 地址
#   - MODEL：模型名称
#   - WEATHER_API_KEY：天气 API 密钥（可选）
#   - MAX_CONCURRENT：最大并发数
#   - TEMPERATURE：温度参数
```

配置好 `.env` 后，运行命令时不需要再传 `--api-key` 等参数，程序会自动从 `.env` 读取。

**备选方式：命令行参数**

如果不想使用 `.env` 文件，也可以直接在命令行传递参数（见下方示例）。

## 🚀 快速开始

### 0. 人设生成（支持批量并发）

**单个人设生成：**
```bash
python main.py \
  --generate-persona \
  --image character.png \
  --persona-output personas/character.json
```

**⚡ 批量人设生成（并发）：**
```bash
# 同时生成多个人设（Stage 4-7 也会并发执行）
python main.py \
  --generate-persona \
  --images img1.png img2.png img3.png img4.png img5.png
```

**性能提升：**
- 单个人设：从 2.5分钟 → 1.5分钟（Stage 4-7 并发）⚡
- 5个人设：从 12.5分钟 → 3-4分钟（批量并发）🚀

### 1. 单个人设生成推文

**使用 .env 文件（推荐）：**

```bash
# 配置好 .env 后，命令简洁多了！
python main.py \
  --persona ../ComfyUI/custom_nodes/comfyui-twitterchat/personas/lila_monroe.json \
  --calendar ../ComfyUI/custom_nodes/comfyui-twitterchat/calendars/lila_monroe_2025-12.json \
  --tweets 5
```

**不使用 .env 文件（手动传参）：**

```bash
python main.py \
  --persona ../ComfyUI/custom_nodes/comfyui-twitterchat/personas/lila_monroe.json \
  --calendar ../ComfyUI/custom_nodes/comfyui-twitterchat/calendars/lila_monroe_2025-12.json \
  --tweets 5 \
  --api-key "your-api-key" \
  --api-base "https://www.dmxapi.cn/v1" \
  --model "grok-4.1-non-thinking"
```

### 2. 批量生成（高并发）

```bash
# 使用 .env 后，批量命令也更简洁
python main.py \
  --batch-mode \
  --personas ../ComfyUI/custom_nodes/comfyui-twitterchat/personas/*.json \
  --calendars ../ComfyUI/custom_nodes/comfyui-twitterchat/calendars/*.json \
  --tweets 10
```

### 3. 超大批量（100个人设）

```bash
# 准备文件列表
COMFYUI_DIR="../ComfyUI/custom_nodes/comfyui-twitterchat"
find $COMFYUI_DIR/personas -name "*.json" > personas.txt
find $COMFYUI_DIR/calendars -name "*.json" > calendars.txt

# 批量生成
python main.py \
  --batch-mode \
  --personas $(cat personas.txt) \
  --calendars $(cat calendars.txt) \
  --tweets 5 \
  --api-key "your-api-key" \
  --max-concurrent 50 \
  --output-dir output_batch_$(date +%Y%m%d)
```

## 📊 性能对比

| 场景 | ComfyUI单实例 | 独立程序(并发20) | 独立程序(并发50) |
|------|--------------|-----------------|-----------------|
| 10个人设×5推文 | ~400秒 | **~80秒** | **~40秒** |
| 100个人设×5推文 | ~4000秒 | **~800秒** | **~400秒** |

## 📁 文件结构

```
auto-tweet-generator/
├── main.py                 # 主程序入口
├── core/
│   └── tweet_generator.py  # 核心推文生成逻辑
├── utils/
│   └── llm_client.py       # LLM 异步客户端
├── prompts/                # 从原项目复制的 prompts
└── README.md               # 本文件
```

## ⚙️ 配置参数

```bash
python main.py --help
```

**核心参数:**
- `--persona`: 人设JSON文件路径
- `--calendar`: 日历JSON文件路径
- `--tweets`: 每个人设生成的推文数（默认5）
- `--api-key`: LLM API密钥
- `--max-concurrent`: 最大并发数（默认20）

**批量模式:**
- `--batch-mode`: 开启批量模式
- `--personas`: 多个人设文件路径（空格分隔）
- `--calendars`: 多个日历文件路径（空格分隔）

## 🔍 输入文件格式

### 人设文件 (persona.json)

```json
{
  "spec": "chara_card_v2",
  "spec_version": "2.0",
  "data": {
    "name": "Lila Monroe",
    "system_prompt": "...",
    "twitter_persona": {
      "tweet_examples": [
        {
          "text": "example tweet",
          "scene_hint": "scene description",
          "mood": "playful"
        }
      ]
    }
  }
}
```

### 日历文件 (calendar.json)

```json
{
  "persona_name": "Lila Monroe",
  "month": "2025-12",
  "calendar": {
    "2025-12-07": {
      "topic_type": "whispered_domination",
      "recommended_time": "evening_prime",
      "theme": "...",
      "content_direction": "..."
    }
  }
}
```

## 📤 输出格式

生成的推文保存为JSON文件：

```json
{
  "version": "1.0",
  "generated_at": "2025-12-07T10:30:00",
  "persona": {
    "name": "Lila Monroe"
  },
  "tweets": [
    {
      "slot": 1,
      "topic_type": "whispered_domination",
      "tweet_text": "...",
      "image_generation": {
        "scene_hint": "...",
        "positive_prompt": "..."
      }
    }
  ]
}
```

## 🎯 使用场景

### 场景1: 开发调试
```bash
# 快速测试单个人设
python main.py \
  --persona test_persona.json \
  --calendar test_calendar.json \
  --tweets 3 \
  --api-key "xxx"
```

### 场景2: 批量生产
```bash
# 生成一周的内容（7天×10推文）
python main.py \
  --persona lila.json \
  --calendar lila_weekly.json \
  --tweets 70 \
  --api-key "xxx" \
  --max-concurrent 30
```

### 场景3: 多账号管理
```bash
# 同时为100个账号生成推文
python main.py \
  --batch-mode \
  --personas personas/*.json \
  --calendars calendars/*.json \
  --tweets 5 \
  --max-concurrent 50 \
  --output-dir output_$(date +%Y%m%d)
```

## 🛠️ 高级用法

### 自定义LLM端点

```bash
# 使用本地 LLM
python main.py \
  --api-base "http://localhost:1234/v1" \
  --model "llama-3" \
  --api-key "not-needed"
```

### 调整温度参数

```bash
# 更随机的输出
python main.py \
  --temperature 1.5 \
  ...

# 更确定性的输出
python main.py \
  --temperature 0.7 \
  ...
```

### 监控日志

```bash
# 实时查看日志
python main.py ... 2>&1 | tee generation.log
```

## 🔧 扩展开发

### 添加新的生成器

```python
# core/my_generator.py
class MyGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client

    async def generate(self, ...):
        # 你的逻辑
        pass
```

### 自定义输出格式

```python
# 修改 main.py 中的保存逻辑
output_file = self.output_dir / f"custom_{persona_name}.txt"
with open(output_file, 'w') as f:
    for tweet in tweets_batch['tweets']:
        f.write(f"{tweet['tweet_text']}\n\n")
```

## 📈 性能调优

### 1. 调整并发数

```bash
# CPU密集型任务
--max-concurrent 10

# IO密集型任务（LLM API）
--max-concurrent 50
```

### 2. 批量大小

```bash
# 小批量测试
--tweets 3

# 生产环境
--tweets 20
```

### 3. API限流

如果遇到API限流，降低并发数：

```bash
--max-concurrent 5
```

## ❓ 常见问题

**Q: 和 ComfyUI 版本有什么区别？**
A: 完全相同的 Prompt 和生成逻辑，只是去掉了 ComfyUI 依赖，改用直接 API 调用。

**Q: 能不能用其他 LLM？**
A: 可以！只要兼容 OpenAI API 格式的都支持（OpenAI, Claude, 本地模型等）。

**Q: 如何处理失败的任务？**
A: 程序会自动跳过失败的任务，继续执行其他任务，并在最后汇总报告。

**Q: 输出文件如何导入ComfyUI？**
A: 生成的 JSON 格式完全兼容 ComfyUI 的 TweetBatchLoader 节点。

## 📞 支持

如有问题，查看日志输出或检查：
1. API密钥是否正确
2. 网络连接是否正常
3. 输入文件格式是否正确
4. 并发数是否过高导致限流
