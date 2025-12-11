# 真实感图片生成方案 - LLM灵活注入

**最后更新**: 2025-12-10
**版本**: v2.0 (LLM灵活注入)

---

## 🎯 核心方案

真实感词汇通过 **LLM灵活添加** 而非代码死规则。

### 工作原理

```
步骤1: LLM收到增强的system prompt
  ├─ 包含真实感词汇指导
  ├─ 提供分类词汇列表
  ├─ 给出使用场景规则
  └─ 展示正反例

步骤2: LLM生成scene_hint
  ├─ 理解场景语义
  ├─ 选择合适的真实感词汇
  └─ 自然地添加到描述末尾

步骤3: 代码层直接使用
  └─ positive_prompt = scene_hint (不再做额外处理)
```

---

## 📝 LLM指导内容

### System Prompt添加的指导

**位置**: `core/tweet_generator.py` 的 `_build_system_prompt()` 方法

```python
### 4.5. CRITICAL: Realistic Photography Style

🎯 **Goal**: Make images look like authentic phone photos, NOT AI-generated perfect renders.

**ALWAYS include 2-4 realistic modifiers at the END of your scene description**:

**Core Authenticity** (choose 2):
- "Raw photo" - unedited, straight from camera
- "candid photography" - natural, unposed moment
- "authentic snapshot" - real moment captured
- "smartphone camera aesthetic" - phone camera quality
- "shot on iPhone" - casual phone photography

**Natural Imperfections** (choose 1-2 based on scene):
- "messy background" - cluttered, real environment (outdoor/public places)
- "uneven skin tone" - natural skin texture, not airbrushed
- "Chromatic aberration" - lens color fringing
- "motion blur" - subject moving (ONLY if movement in scene)
- "slightly out of focus" - not perfectly sharp (use sparingly)

**Lighting Variations** (choose 1 if applicable):
- "low lighting" - dim/night scenes
- "overexposed" - very bright/sunny scenes (use sparingly)
- "underexposed" - shadowy/dim areas (use sparingly)

**Camera Effects** (optional, choose 0-1):
- "in motion" - capturing movement
- "GoPro lens" - wide angle distortion
- "amateur photography" - not professionally shot

**Atmospheric** (optional, rare):
- "eerie atmosphere" - mysterious/creepy scenes only

**Format**: Add these modifiers as a natural continuation at the end:
"[main scene description], Raw photo, candid photography, messy background, uneven skin tone"

**Scene Type Guidance**:
- Night/dark scenes → always include "low lighting"
- Outdoor/public → always include "messy background"
- Moving subject → include "motion blur" and "in motion"
- Bright/sunny → optionally include "overexposed" (20% of time)
- Indoor shadows → optionally include "underexposed" (20% of time)
```

---

## 🎨 示例输出

### 示例1: 夜间卧室场景

**LLM生成的scene_hint**:
```
Late evening bedroom, woman kneeling on carpet wearing oversized t-shirt
and black panties, dim purple LED light from behind bed, messy hair
falling over shoulders, vulnerable expression with soft puppy eyes,
close-up shot focusing on upper body, Raw photo, smartphone camera
aesthetic, low lighting, uneven skin tone
```

**分析**:
- ✅ 包含4个真实感词汇
- ✅ 选择了 Core Authenticity: "Raw photo", "smartphone camera aesthetic"
- ✅ 选择了 Lighting: "low lighting" (夜间场景)
- ✅ 选择了 Imperfections: "uneven skin tone"

### 示例2: 户外咖啡厅

**LLM生成的scene_hint**:
```
Afternoon at outdoor cafe on busy street, woman sitting at table with
coffee cup, bright sunlight streaming through windows, casual sundress,
people visible in blurred background, relaxed expression, medium shot
from across table, candid photography, messy background, Chromatic
aberration, slightly overexposed
```

**分析**:
- ✅ 包含4个真实感词汇
- ✅ 选择了 Core Authenticity: "candid photography"
- ✅ 选择了 Imperfections: "messy background" (户外场景)
- ✅ 选择了 Imperfections: "Chromatic aberration"
- ✅ 选择了 Lighting: "overexposed" (明亮场景)

### 示例3: 运动场景

**LLM生成的scene_hint**:
```
Woman walking quickly through hallway, motion in frame, casual clothes
with hair moving, natural indoor lighting from ceiling lights, determined
expression, full body shot from front, authentic snapshot, motion blur,
in motion, amateur photography
```

**分析**:
- ✅ 包含4个真实感词汇
- ✅ 选择了 Core Authenticity: "authentic snapshot", "amateur photography"
- ✅ 选择了 Imperfections: "motion blur" (运动场景)
- ✅ 选择了 Camera Effects: "in motion" (运动场景)

---

## 🆚 对比：LLM vs 代码规则

### LLM灵活添加（当前方案）✅

**优点**:
- ✅ **语义理解**: LLM理解场景整体语境
- ✅ **灵活智能**: 能处理复杂场景（如"night party with bright lights"）
- ✅ **自然融合**: 词汇添加更自然，不突兀
- ✅ **易于调整**: 修改prompt即可，无需改代码
- ✅ **可扩展**: 添加新词汇只需更新prompt

**注意事项**:
- ⚠️ **稳定性**: LLM可能不总是遵循指导（需要好的prompt设计）
- ⚠️ **一致性**: 需要明确的指导确保一致性

### 代码死规则（旧方案）❌

**优点**:
- ✅ 完全可控
- ✅ 绝对稳定

**缺点**:
- ❌ 不够灵活
- ❌ 简单关键词匹配可能误判
- ❌ 难以处理复杂语境
- ❌ 维护成本高（需要改代码）

---

## 🔧 代码实现

### 1. System Prompt（指导LLM）

**位置**: `core/tweet_generator.py:157-227`

添加了详细的真实感词汇指导，包括:
- 词汇分类列表
- 使用场景规则
- 正反例对比
- 格式要求

### 2. 解析响应（直接使用）

**位置**: `core/tweet_generator.py:423-497`

```python
def _parse_response(self, response: str, calendar_plan: Dict, persona: Dict) -> Dict:
    # 提取LLM生成的scene_hint
    scene_hint = "..."  # 已包含真实感词汇

    # ⭐ 直接使用，不做额外处理
    positive_prompt = scene_hint

    # 使用增强的negative prompt
    negative_prompt = (
        "ugly, deformed, noisy, blurry, low quality, "
        "artificial lighting, oversaturated, "
        "perfect studio lighting, airbrushed skin, "
        "CGI, 3d render, anime, "
        "perfect, flawless, professional photoshoot"
    )

    return {
        "image_generation": {
            "scene_hint": scene_hint,
            "positive_prompt": positive_prompt,  # = scene_hint
            "negative_prompt": negative_prompt
        }
    }
```

---

## 🧪 验证方法

### 1. 运行测试脚本

```bash
python test_llm_realism.py
```

验证:
- ✅ Scene hint格式是否正确
- ✅ 是否包含2-4个真实感词汇
- ✅ 词汇选择是否符合场景

### 2. 实际生成测试

```bash
# 生成5条推文
python main.py --persona personas/test.json --tweets 5

# 检查输出JSON
cat output_standalone/test_*.json | grep "scene_hint"
```

检查:
- scene_hint是否包含真实感词汇
- 词汇是否符合场景类型
- 数量是否在2-4个范围

### 3. 图片生成测试

```bash
# 生成图片
python main.py --generate-images --tweets-batch output_standalone/test_*.json

# 查看图片效果
ls output_images/
```

验证:
- 图片是否有手机拍摄感
- 是否降低了AI感
- 真实感词汇是否生效

---

## 📊 效果预期

### 降低AI感

**指标**:
- ✅ 肤色更自然（略微不均匀）
- ✅ 背景更真实（适度凌乱）
- ✅ 光照更自然（可能略微过曝/欠曝）
- ✅ 整体更接近手机拍摄效果

### 提升灵活性

**优势**:
- ✅ LLM理解场景语义，选择更合适
- ✅ 能处理复杂场景（如夜间派对但有明亮灯光）
- ✅ 自然融合，不会产生突兀的词汇组合

---

## 🎓 最佳实践

### 1. Prompt设计原则

- **明确指令**: "ALWAYS include 2-4 realistic modifiers"
- **提供列表**: 给出所有可用词汇
- **场景规则**: 明确什么场景用什么词
- **正反例**: 展示好的和坏的示例

### 2. 词汇选择建议

**必选** (Core Authenticity, 2个):
- Raw photo
- candid photography
- authentic snapshot

**场景相关** (Imperfections, 1-2个):
- 户外 → messy background
- 所有 → uneven skin tone
- 所有 → Chromatic aberration
- 运动 → motion blur

**光照相关** (Lighting, 0-1个):
- 夜间 → low lighting
- 明亮 → overexposed (谨慎)
- 阴影 → underexposed (谨慎)

### 3. 质量控制

**检查LLM输出**:
```python
# 验证scene_hint包含真实感词汇
realism_keywords = ["Raw photo", "candid", "authentic", ...]
count = sum(1 for kw in realism_keywords if kw in scene_hint)

if count < 2:
    print("⚠️ 真实感词汇不足，LLM可能未遵循指导")
```

---

## 🚀 迁移指南

### 从PromptEnhancer（代码规则）迁移

**旧方案** (v1.0):
```python
# 代码层添加真实感词汇
enhancer = create_prompt_enhancer("z-image", "medium")
result = enhancer.enhance(scene_hint)
positive_prompt = result["positive_prompt"]
```

**新方案** (v2.0):
```python
# LLM已经添加，直接使用
positive_prompt = scene_hint
```

**优势**:
- ✅ 更简单（去掉了PromptEnhancer调用）
- ✅ 更灵活（LLM理解语义）
- ✅ 更自然（词汇融入描述）

**注意**:
- ⚠️ PromptEnhancer代码仍保留在 `core/prompt_enhancer.py`
- ⚠️ 可以作为备用方案或用于其他用途
- ⚠️ 配置文件 `config/image_generation.yaml` 仍然有效（控制生成参数）

---

## 📝 常见问题

### Q1: LLM不遵循指导怎么办？

**检查**:
1. System prompt是否正确添加
2. 指令是否够明确（"ALWAYS", "CRITICAL"）
3. 是否提供了清晰的正反例

**解决**:
- 强化指令措辞（MUST, ALWAYS, CRITICAL）
- 增加更多正反例
- 调整temperature（降低可提高一致性）

### Q2: 词汇添加太多或太少？

**调整prompt**:
```python
# 原来: "ALWAYS include 2-4 realistic modifiers"
# 改为: "ALWAYS include EXACTLY 3 realistic modifiers"
```

### Q3: 如何回退到代码规则？

**方案1**: 使用PromptEnhancer
```python
# 在 _parse_response() 中重新启用
from core.prompt_enhancer import create_prompt_enhancer

enhancer = create_prompt_enhancer("z-image", "medium")
result = enhancer.enhance(scene_hint)
positive_prompt = result["positive_prompt"]
```

**方案2**: 移除System Prompt中的真实感指导

### Q4: 如何添加新的真实感词汇？

只需修改System Prompt:
```python
# 在 _build_system_prompt() 中添加
**New Category** (optional):
- "your new keyword" - description
```

---

## 📚 相关文件

- `core/tweet_generator.py:157-227` - 真实感指导prompt
- `core/tweet_generator.py:423-497` - 解析和使用
- `test_llm_realism.py` - 验证测试脚本
- `config/image_generation.yaml` - 生成参数配置（仍然有效）

---

**结论**: LLM灵活注入方案更智能、更灵活，是推荐的生产方案。PromptEnhancer代码规则作为备用保留。
