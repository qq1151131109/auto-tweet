# 优化效果测试报告
**日期**: 2025-12-11
**测试人设**: Valeria "Val" Ortiz (hollyjai.jpg)

---

## 🎯 优化目标

### 1. 增加 iPhone 镜子自拍场景
- **目标**: 20-30% 的内容应该是镜子自拍（iPhone 手机拍摄）
- **原因**: 镜子自拍流量更高，engagement 更好

### 2. 强化真实感修饰词
- **目标**: 每条 scene_hint 包含 3-4 个真实感修饰词
- **重点词汇**:
  - `authentic snapshot` - 真实抓拍
  - `motion blur` - 运动模糊
  - `messy background` - 凌乱背景
- **原因**: 让图片看起来像手机实拍，而不是完美的 AI 生成图

---

## 📝 优化内容

### 修改 1: `core/persona_generator.py` (Stage 2: Tweet Strategy)

**位置**: 第 232-239 行

**新增内容**:
```python
CRITICAL GUIDELINES:
1. Content types must be SPECIFIC to this persona, not generic
2. **IMPORTANT**: Mirror selfies (especially iPhone selfies in bathroom/bedroom) 
   perform extremely well and should be heavily weighted (20-30%)
3. Include variations like:
   - "bathroom_mirror_selfie" or "bedroom_mirror_selfie" - showing off outfit/body
   - "gym_mirror_selfie" - post-workout physique shots
   - "fitting_room_selfie" - trying on clothes
4. Mirror selfies are versatile and work for almost any persona
```

### 修改 2: `core/tweet_generator.py` (Section 4.5: Realistic Photography Style)

**位置**: 第 331-393 行

**主要改动**:
1. **"messy background" 使用率提升**:
   - 之前: 仅户外使用
   - 现在: **70% 的室内场景也使用**

2. **"motion blur" 使用更频繁**:
   - 之前: 仅明显运动
   - 现在: **40% 的场景使用（轻微动作也算）**

3. **"authentic snapshot" 优先级提高**:
   - 标记为 `[USE FREQUENTLY]`
   - 镜子自拍**必须包含**

4. **光照瑕疵词使用增加**:
   - "overexposed": 20% → **60%** (明亮场景)
   - "underexposed": 20% → **40%** (室内阴影)

5. **默认修饰词数量增加**:
   - 之前: 2-4 个
   - 现在: **目标 3-4 个，不是 2 个**

---

## ✅ 测试结果

### 优化 1: 镜子自拍场景 ✅ 成功

**数据**:
- 总示例推文: 8 条
- 镜子自拍相关: **3 条 (37.5%)**

**分布**:
- 🪞 `gym_mirror_selfie`: 2 (25.0%)
- 🪞 `bathroom_bedroom_mirror_selfie`: 1 (12.5%)
- `2am_close_friends_spill`: 1 (12.5%)
- `club_bathroom_twerk_vids`: 1 (12.5%)
- `fitting_room_tryon_hauls`: 1 (12.5%)
- `ocean_drive_walking_clips`: 1 (12.5%)
- `post_delete_regret_reels`: 1 (12.5%)

**结论**:
✅ **镜子自拍占比 37.5%，超过目标 20-30%，优化成功！**

---

### 优化 2: 真实感修饰词 ⏸️ 待验证

**说明**:
- 人设生成阶段的示例推文 (Stage 3) 使用的是**旧版提示词**
- 真实感词优化在 `core/tweet_generator.py` 中
- **实际推文生成时**（`--persona xxx --tweets 10`）才会应用新提示词

**预期效果**:
- 每条 scene_hint 将包含 3-4 个真实感词
- `messy background` 出现在 70% 的场景中
- `motion blur` 出现在 40% 的场景中
- `authentic snapshot` 在镜子自拍中 100% 出现

**验证方法**:
```bash
python main.py --persona personas/test_optimized.json \\
  --calendar calendars/xxx.json --tweets 10
```
然后分析生成的推文中 `scene_hint` 的真实感词数量。

---

## 📊 对比总结

| 优化项目 | 之前 | 现在 | 状态 |
|---------|------|------|------|
| 镜子自拍占比 | ~15% (推测) | **37.5%** | ✅ 成功 |
| 真实感词数量 | 2 个/推文 | **3-4 个/推文 (预期)** | ⏸️ 待验证 |
| `messy background` 使用率 | 仅户外 | **70% (室内+户外)** | ⏸️ 待验证 |
| `motion blur` 使用率 | 仅明显运动 | **40% 所有场景** | ⏸️ 待验证 |

---

## 🎯 下一步建议

### 1. 完整测试真实感词效果
生成实际推文batch，验证真实感词是否按预期添加：
```bash
# 先生成一个完整的calendar
python main.py --persona personas/test_optimized.json --generate-calendar

# 然后生成推文
python main.py --persona personas/test_optimized.json \\
  --calendar calendars/Valeria_calendar.json --tweets 14

# 分析结果
python analyze_realism_words.py output_standalone/Valeria_*.json
```

### 2. A/B 测试
- 对比新旧人设生成的图片
- 统计 engagement 数据
- 验证真实感提升是否带来更高的互动率

### 3. 微调建议
如果真实感词过多导致图片质量下降：
- 调整使用率：70% → 50%
- 减少同时使用的修饰词数量：3-4 → 2-3

---

## 📁 生成的测试文件

- **人设**: `personas/test_optimized.json`
- **Calendar**: `calendars/test_calendar.json`
- **日志**: `test_optimization.log`
- **本报告**: `OPTIMIZATION_TEST_REPORT.md`

---

**测试完成时间**: 2025-12-11 06:47
**优化版本**: v1.0 (镜子自拍 + 真实感词强化)
