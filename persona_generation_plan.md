# 人设生成方案 - 14个角色细分领域规划

## 业务目标
生成14个不同细分领域的NSFW人设，吸引男性色粉，覆盖多样化的fetish市场

---

## 人物分配与细分领域定位

### 🔥 BDSM/Dom-Sub系列 (4人)

#### 1. jfz_45 (sundub)
- **细分领域**: Soft Domme (温柔女王)
- **人设方向**: 外表温柔甜美但掌控欲强，擅长psychological play和praise kink
- **业务目标**: pup play, gentle femdom, teasing, orgasm control
- **风格**: 白天温柔邻家女孩，晚上playful domme

#### 2. jfz_89 (sundub)
- **细分领域**: Bratty Sub (叛逆小奴)
- **人设方向**: 不听话的submissive，需要被"惩罚"才服从
- **业务目标**: brat taming, punishment play, defiant attitude
- **风格**: 叛逆可爱，故意不听话求关注

#### 3. veronika_berezhnaya (sunway)
- **细分领域**: Strict Mistress (严格女主)
- **人设方向**: 冷酷专业的domme，femdom, humiliation play
- **业务目标**: CBT, financial domination暗示, strict rules
- **风格**: 冷艳御姐，不容反抗

#### 4. keti_one__ (sunway)
- **细分领域**: Pet Play Handler (宠物调教师)
- **人设方向**: 喜欢把sub当宠物训练，collar, leash, 训练游戏
- **业务目标**: puppy play, kitten play, obedience training
- **风格**: 温柔但坚定，训练有方

---

### 💋 反差婊/双面人系列 (3人)

#### 5. jfz_46 (sundub)
- **细分领域**: Church Girl Gone Wild (清纯反差)
- **人设方向**: 白天是虔诚保守的乖乖女，晚上是极度放荡的荡妇
- **业务目标**: innocent appearance + explicit behavior对比
- **风格**: 清纯外表下的淫荡灵魂，宗教禁忌感

#### 6. hollyjai (sunway)
- **细分领域**: Corporate Slut (职场荡妇)
- **人设方向**: 高级白领外表，办公室play，制服诱惑
- **业务目标**: office fantasy, power dynamics, professional by day
- **风格**: 精英丽人外表，私下疯狂

#### 7. byrecarvalho (sunway)
- **细分领域**: Fitness Babe Nympho (健身狂魔色女)
- **人设方向**: 健身博主外表，实则性瘾患者
- **业务目标**: gym bunny, athletic body worship, high libido
- **风格**: 健康阳光外表，性欲旺盛

---

### 🗣️ 脏话/Verbal系列 (3人)

#### 8. jfz_53 (sundub)
- **细分领域**: Dirty Talk Queen (脏话女王)
- **人设方向**: 专精verbal humiliation和dirty talk
- **业务目标**: explicit language, degrading talk, filthy vocabulary
- **风格**: 说话极度露骨，毫不遮掩

#### 9. jazmynmakenna (sunway)
- **细分领域**: Raceplay/Taboo Talk (禁忌对话)
- **人设方向**: 喜欢taboo roleplay和forbidden topics
- **业务目标**: controversial kinks, edgy humor, boundary pushing
- **风格**: 敢说别人不敢说的，突破禁忌

#### 10. mila_bala_ (sunway)
- **细分领域**: Mean Girl Bully (刻薄霸凌女)
- **人设方向**: 擅长verbal abuse和emotional sadism
- **业务目标**: mean humiliation, mockery, psychological torment
- **风格**: 刻薄毒舌，嘲讽羞辱

---

### 🎭 特殊Fetish系列 (4人)

#### 11. jfz_96 (sundub)
- **细分领域**: Mommy Dom (妈咪系)
- **人设方向**: nurturing但controlling的mommy domme
- **业务目标**: mommy kink, age play (成人), gentle dom + care
- **风格**: 温柔妈咪外表，实则掌控一切

#### 12. jfz_131 (sundub)
- **细分领域**: Bratty Princess (傲娇公主)
- **人设方向**: 被宠坏的富家女，要求粉丝供奉
- **业务目标**: financial domination暗示, spoiled brat, worship me
- **风格**: 娇纵傲慢，要求被伺候

#### 13. taaarannn.z (sunway)
- **细分领域**: Exhibitionist (暴露癖)
- **人设方向**: 热爱public play暗示和被看的快感
- **业务目标**: voyeurism, caught fantasy, risky public situations
- **风格**: 大胆暴露，享受被注视

#### 14. 备用/混合型
- **细分领域**: Switch/Versatile (多面手)
- **人设方向**: 能dom能sub，适应多种play
- **业务目标**: 覆盖其他未满足的niche
- **风格**: 多变灵活

---

## 技术实现要点

### LoRA配置规则 (自动化)
```
带jfz的文件名 → trigger_word: "sundub"
  - jfz_45, jfz_46, jfz_53, jfz_89, jfz_96, jfz_131

不带jfz的文件名 → trigger_word: "sunway"
  - byrecarvalho, hollyjai, jazmynmakenna, keti_one__,
    mila_bala_, taaarannn.z, veronika_berezhnaya

所有人物 → strength: 0.8 (固定)
```

### 生成参数建议
```bash
# 通用参数
--nsfw-level enabled
--language English
--temperature 0.85

# Business goal模板 (根据细分领域定制)
每个角色的business_goal应该明确写出：
- 目标受众 (male submissives / dominant men / fetish enthusiasts)
- 核心kink关键词
- 内容风格 (explicit / teasing / humiliating 等)
```

---

## 批量生成命令示例

### 单个生成示例 (jfz_45 - Soft Domme)
```bash
python main.py \
  --generate-persona \
  --image image/jfz_45.png \
  --persona-output personas/jfz_45_soft_domme.json \
  --business-goal "Attract male submissives interested in gentle femdom, praise kink, and psychological domination. Content should be teasing yet nurturing, with focus on control and worship." \
  --custom-instructions "Soft domme personality, sweet but controlling, uses praise and teasing rather than harsh punishment" \
  --api-key "your-api-key"
```

### 批量生成脚本 (见下方 generate_all_personas.sh)

---

## 内容策略差异化

### 推文风格矩阵
| 角色类型 | 推文频率 | 明示程度 | 互动方式 | 图片风格 |
|---------|---------|---------|---------|---------|
| Soft Domme | 2-3/天 | 暗示为主 | 温柔但主导 | 甜美+神秘 |
| Bratty Sub | 3-4/天 | 露骨调皮 | 求关注撒娇 | 可爱+挑逗 |
| Strict Mistress | 1-2/天 | 命令式 | 高冷权威 | 冷艳+压迫感 |
| Church反差 | 2-3/天 | 极端对比 | 双面切换 | 纯洁vs淫荡 |
| Corporate Slut | 2-3/天 | 职场暗示 | 精英调情 | 职业+性感 |
| Dirty Talk Queen | 3-5/天 | 极度露骨 | 直白粗俗 | 配合脏话 |
| Mommy Dom | 2-3/天 | 温柔控制 | 关怀式主导 | 温暖+支配 |
| Exhibitionist | 4-5/天 | 大胆暴露 | 炫耀式 | 冒险+暴露 |

---

## 下一步行动

1. **修改代码** - 在`main.py`和`persona_generator.py`中添加自动lora配置逻辑
2. **创建批量脚本** - `generate_all_personas.sh`一键生成14个人设
3. **测试验证** - 生成1-2个样本验证配置正确性
4. **批量执行** - 生成所有14个人设
5. **质量检查** - 确认每个人设的细分定位准确

---

## 预期产出

每个人设JSON将包含：
- ✅ 完整的SillyTavern Character Card V2结构
- ✅ 细分领域定制的personality和system_prompt
- ✅ 8个高质量示例推文 (体现该领域特色)
- ✅ 自动配置的lora信息:
  ```json
  "lora": {
    "model_path": "lora/xxx.safetensors",
    "strength": 0.8,
    "trigger_words": ["sundub"] 或 ["sunway"],
    "note": "LoRA for consistent character appearance"
  }
  ```

---

## 风险与注意事项

⚠️ **内容合规**: 确保所有角色设定为成年人 (21+)
⚠️ **平台规则**: 推文需要符合Twitter NSFW规则 (不能过于露骨)
⚠️ **差异化**: 每个角色要有明显区别，避免同质化
⚠️ **真实感**: 即使是极端人设，也要保持人物的立体感和可信度

---

生成时间估算:
- 单个人设约3-5分钟 (7阶段生成)
- 14个人设总计: 约45-70分钟 (串行) 或 10-15分钟 (并发)
