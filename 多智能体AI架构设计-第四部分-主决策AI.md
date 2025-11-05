# 多智能体AI架构设计 - 第四部分：主决策AI

## 🎯 核心思想

将前三层的所有分析结果，通过**上下文工程**整合成一个超级Prompt，让主AI做出最优决策。

---

## 📝 主AI的超级Prompt结构

```python
def build_master_prompt(hand, last_play, analysis, collector):
    """
    整合所有信息，构建主AI决策prompt
    analysis: 来自第三部分三个AI的分析结果
    """
    
    prompt = f"""你是掼蛋游戏大师，现在做出最优决策。

【我的手牌】
{format_cards(hand)}

【上家出牌】
{format_last_play(last_play)}

【对手1情报】（来自牌型推断AI）
- 剩余: {analysis['opponent1_cards']['card_count']}张
- 炸弹概率: {analysis['opponent1_cards']['bomb_probability']*100}%
- 威胁等级: {analysis['opponent1_cards']['threat_level']}/10
- 风格: {analysis['opponent1_style']['style_summary']}

【对手2情报】（来自牌型推断AI）
- 剩余: {analysis['opponent2_cards']['card_count']}张  
- 炸弹概率: {analysis['opponent2_cards']['bomb_probability']*100}%
- 威胁等级: {analysis['opponent2_cards']['threat_level']}/10

【局势分析】（来自局势评估AI）
- 我方胜率: {analysis['situation']['win_probability']}%
- 建议策略: {analysis['situation']['recommended_strategy']}
- 行动优先级: {analysis['situation']['action_priority']}

【决策要求】
{analysis['situation']['reasoning']}

请给出你的决策（"过牌" 或 "出牌: X♠ Y♥"），并简述理由。"""
    
    return prompt
```

---

## 🔄 完整决策流程

```
1. 获取我的手牌 + 上家出牌
         ↓
2. 事件收集器提供历史数据
         ↓
3. 并行调用三个分析AI（5秒内完成）
         ↓
4. 整合分析结果 → 构建超级Prompt
         ↓
5. 主AI做决策
         ↓
6. 解析决策 → 执行出牌/过牌
```

---

## ⚡ 关键优化

1. **缓存分析结果** - 5秒内不重复分析同一对手
2. **异步并行** - 三个分析AI同时调用，节省时间
3. **降级策略** - 分析AI失败时，主AI依然能用基础信息决策
4. **Token控制** - 超级Prompt控制在4000 tokens以内

---

## 🎉 完成！

四层架构完整设计：
1. ✅ 综述 - 整体思路
2. ✅ 信息收集层 - SSE事件监听
3. ✅ 分析AI层 - 三个专业AI
4. ✅ 主决策AI - 上下文整合

明天开始实现！💪

---

*最后更新: 2025-11-06*
*系列文档完结 🎊*
