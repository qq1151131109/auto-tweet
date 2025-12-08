#!/bin/bash
# 批量生成14个人设脚本
# 基于persona_generation_plan.md中的细分领域规划

set -e  # 遇到错误立即退出

# API配置（从环境变量或.env读取）
API_KEY="${OPENAI_API_KEY:-}"
API_BASE="${OPENAI_API_BASE:-https://api.openai.com/v1}"
MODEL="${OPENAI_MODEL:-gpt-4o}"

# 检查API_KEY
if [ -z "$API_KEY" ]; then
    echo "错误: 请设置OPENAI_API_KEY环境变量"
    echo "或在.env文件中配置"
    exit 1
fi

# 通用参数
NSFW_LEVEL="enabled"
LANGUAGE="English"
TEMPERATURE="0.85"

echo "======================================================================"
echo "🚀 批量生成14个NSFW人设"
echo "======================================================================"
echo "API: $API_BASE"
echo "Model: $MODEL"
echo "======================================================================"
echo ""

# 创建输出目录
mkdir -p personas

# ============================================================================
# 🔥 BDSM/Dom-Sub系列 (4人)
# ============================================================================

echo "📍 [1/14] 生成: jfz_45 - Soft Domme (温柔女王)"
python main.py \
  --generate-persona \
  --image image/jfz_45.png \
  --persona-output personas/jfz_45_soft_domme.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract male submissives interested in gentle femdom, praise kink, and psychological domination. Content should be teasing yet nurturing, with focus on control and worship. Target audience: submissive men who prefer soft dominance over harsh punishment." \
  --custom-instructions "Soft domme personality, sweet but controlling, uses praise and teasing rather than harsh punishment. Focus on psychological play, orgasm control, and gentle guidance. Avoids extreme pain or humiliation." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

echo ""
echo "📍 [2/14] 生成: jfz_89 - Bratty Sub (叛逆小奴)"
python main.py \
  --generate-persona \
  --image image/jfz_89.png \
  --persona-output personas/jfz_89_bratty_sub.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract dominant men who enjoy brat taming and defiant submissives. Content should be playfully disobedient, seeking attention through mischief. Target audience: doms who like the challenge of 'breaking' a bratty sub." \
  --custom-instructions "Bratty submissive personality, deliberately disobedient and provocative, constantly testing boundaries. Seeks punishment through misbehavior. Playful but ultimately wants to be controlled. Uses teasing language and defiant attitude." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

echo ""
echo "📍 [3/14] 生成: veronika_berezhnaya - Strict Mistress (严格女主)"
python main.py \
  --generate-persona \
  --image image/veronika_berezhnaya.jpg \
  --persona-output personas/veronika_strict_mistress.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract submissive men interested in strict femdom, humiliation, and total obedience. Content should be cold, commanding, and unapologetic. Target audience: devoted subs seeking a demanding Mistress." \
  --custom-instructions "Strict dominant personality, cold and professional in her dominance. Specializes in humiliation play, strict rules, and punishments. Uses commanding language, expects immediate obedience. Hints at financial domination and CBT." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

echo ""
echo "📍 [4/14] 生成: keti_one__ - Pet Play Handler (宠物调教师)"
python main.py \
  --generate-persona \
  --image image/keti_one__.jpg \
  --persona-output personas/keti_pet_handler.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract men interested in pet play, collars, and obedience training. Content should focus on training dynamics, pet-like behavior, and ownership. Target audience: subs who enjoy puppy/kitten play." \
  --custom-instructions "Pet play handler personality, enjoys training submissives as pets (puppies, kittens). Uses collars, leashes, and training commands. Firm but caring, rewards good behavior. Focuses on obedience and pet-like devotion." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

# ============================================================================
# 💋 反差婊/双面人系列 (3人)
# ============================================================================

echo ""
echo "📍 [5/14] 生成: jfz_46 - Church Girl Gone Wild (清纯反差)"
python main.py \
  --generate-persona \
  --image image/jfz_46.png \
  --persona-output personas/jfz_46_church_wild.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract men fascinated by the contrast between innocent appearance and wild behavior. Content should emphasize religious/innocent daytime persona versus explicit nighttime content. Target audience: men who enjoy corruption fantasies and purity/sin contrast." \
  --custom-instructions "Dual personality: devout church girl by day, wild and uninhibited by night. Emphasize the stark contrast between innocent appearance and explicit behavior. Uses religious imagery mixed with sexual content. Forbidden fruit appeal." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

echo ""
echo "📍 [6/14] 生成: hollyjai - Corporate Slut (职场荡妇)"
python main.py \
  --generate-persona \
  --image image/hollyjai.jpg \
  --persona-output personas/hollyjai_corporate.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract men interested in office fantasies, power dynamics, and professional women with secret wild sides. Content should mix corporate polish with sexual adventure. Target audience: men aroused by suit/uniform kink and workplace scenarios." \
  --custom-instructions "High-powered corporate professional by day, sexually adventurous by night. Emphasize office settings, business attire, power dynamics. Hints at workplace affairs and after-hours escapades. Sophisticated but secretly uninhibited." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

echo ""
echo "📍 [7/14] 生成: byrecarvalho - Fitness Babe Nympho (健身狂魔色女)"
python main.py \
  --generate-persona \
  --image image/byrecarvalho.jpg \
  --persona-output personas/byrecarvalho_fitness.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract men interested in athletic bodies, high libido, and gym culture. Content should showcase fitness lifestyle mixed with insatiable sexual appetite. Target audience: fitness enthusiasts and body worship fans." \
  --custom-instructions "Fitness influencer with extremely high sex drive. Emphasize athletic body, gym culture, and constant sexual energy. Posts mix workout content with explicit sexual content. Nymphomaniac personality, always craving more." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

# ============================================================================
# 🗣️ 脏话/Verbal系列 (3人)
# ============================================================================

echo ""
echo "📍 [8/14] 生成: jfz_53 - Dirty Talk Queen (脏话女王)"
python main.py \
  --generate-persona \
  --image image/jfz_53.png \
  --persona-output personas/jfz_53_dirty_talk.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract men aroused by explicit verbal content, dirty talk, and graphic language. Content should be extremely explicit in language, focusing on verbal descriptions of sexual acts. Target audience: men who prioritize dirty talk and verbal humiliation." \
  --custom-instructions "Specializes in dirty talk and explicit verbal content. Uses graphic sexual language without shame. Describes acts in filthy detail. No euphemisms, completely uninhibited vocabulary. Focuses on verbal degradation and explicit descriptions." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

echo ""
echo "📍 [9/14] 生成: jazmynmakenna - Raceplay/Taboo Talk (禁忌对话)"
python main.py \
  --generate-persona \
  --image image/jazmynmakenna.jpg \
  --persona-output personas/jazmynmakenna_taboo.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract men interested in edgy, taboo roleplay and boundary-pushing content. Content should hint at forbidden scenarios and controversial kinks. Target audience: men seeking extreme or unconventional fantasies." \
  --custom-instructions "Enjoys taboo roleplay and pushing boundaries. Comfortable with controversial topics and edgy humor. Hints at forbidden scenarios. Specializes in making the 'unacceptable' acceptable in fantasy context. Bold and unapologetic." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

echo ""
echo "📍 [10/14] 生成: mila_bala_ - Mean Girl Bully (刻薄霸凌女)"
python main.py \
  --generate-persona \
  --image image/mila_bala_.jpg \
  --persona-output personas/mila_mean_girl.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract men aroused by verbal abuse, mockery, and emotional sadism. Content should be mean-spirited, mocking, and psychologically cruel. Target audience: men who enjoy being humiliated and degraded." \
  --custom-instructions "Mean girl personality, specializes in verbal abuse and mockery. Enjoys humiliating and belittling followers. Uses cruel language, sarcastic insults, and psychological torment. Makes fun of inadequacy. Popular girl who bullies for pleasure." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

# ============================================================================
# 🎭 特殊Fetish系列 (4人)
# ============================================================================

echo ""
echo "📍 [11/14] 生成: jfz_96 - Mommy Dom (妈咪系)"
python main.py \
  --generate-persona \
  --image image/jfz_96.png \
  --persona-output personas/jfz_96_mommy_dom.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract men interested in mommy domme dynamics, nurturing dominance, and age play (adult only). Content should balance care and control, maternal affection with dominance. Target audience: men seeking gentle but firm maternal dominance." \
  --custom-instructions "Mommy domme personality, nurturing but controlling. Uses maternal language mixed with dominance. Cares for submissives while maintaining control. Gentle punishment and praise. Emphasizes good boy/bad boy dynamics. All participants are adults." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

echo ""
echo "📍 [12/14] 生成: jfz_131 - Bratty Princess (傲娇公主)"
python main.py \
  --generate-persona \
  --image image/jfz_131.png \
  --persona-output personas/jfz_131_princess.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract men who enjoy spoiling women and financial domination themes. Content should emphasize entitlement, luxury, and demanding worship. Target audience: men aroused by serving a spoiled princess who expects gifts and tribute." \
  --custom-instructions "Spoiled bratty princess personality, expects to be worshipped and spoiled. Hints at financial domination, expects gifts and tributes. Demanding and entitled attitude. Uses followers for attention and presents. Luxurious lifestyle, princess treatment required." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

echo ""
echo "📍 [13/14] 生成: taaarannn.z - Exhibitionist (暴露癖)"
python main.py \
  --generate-persona \
  --image image/taaarannn.z.jpg \
  --persona-output personas/taaarannn_exhibitionist.json \
  --nsfw-level "$NSFW_LEVEL" \
  --language "$LANGUAGE" \
  --temperature "$TEMPERATURE" \
  --business-goal "Attract voyeurs and men interested in public play, exhibitionism, and risky situations. Content should hint at public exposure and being watched. Target audience: men aroused by exhibition and voyeurism fantasies." \
  --custom-instructions "Exhibitionist personality, loves being watched and showing off. Hints at risky public situations and exposure. Thrives on attention and being seen. Posts content suggesting public play. Enjoys the thrill of potentially being caught." \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

# ============================================================================
# 完成
# ============================================================================

echo ""
echo "======================================================================"
echo "✅ 批量生成完成！"
echo "======================================================================"
echo "共生成 13 个人设文件 (保存在 personas/ 目录)"
echo ""
echo "下一步操作："
echo "1. 检查生成的人设文件: ls -lh personas/"
echo "2. 查看某个人设内容: cat personas/jfz_45_soft_domme.json | jq '.data.name, .data.lora'"
echo "3. 生成推文: python main.py --persona personas/xxx.json --tweets 10 --generate-calendar"
echo "======================================================================"
