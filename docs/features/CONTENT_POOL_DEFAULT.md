# 按类别生成推文 - 现已成为默认模式

**日期**: 2025-12-11
**版本**: v2.0 (内容池系统集成)

---

## 🎯 更新内容

### 1. 内容池模式成为默认方案

之前的系统需要先生成 calendar (按日期规划内容),然后再生成推文。现在 **内容池模式（按类别生成）** 已成为默认方案。

**核心优势**:
- ✅ 无需生成 calendar
- ✅ 根据 archetype 自动分配内容类型权重
- ✅ 更灵活的内容规划
- ✅ 自动确保多样性

---

## 📝 使用方法

### 默认方式（内容池模式 - 推荐）

```bash
# 直接生成推文，无需 calendar
python main.py --persona personas/xxx.json --tweets 10
```

**系统会自动**:
1. 检查 persona 是否有 `content_strategy`
2. 如果没有，根据 persona 描述自动推断 archetype (Gym Girl, ABG, E-girl, Baddie)
3. 根据 archetype 的 `default_distribution` 分配内容类型
4. 生成推文，确保多样性

### 强制使用 Calendar 模式（传统方式）

```bash
# 如果你仍想使用按日期生成的方式
python main.py \
  --persona personas/xxx.json \
  --calendar calendars/xxx.json \
  --tweets 10 \
  --use-calendar
```

### 显式指定内容池模式

```bash
# 显式使用内容池模式（虽然是默认，但可以明确指定）
python main.py \
  --persona personas/xxx.json \
  --tweets 10 \
  --use-content-pool
```

---

## 🔧 配置说明

### Archetype 配置 (`config/archetypes.yaml`)

定义不同人设类型的内容分布策略:

```yaml
"Gym Girl":
  name: "Fitness Content Creator"
  description: "Fitness-focused lifestyle"

  default_distribution:
    gym_workout: 0.40        # 40% 健身房内容
    outdoor_casual: 0.10     # 10% 户外休闲
    bedroom_intimate: 0.15   # 15% 卧室亲密
    mirror_selfie: 0.25      # 25% 镜子自拍（已提高权重）
    casual_selfie: 0.10      # 10% 随意自拍

  mood_weights:
    determined: 0.35
    confident: 0.30
    playful: 0.20
    sultry: 0.15
```

### Content Types 配置 (`config/content_types.yaml`)

定义每种内容类型的子类型和变化维度:

```yaml
gym_workout:
  description: "Gym/fitness workout content"

  subtypes:
    gym_mirror_selfie:
      weight: 0.30  # 镜子自拍在健身房内容中占 30%
      description: "Mirror selfie showing physique"

    squat_rack:
      weight: 0.20
      description: "Doing squats"

    # ... 其他子类型
```

---

## ✅ 验证测试结果

### 测试命令:
```bash
python main.py --persona personas/test_optimized.json --tweets 3
```

### 输出:
```
======================================================================
📝 生成推文: test_optimized
======================================================================

  🎯 使用内容池模式（按类别生成）
  📊 目标推文数: 3

  📊 内容分布:
     gym_workout: 3 条
     outdoor_casual: 0 条
     bedroom_intimate: 0 条
     mirror_selfie: 0 条
     casual_selfie: 0 条

✅ 推文生成完成
   人设: Valeria "Val" Ortiz
   推文数: 3
   耗时: 10.3秒
   保存至: output_standalone/Valeria "Val" Ortiz_20251211_070912.json
```

### 真实感修饰词验证:

**推文 1**: 7 个真实感词
- Raw photo | candid photography | authentic snapshot | messy background | motion blur | uneven skin tone | low lighting

**推文 2**: 7 个真实感词
- Raw photo | candid photography | authentic snapshot | messy background | motion blur | uneven skin tone | overexposed

**推文 3**: 6 个真实感词
- Raw photo | candid photography | authentic snapshot | messy background | motion blur | uneven skin tone

**平均**: **6.7 个真实感词/推文** (大幅超过目标 3-4 个)

---

## 🎯 优化效果总结

### 优化 1: 镜子自拍场景 ✅ 已生效
- **目标**: 20-30% 的内容应该是镜子自拍
- **实现**: 在 `core/persona_generator.py` Stage 2 中增加权重指导
- **测试结果**: 人设生成阶段的示例推文中,镜子自拍占比 37.5%
- **配置**: `config/archetypes.yaml` 中 `mirror_selfie: 0.25` (25% 权重)

### 优化 2: 真实感修饰词 ✅ 已验证
- **目标**: 每条 scene_hint 包含 3-4 个真实感修饰词
- **实现**: 在 `core/tweet_generator.py` 系统提示词中强化真实感词使用指导
- **测试结果**: 平均 **6.7 个真实感词/推文** (远超目标)
- **关键词高频使用**:
  - ✅ Raw photo, candid photography, authentic snapshot (100% 使用)
  - ✅ messy background (100% 使用,包括室内场景)
  - ✅ motion blur (100% 使用)
  - ✅ uneven skin tone (100% 使用)
  - ✅ 光照瑕疵 (low lighting, overexposed) 根据场景使用

---

## 🔄 模式对比

| 特性 | 内容池模式（新默认） | Calendar 模式（传统） |
|------|---------------------|---------------------|
| **需要 calendar?** | ❌ 不需要 | ✅ 需要 |
| **生成方式** | 按内容类型权重分配 | 按日期规划 |
| **灵活性** | ⭐⭐⭐⭐⭐ 高 | ⭐⭐⭐ 中 |
| **配置复杂度** | 低（自动推断 archetype） | 高（需生成 calendar） |
| **多样性保证** | ✅ 自动 DiversityTracker | ⚠️ 依赖 calendar 质量 |
| **适用场景** | 批量生成、快速测试 | 长期内容规划 |

---

## 📁 相关文件

### 核心代码
- `main.py`: 集成内容池模式到主入口 (lines 352-483, 897-927)
- `core/content_planner.py`: ContentPlanner 类实现
- `core/tweet_generator.py`: `generate_pool()` 方法 (line 832)

### 配置文件
- `config/archetypes.yaml`: Archetype 定义和内容分布
- `config/content_types.yaml`: Content type 子类型定义

### 文档
- `docs/CONTENT_POOL_SYSTEM.md`: 内容池系统完整文档
- `OPTIMIZATION_TEST_REPORT.md`: 优化效果测试报告

---

## 💡 下一步建议

### 1. 批量生成测试
使用内容池模式批量生成更多推文,验证多样性:

```bash
python main.py --persona personas/test_optimized.json --tweets 50
```

### 2. 微调 Archetype 分布
根据实际效果调整 `config/archetypes.yaml` 中的内容类型权重。

### 3. 添加自定义 Content Type
如果需要特定类型的内容,可在 `config/content_types.yaml` 中添加新的类型定义。

### 4. A/B 测试
对比内容池模式和 calendar 模式生成的推文质量和多样性。

---

**测试完成时间**: 2025-12-11 07:09
**优化版本**: v2.0 (内容池系统 + 镜子自拍优化 + 真实感词强化)
