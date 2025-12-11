# 配置管理使用指南

## 📚 概述

本项目现在使用**分层配置系统**，将所有配置参数统一管理：

- **基础设施配置** → `.env` + `config.py` (Settings)
- **生成流程配置** → `generation_config.yaml/json` + `config_generation.py` (GenerationConfig)

## 🗂️ 配置文件结构

```
auto-tweet-generator/
├── .env                        # 环境变量（API密钥、基础设施配置）
├── config.py                   # 统一配置入口（BaseSettings）
├── config_generation.py        # 生成配置类定义（Pydantic模型）
├── generation_config.yaml      # 生成参数配置（推荐）✅
└── generation_config.json      # 生成参数配置（JSON格式）
```

---

## 🔧 配置方式对比

### 方式1: 使用 YAML 配置文件（推荐）✅

**优点**:
- 可读性强，支持注释
- 修改方便，无需重启代码
- 参数分组清晰

**使用方法**:
```bash
# 1. 复制示例配置
cp generation_config.yaml my_config.yaml

# 2. 编辑配置
vim my_config.yaml

# 3. 设置环境变量（可选）
export GENERATION_CONFIG_FILE=my_config.yaml

# 4. 运行程序（自动加载）
python main.py --persona xxx.json --tweets 10
```

### 方式2: 使用 JSON 配置文件

**优点**:
- 标准格式，易于程序解析
- 跨平台兼容性好

**使用方法**:
```bash
# 1. 编辑 generation_config.json
vim generation_config.json

# 2. 运行程序（自动从当前目录加载）
python main.py --persona xxx.json --tweets 10
```

### 方式3: 使用环境变量（仅基础设施配置）

**适用于**: API密钥、服务地址、并发控制等基础配置

**使用方法**:
```bash
# .env 文件
API_KEY=sk-xxxxx
MAX_CONCURRENT=20
TEMPERATURE=1.0
```

---

## 📖 配置参数说明

### 1. 人设生成配置 (persona)

#### 各阶段配置

| 阶段 | 参数路径 | 默认值 | 说明 |
|-----|---------|--------|------|
| Stage 1 | `persona.stage1_core_persona.temperature` | 0.85 | 核心人设生成温度 |
| Stage 1 | `persona.stage1_core_persona.max_tokens` | 4000 | 最大token数 |
| Stage 2 | `persona.stage2_tweet_strategy.temperature` | 0.85 | 推文策略温度 |
| Stage 2 | `persona.stage2_tweet_strategy.max_tokens` | 8000 | - |
| Stage 3 | `persona.stage3_example_tweets.temperature` | 0.9 | 示例推文温度（需要更高创造性） |
| Stage 3 | `persona.num_example_tweets` | 8 | 生成的示例推文数量 |
| Stage 4-7 | `persona.stage{N}_{name}.temperature` | 0.8-0.85 | 其他阶段温度 |

#### 通用配置

```yaml
persona:
  default_nsfw_level: "enabled"    # NSFW等级: enabled | disabled
  default_language: "English"      # 默认语言: English | 中文 | 日本語
```

---

### 2. 推文生成配置 (tweet)

```yaml
tweet:
  # LLM参数
  temperature: 1.0          # 生成温度（推文需要高创造性）
  max_tokens: 2000          # 单条推文最大token

  # Few-shot示例
  max_examples: 3           # 从人设中选择的示例数量（1-8）

  # 内容约束
  tweet_min_length: 140     # 推文最小字符数
  tweet_max_length: 280     # 推文最大字符数
  scene_min_words: 50       # 场景描述最小词数
  scene_max_words: 100      # 场景描述最大词数

  # 日历配置
  default_calendar_days: 15  # 默认生成日历天数
```

---

### 3. 图片生成配置 (image)

```yaml
image:
  # Z-Image模型参数
  default_width: 768         # 默认宽度（像素）
  default_height: 1024       # 默认高度（像素）
  default_steps: 9           # Z-Image-Turbo推荐步数
  default_cfg: 1.0           # CFG scale

  # LoRA参数
  default_lora_strength: 1.0 # LoRA强度（0.0-2.0）

  # 负向提示词
  negative_prompt: "ugly, deformed, noisy, blurry, low quality"

  # 多GPU配置
  task_queue_timeout: 1      # 任务队列超时（秒）
  result_queue_timeout: 300  # 结果队列超时（秒）- 5分钟
  process_join_timeout: 10   # 进程等待超时（秒）
```

---

## 💻 代码中使用配置

### 方式1: 使用全局配置实例（推荐）✅

```python
from config import generation_config

# 人设生成器中使用
class PersonaGenerator:
    async def _generate_core_persona(self, ...):
        response = await self.llm_client.chat_completion(
            messages=messages,
            temperature=generation_config.persona.stage1_core_persona.temperature,
            max_tokens=generation_config.persona.stage1_core_persona.max_tokens
        )
```

### 方式2: 动态加载配置

```python
from config import settings

# 在运行时加载自定义配置
gen_config = settings.load_generation_config()

# 使用配置
temperature = gen_config.tweet.temperature
max_tokens = gen_config.tweet.max_tokens
```

### 方式3: 从自定义文件加载

```python
from config_generation import load_generation_config

# 从指定文件加载
config = load_generation_config("custom_config.yaml")

# 访问配置
width = config.image.default_width
height = config.image.default_height
```

---

## 🔄 迁移现有代码

### Before（硬编码）❌

```python
# core/persona_generator.py
response = await self.llm_client.chat_completion(
    messages=messages,
    temperature=0.85,  # 硬编码
    max_tokens=4000    # 硬编码
)
```

### After（使用配置）✅

```python
# core/persona_generator.py
from config import generation_config

response = await self.llm_client.chat_completion(
    messages=messages,
    temperature=generation_config.persona.stage1_core_persona.temperature,
    max_tokens=generation_config.persona.stage1_core_persona.max_tokens
)
```

---

## 🎯 常见使用场景

### 场景1: 调整人设生成的创造性

修改 `generation_config.yaml`:
```yaml
persona:
  stage3_example_tweets:
    temperature: 1.2  # 从0.9提高到1.2，生成更有创意的示例推文
```

### 场景2: 修改图片分辨率

修改 `generation_config.yaml`:
```yaml
image:
  default_width: 1024   # 从768提高到1024
  default_height: 1536  # 从1024提高到1536
```

### 场景3: 调整推文长度限制

修改 `generation_config.yaml`:
```yaml
tweet:
  tweet_max_length: 350  # 从280扩展到350字符
```

### 场景4: 批量生成时使用自定义配置

```bash
# 方法1: 设置环境变量
export GENERATION_CONFIG_FILE=high_quality_config.yaml
python main.py --batch-mode --personas personas/*.json --tweets 20

# 方法2: 直接修改 generation_config.yaml
python main.py --batch-mode --personas personas/*.json --tweets 20
```

---

## 🛠️ 高级用法

### 1. 为不同流程创建不同配置

```bash
# 高质量配置（慢但质量高）
generation_config_high_quality.yaml
  persona.stage1.temperature: 0.7  # 更稳定
  image.default_steps: 20          # 更多步数

# 快速配置（快但质量较低）
generation_config_fast.yaml
  persona.stage1.temperature: 1.0  # 更随机
  image.default_steps: 5           # 更少步数

# 使用
export GENERATION_CONFIG_FILE=generation_config_fast.yaml
python main.py --persona xxx.json --tweets 100
```

### 2. 环境隔离

```bash
# 开发环境
.env.development
generation_config.development.yaml

# 生产环境
.env.production
generation_config.production.yaml

# 使用
export ENV=production
export GENERATION_CONFIG_FILE=generation_config.$ENV.yaml
```

### 3. 程序化修改配置

```python
from config import generation_config

# 运行时修改配置
generation_config.tweet.temperature = 1.5
generation_config.image.default_steps = 15

# 使用修改后的配置
generator = TweetGenerator(...)
```

---

## ⚠️ 注意事项

### 1. 配置加载优先级

```
1. GENERATION_CONFIG_FILE 环境变量指定的文件
2. 当前目录的 generation_config.yaml
3. 当前目录的 generation_config.json
4. 默认硬编码值（fallback）
```

### 2. 参数验证

所有配置都通过 Pydantic 验证：
```python
# 无效配置会抛出异常
persona:
  stage1_core_persona:
    temperature: 5.0  # ❌ 超出范围 (0.0-2.0)
    max_tokens: -100  # ❌ 负数
```

### 3. 兼容性

- 现有代码在没有配置文件时仍使用默认值（向后兼容）
- 逐步迁移：可以先使用配置文件，旧代码继续使用硬编码

---

## 📝 配置文件模板

### 最小配置（只修改关键参数）

```yaml
# generation_config.minimal.yaml
tweet:
  temperature: 1.2  # 只修改推文生成温度

# 其他参数使用默认值
```

### 完整配置（覆盖所有默认值）

见 `generation_config.yaml`（已包含所有参数和注释）

---

## 🔍 调试配置

```python
# 查看当前加载的配置
from config import generation_config
import json

print(json.dumps(generation_config.dict(), indent=2))
```

输出:
```json
{
  "persona": {
    "stage1_core_persona": {
      "temperature": 0.85,
      "max_tokens": 4000
    },
    ...
  },
  "tweet": {...},
  "image": {...}
}
```

---

## 📚 相关文件

- `config.py` - 主配置入口
- `config_generation.py` - 生成配置类定义
- `generation_config.yaml` - YAML格式配置（推荐）
- `generation_config.json` - JSON格式配置
- `.env` - 环境变量（基础设施配置）

---

## 🆘 常见问题

### Q1: 配置文件不生效？

检查加载优先级：
```bash
# 查看是否设置了环境变量
echo $GENERATION_CONFIG_FILE

# 检查文件是否存在
ls -la generation_config.yaml
```

### Q2: 如何知道配置是否被正确加载？

在代码中添加日志：
```python
from config import generation_config
print(f"Loaded config: {generation_config.persona.stage1_core_persona.temperature}")
```

### Q3: 可以混合使用环境变量和配置文件吗？

可以：
- 基础设施配置（API密钥、并发数）→ `.env`
- 生成流程配置（温度、步数、分辨率）→ `generation_config.yaml`

---

## 🚀 下一步

1. **复制配置文件**: `cp generation_config.yaml my_config.yaml`
2. **修改参数**: 根据需求调整
3. **测试**: 运行小批量任务验证配置
4. **应用到生产**: 批量生成时使用经过验证的配置

---

**需要帮助？** 查看项目文档或提交 Issue。
