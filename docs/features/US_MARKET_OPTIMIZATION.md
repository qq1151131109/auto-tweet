# 美国市场审美优化指南

**最后更新**: 2025-12-10
**版本**: v1.0

---

## 🎯 核心目标

将系统从**东亚审美**转向**美国市场审美**,提升在美国社交媒体平台的内容吸引力。

### 核心差异

| 维度 | 东亚审美 (China) | 美国审美 (US) |
|------|----------------|--------------|
| **关键词** | 白瘦幼、纯欲、清纯 | Curvy、自信、Baddie、野性 |
| **身材** | 极致纤细、A4腰、筷子腿 | Slim-thick (腰细臀宽腿粗)、健身感 |
| **肤色** | 冷白皮 | 小麦色/古铜色 (Sun-kissed/Tan) |
| **姿态** | 收缩、害羞、回避眼神 | 占据空间、直视镜头、自信 |
| **性格** | 依赖、温柔、被动 | 独立、主动、有攻击性 |

---

## 📝 System Prompt 优化

### 位置
`core/tweet_generator.py:171-271`

### 新增内容

在原有的 Scene Description 指导后,新增了 **4.3. CRITICAL: US Market Aesthetic Optimization** 章节,包含:

#### 1. 身体语言与姿态 (Body Language & Posing)

**必须做 (DO)**:
- ✅ **Direct eye contact** - 直视镜头建立寄社会关系
- ✅ **Arched back** - 骨盆前倾强调腰臀比
- ✅ **Legs apart stance** - 重心偏移,展示自信
- ✅ **Arms away from body** - 占据空间
- ✅ **Open chest** - 挺胸展示身材

**严格避免 (DON'T)**:
- ❌ Eye contact avoidance (眼神回避)
- ❌ Pigeon-toed stance (内八字)
- ❌ Hunched shoulders (耸肩)
- ❌ Covering face with hands (遮脸)
- ❌ Pouting lips (嘟嘴)

#### 2. 表情与眼神 (Facial Expression & Gaze)

**推荐表情**:
- "Bedroom eyes" - 眼睑微垂但聚焦
- Parted lips - 微张嘴露齿
- Smirk - 自信的坏笑
- Direct stare - 直视镜头

**避免幼态化表情**:
- 过度睁大的无辜眼神
- 遮嘴笑
- 咬手指等过度可爱动作

#### 3. 肤色与质感 (Skin Tone & Texture)

**推荐描述**:
- Warm/golden skin tone (暖色调)
- Sun-kissed (阳光吻过的)
- Glossy/dewy skin (光泽感/水润感)
- Natural texture visible (保留自然质感)

**严格避免**:
- Cold pale white skin (冷白皮)
- Porcelain doll skin (瓷娃娃般的)
- Overly smoothed (过度磨皮)

#### 4. 风格原型 (Styling Archetypes)

**ABG (Asian Baby Girl)** - 亚洲创作者最佳选择:
- 染发挑染 (Balayage/Platinum blonde)
- 重修容妆 (Heavy contour, arched brows)
- 街头风 (Bodycon dresses, crop tops, athleisure)
- 配饰 (Hoop earrings, temporary tattoos)
- "Bad bitch energy" 态度

**Gym Girl/Fitness**:
- 紧身运动装 (Leggings + sports bra)
- 肌肉线条可见 (Visible ab/muscle definition)
- 健身房场景
- 运动后光泽感

**E-girl/Gamer** (适合娇小身材):
- 猫耳耳机 + RGB灯光
- 百褶裙 + 过膝袜
- 夸张眼线 + 俏皮表情
- 游戏设备可见
- 可以保持白皙肤色

---

## 🎨 实施效果

### Before (东亚审美)

```
❌ 不推荐:
"Woman in bedroom wearing oversized pastel sweater and white knee socks,
sitting on bed with knees pulled to chest, looking down shyly avoiding
camera, pale white skin, small delicate frame, twin braids, hands
covering lower face, soft pink lighting, innocent doe eyes"
```

**问题**:
- 眼神回避 (looking down shyly, avoiding camera)
- 冷白皮 (pale white skin)
- 幼态特征 (small delicate frame, twin braids)
- 遮脸动作 (hands covering face)
- 过度无辜 (innocent doe eyes)

### After (美国审美)

```
✅ 推荐:
"Medium shot from low angle: Woman standing in gym wearing tight black
leggings and purple sports bra, one hand on hip, other hand running
through messy ponytail, direct confident gaze into camera, visible ab
definition, golden tan skin with slight sheen of sweat, arched back
emphasizing curves, legs shoulder-width apart, gym equipment blurred
in background, warm fluorescent lighting, smirking expression"
```

**优势**:
- 直视镜头 (direct confident gaze)
- 暖色肤色 (golden tan skin)
- 自信姿态 (hand on hip, arched back, legs apart)
- 身材展示 (visible ab definition, emphasizing curves)
- 健身场景 (符合美国健康文化)

---

## 🧪 测试验证

### 运行测试脚本

```bash
python test_us_market_optimization.py
```

### 验证要点

生成的 scene_hint 应包含:

**必须项**:
- ✅ Direct eye contact / direct gaze
- ✅ Warm/golden skin tone
- ✅ Confident body language
- ✅ Space-occupying poses

**避免项**:
- ❌ Shy/avoiding gaze
- ❌ Cold pale skin
- ❌ Submissive posture
- ❌ Childish features

---

## 📊 对比表格

### 场景示例对比

| 场景 | 东亚审美 (❌避免) | 美国审美 (✅使用) |
|------|-----------------|-----------------|
| **卧室** | 盘腿坐床上,低头害羞,冷白皮,手遮脸 | 坐床边,直视镜头,手叉腰,塌腰翘臀,暖色肤色 |
| **室外** | 双脚并拢,手交叉胸前,看向别处,纤弱 | 双腿分开,手叉腰,直视镜头,健美身材,古铜肤色 |
| **健身房** | 宽松衣服遮身材,看地板,显得娇小 | 紧身运动装,深蹲姿势,看镜子,肌肉线条,汗水光泽 |

### 身体语言对比

| 特征 | 东亚 (避免) | 美国 (使用) |
|------|-----------|-----------|
| **眼神** | 回避、低头、闪躲 | 直视、聚焦、挑逗 |
| **站姿** | 内八字、双腿并拢 | 双腿分开、重心偏移 |
| **手臂** | 贴紧身体、遮挡 | 远离身体、叉腰、伸展 |
| **胸部** | 含胸、缩肩 | 挺胸、肩膀后展 |
| **表情** | 害羞、无辜、嘟嘴 | 自信、坏笑、性感 |

---

## 🚀 使用建议

### 1. 生成推文时

LLM 会自动应用这些指导生成 scene_hint,无需手动干预。

### 2. 检查生成质量

使用测试脚本检查生成的 scene_hint 是否符合美国审美:

```bash
# 生成测试推文
python main.py --persona personas/test.json --tweets 5

# 检查输出
cat output_standalone/test_*.json | grep "scene_hint"
```

### 3. 针对不同人设选择风格

- **亚洲面孔**: 优先使用 **ABG** 风格
- **健身人设**: 使用 **Gym Girl** 风格
- **娇小/宅**: 使用 **E-girl** 风格

### 4. Negative Prompt 配合

确保 negative prompt 排除东亚特征:

```python
negative_prompt = (
    # 排除幼态化
    "childish features, infantile appearance, overly innocent expression, "
    "doll-like face, excessive smoothing, plastic skin, "
    "cold white skin tone, "

    # 排除不良姿态
    "shrinking posture, hunched shoulders, pigeon-toed stance, "
    "avoiding eye contact, covering face with hands, "

    # 原有的AI感排除
    "ugly, deformed, noisy, blurry, low quality, "
    "artificial lighting, oversaturated, "
    "perfect studio lighting, airbrushed skin, "
    "CGI, 3d render, anime, "
    "perfect, flawless, professional photoshoot"
)
```

---

## 🎓 最佳实践

### Persona 设计建议

在创建 persona 时,可以在 `twitter_persona` 中明确风格倾向:

```json
{
  "twitter_persona": {
    "style_preference": "ABG",
    "body_type": "curvy_athletic",
    "skin_tone": "warm_tan",
    "attitude": "confident_assertive"
  }
}
```

### Scene Hint 质量检查清单

生成后检查:
- [ ] 包含直视镜头描述
- [ ] 肤色描述为暖色调
- [ ] 身体姿态展现自信
- [ ] 没有幼态化特征
- [ ] 符合选定的风格原型 (ABG/Gym Girl/E-girl)

---

## 📚 相关文件

- `core/tweet_generator.py:171-271` - System prompt 美国市场指导
- `test_us_market_optimization.py` - 测试验证脚本
- `docs/跨文化视觉美学报告.md` - 详细研究报告 (中文)

---

## 🔄 版本历史

- **v1.0** (2025-12-10): 初始版本,添加美国市场审美指导到 system prompt

---

**总结**: 通过在 system prompt 中添加详细的美国审美指导,LLM 现在能够生成符合美国市场偏好的 scene descriptions,强调自信、性成熟、力量感,避免东亚的幼态化和羞涩特征。
