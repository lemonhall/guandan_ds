# 多智能体AI架构设计 - 第三部分：分析AI层

## 🤖 三个专业分析AI

每个AI都是独立的LLM调用，专注于特定领域的分析，可以**并行执行**提高效率。

---

## 1️⃣ 牌型推断AI (Card Inference Agent)

### 目标
推测对手剩余的牌型分布和关键牌概率

### 输入数据
- 对手已出的所有牌
- 对手剩余牌数
- 全局已出现的牌
- 对手的出牌/过牌决策历史

### Prompt设计

```python
def get_card_inference_prompt(player_id, collector):
    """
    构建牌型推断AI的prompt
    """
    # 获取数据
    opponent_played = collector.get_cards_played_by_player(player_id)
    remaining_count = collector.get_remaining_cards_count(player_id)
    cards_not_seen = collector.get_cards_not_seen_yet()
    opponent_history = collector.get_player_history(player_id, limit=20)
    
    # 格式化已出牌
    played_str = format_cards_list(opponent_played)
    
    # 格式化未见过的牌
    not_seen_str = format_cards_list(cards_not_seen)
    
    # 分析出牌模式
    pattern_analysis = analyze_play_pattern(opponent_history)
    
    prompt = f"""你是一个掼蛋游戏的牌型推断专家，精通概率论和组合数学。

【任务】
推测玩家{player_id}当前可能剩余的牌型分布。

【已知信息】
1. 该玩家已出的牌（共{len(opponent_played)}张）：
{played_str}

2. 该玩家剩余牌数：{remaining_count}张

3. 全局尚未出现的牌（共{len(cards_not_seen)}张）：
{not_seen_str}

4. 该玩家出牌模式分析：
{pattern_analysis}

【推断规则】
1. 炸弹概率：
   - 如果该玩家从未出过炸弹，但多次在强势局面选择过牌
   - 则炸弹存在概率较高（正在憋大招）
   
2. 大牌概率：
   - 统计全局已出现的2、大王、小王数量
   - 计算该玩家持有的数学期望
   
3. 牌型分布：
   - 根据剩余牌数和已出牌型
   - 推测可能的单牌/对子/三张分布
   
4. 关键判断：
   - 如果该玩家频繁过牌，可能手牌不整（散牌多）
   - 如果该玩家出牌果断，可能手牌连续性好

【输出要求】
请以JSON格式输出分析结果：
```json
{{
  "bomb_probability": 0.6,           // 有炸弹的概率 (0-1)
  "bomb_type": "可能是4个6或4个7",    // 推测的炸弹类型
  "big_cards": {{
    "2": 1,                           // 推测有几个2
    "joker_small": 0,                 // 推测有几个小王
    "joker_big": 1                    // 推测有几个大王
  }},
  "card_distribution": {{
    "singles": 8,                     // 推测单牌数量
    "pairs": 3,                       // 推测对子数量
    "triples": 1                      // 推测三张数量
  }},
  "hand_quality": "中等",             // 手牌质量：强/中等/弱
  "threat_level": 7,                 // 威胁等级 (1-10)
  "reasoning": "该玩家保留了多张大牌未出，且在多次可以出牌时选择过牌，推测手中有炸弹或大王。但单牌较多，整体威胁中等。"
}}
```

只返回JSON，不要其他解释。"""
    
    return prompt
```

### 输出格式
```python
{
    "bomb_probability": 0.6,
    "bomb_type": "可能是4个6",
    "big_cards": {"2": 1, "joker_small": 0, "joker_big": 1},
    "card_distribution": {"singles": 8, "pairs": 3, "triples": 1},
    "hand_quality": "中等",
    "threat_level": 7,
    "reasoning": "推理说明..."
}
```

---

## 2️⃣ 风格分析AI (Opponent Profiling Agent)

### 目标
分析对手的打牌风格、习惯和策略倾向

### 输入数据
- 对手的完整出牌历史
- 对手的出牌/过牌选择
- 关键决策点的表现

### Prompt设计

```python
def get_style_analysis_prompt(player_id, collector):
    """
    构建风格分析AI的prompt
    """
    opponent_history = collector.get_player_history(player_id)
    
    # 提取关键决策点
    key_decisions = extract_key_decisions(opponent_history)
    
    # 统计数据
    total_plays = sum(1 for h in opponent_history if h['action'] == 'play')
    total_passes = sum(1 for h in opponent_history if h['action'] == 'pass')
    
    # 格式化决策历史
    history_str = format_decision_history(opponent_history[-15:])
    key_decisions_str = format_key_decisions(key_decisions)
    
    prompt = f"""你是一个掼蛋游戏的心理分析专家，擅长通过玩家行为推断其策略风格。

【任务】
分析玩家{player_id}的打牌风格和策略倾向。

【数据统计】
- 总出牌次数：{total_plays}次
- 总过牌次数：{total_passes}次
- 出牌率：{total_plays/(total_plays+total_passes)*100:.1f}%

【最近15轮出牌记录】
{history_str}

【关键决策点分析】
{key_decisions_str}

【分析维度】

1. **激进度 (1-10)**
   - 1-3分：保守型，常过牌，倾向保留大牌
   - 4-7分：平衡型，根据局势调整
   - 8-10分：激进型，频繁用大牌压制

2. **策略性 (1-10)**
   - 1-3分：无明显策略，随意出牌
   - 4-7分：有一定策略意识
   - 8-10分：策略性强，懂配合和控场

3. **手牌管理能力 (1-10)**
   - 出牌是否有序，是否避免拆牌型
   - 是否合理规划大牌使用时机

4. **对局感知 (1-10)**
   - 是否根据局势调整打法
   - 是否注意配合队友/针对对手

【输出要求】
以JSON格式输出：
```json
{{
  "aggression": 7,                    // 激进度 (1-10)
  "strategy": 6,                      // 策略性 (1-10)
  "hand_management": 5,               // 手牌管理能力 (1-10)
  "game_sense": 7,                    // 对局感知 (1-10)
  "style_summary": "偏激进的平衡型玩家", // 风格总结
  "habits": [                         // 打牌习惯
    "喜欢用大牌压制",
    "关键时刻会保留炸弹",
    "较少配合队友"
  ],
  "weaknesses": [                     // 弱点
    "容易拆散手牌",
    "对局势判断不够精准"
  ],
  "counter_strategy": "可以通过频繁出小对子消耗其手牌，迫使其拆牌型。注意其可能留有炸弹，关键时刻需谨慎。"
}}
```

只返回JSON。"""
    
    return prompt
```

### 输出格式
```python
{
    "aggression": 7,
    "strategy": 6,
    "hand_management": 5,
    "game_sense": 7,
    "style_summary": "偏激进的平衡型玩家",
    "habits": ["喜欢用大牌压制", "关键时刻会保留炸弹"],
    "weaknesses": ["容易拆散手牌"],
    "counter_strategy": "应对策略说明..."
}
```

---

## 3️⃣ 局势评估AI (Situation Analysis Agent)

### 目标
评估当前游戏局势，给出策略建议

### 输入数据
- 四家剩余牌数
- 最近的出牌趋势
- 队友和对手的状态

### Prompt设计

```python
def get_situation_analysis_prompt(my_player_id, collector):
    """
    构建局势评估AI的prompt
    """
    # 获取所有玩家状态
    all_stats = collector.player_stats
    
    # 计算队友和对手
    teammate_id = (my_player_id + 2) % 4 if (my_player_id + 2) % 4 != 0 else 4
    opponents = [i for i in [1,2,3,4] if i != my_player_id and i != teammate_id]
    
    my_cards = all_stats[my_player_id]['cards_remaining']
    teammate_cards = all_stats[teammate_id]['cards_remaining']
    opponent1_cards = all_stats[opponents[0]]['cards_remaining']
    opponent2_cards = all_stats[opponents[1]]['cards_remaining']
    
    # 获取最近趋势
    recent_history = collector.get_recent_history(limit=10)
    trend_str = format_recent_trend(recent_history)
    
    # 获取当前控场者
    controller = get_current_controller(recent_history)
    
    prompt = f"""你是一个掼蛋游戏的局势分析专家，擅长评估胜率和制定策略。

【任务】
评估当前游戏局势，给出我方策略建议。

【四家剩余牌数】
- 我方（玩家{my_player_id}）：{my_cards}张
- 队友（玩家{teammate_id}）：{teammate_cards}张
- 对手1（玩家{opponents[0]}）：{opponent1_cards}张
- 对手2（玩家{opponents[1]}）：{opponent2_cards}张

【当前控场】
{controller}

【最近10轮出牌趋势】
{trend_str}

【分析要点】

1. **胜负判断**
   - 我方总牌数 vs 对方总牌数
   - 谁最接近获胜（牌数最少）
   - 是否有明显优势/劣势

2. **策略选择**
   - 如果队友快赢（≤5张），应配合队友
   - 如果我方领先，可保守打法保持优势
   - 如果我方落后，需激进追赶
   - 如果对手快赢（≤5张），需全力阻止

3. **关键威胁**
   - 识别最大威胁来自哪位对手
   - 判断是否需要用炸弹/大牌压制

4. **节奏控制**
   - 当前出牌节奏是否对我方有利
   - 是否需要抢夺出牌权

【输出要求】
以JSON格式输出：
```json
{{
  "our_total": {my_cards + teammate_cards},      // 我方总牌数
  "their_total": {opponent1_cards + opponent2_cards}, // 对方总牌数
  "win_probability": 55,            // 我方胜率 (0-100%)
  "game_phase": "中期",              // 游戏阶段：早期/中期/后期/决胜
  "biggest_threat": {opponents[0]},  // 最大威胁玩家ID
  "recommended_strategy": "激进",    // 建议策略：激进/平衡/保守/配合队友
  "key_points": [                   // 关键要点
    "队友剩余5张牌，接近获胜",
    "对手1威胁较大，需重点防守",
    "当前我方控场，可以主动出牌"
  ],
  "action_priority": [              // 行动优先级
    "优先帮助队友清空手牌",
    "阻止对手1获得出牌权",
    "保留炸弹用于关键时刻"
  ],
  "reasoning": "当前队友剩余5张牌接近获胜，我方整体领先。应采取配合策略，帮助队友出完手牌。同时警惕对手1的反扑。"
}}
```

只返回JSON。"""
    
    return prompt
```

### 输出格式
```python
{
    "our_total": 35,
    "their_total": 42,
    "win_probability": 65,
    "game_phase": "中期",
    "biggest_threat": 1,
    "recommended_strategy": "配合队友",
    "key_points": ["队友剩余5张牌，接近获胜"],
    "action_priority": ["优先帮助队友清空手牌"],
    "reasoning": "局势分析说明..."
}
```

---

## 🔄 三AI并行调用

```python
import asyncio
from openai import AsyncOpenAI

async def get_all_analysis(my_player_id, collector, opponents):
    """
    并行调用三个分析AI
    """
    client = AsyncOpenAI(api_key=API_KEY)
    
    # 构建三个prompt
    prompts = {
        'card_inference_opp1': get_card_inference_prompt(opponents[0], collector),
        'card_inference_opp2': get_card_inference_prompt(opponents[1], collector),
        'style_analysis_opp1': get_style_analysis_prompt(opponents[0], collector),
        'style_analysis_opp2': get_style_analysis_prompt(opponents[1], collector),
        'situation': get_situation_analysis_prompt(my_player_id, collector)
    }
    
    # 并行调用
    tasks = []
    for name, prompt in prompts.items():
        task = client.chat.completions.create(
            model='deepseek-chat',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,  # 降低温度，要求更精确
            response_format={'type': 'json_object'}  # 要求JSON输出
        )
        tasks.append(task)
    
    # 等待所有结果
    results = await asyncio.gather(*tasks)
    
    # 解析结果
    analysis = {
        'opponent1_cards': json.loads(results[0].choices[0].message.content),
        'opponent2_cards': json.loads(results[1].choices[0].message.content),
        'opponent1_style': json.loads(results[2].choices[0].message.content),
        'opponent2_style': json.loads(results[3].choices[0].message.content),
        'situation': json.loads(results[4].choices[0].message.content)
    }
    
    return analysis
```

---

## 🎯 辅助函数

### 格式化函数

```python
def format_cards_list(cards):
    """格式化牌列表为字符串"""
    if not cards:
        return "无"
    return "、".join([f"{c['value']}{c['suit']}" for c in cards])

def format_decision_history(history):
    """格式化决策历史"""
    lines = []
    for i, h in enumerate(history, 1):
        if h['action'] == 'play':
            cards_str = format_cards_list(h['cards'])
            lines.append(f"{i}. 出牌：{h['card_type']} ({cards_str})")
        else:
            lines.append(f"{i}. 过牌")
    return "\n".join(lines)

def format_recent_trend(history):
    """格式化最近趋势"""
    lines = []
    for h in history:
        player = h['player_name']
        if h['action'] == 'play':
            cards_str = format_cards_list(h['cards'])
            lines.append(f"{player}: {h['card_type']} ({cards_str}) [剩{h['card_count']}张]")
        else:
            lines.append(f"{player}: 过牌 [剩{h['card_count']}张]")
    return "\n".join(lines)
```

### 分析函数

```python
def analyze_play_pattern(history):
    """分析出牌模式"""
    patterns = []
    
    # 统计出牌类型分布
    card_types = {}
    for h in history:
        if h['action'] == 'play':
            ct = h['card_type']
            card_types[ct] = card_types.get(ct, 0) + 1
    
    # 分析过牌率
    total = len(history)
    passes = sum(1 for h in history if h['action'] == 'pass')
    pass_rate = passes / total if total > 0 else 0
    
    patterns.append(f"过牌率: {pass_rate*100:.1f}%")
    patterns.append(f"出牌类型分布: {card_types}")
    
    # 分析是否有炸弹
    has_bomb = any('炸弹' in h.get('card_type', '') for h in history if h['action'] == 'play')
    patterns.append(f"已出炸弹: {'是' if has_bomb else '否'}")
    
    return "\n".join(patterns)

def extract_key_decisions(history):
    """提取关键决策点"""
    # 找出在强势局面选择过牌的情况
    # 找出用大牌压小牌的情况
    # 等等...
    key_decisions = []
    # TODO: 实现具体逻辑
    return key_decisions
```

---

## ⚡ 性能优化

### 1. 缓存机制
```python
# 如果局势变化不大，可以复用之前的分析
cache = {}
cache_ttl = 5  # 秒

def get_cached_analysis(key):
    if key in cache:
        result, timestamp = cache[key]
        if time.time() - timestamp < cache_ttl:
            return result
    return None
```

### 2. 降级策略
```python
# 如果LLM调用失败，返回默认值
def safe_analysis_call(prompt, default_result):
    try:
        result = call_llm(prompt)
        return json.loads(result)
    except Exception as e:
        print(f"分析AI调用失败: {e}")
        return default_result
```

---

## 📊 数据流

```
事件收集器(GameEventCollector)
        ↓
    查询数据
        ↓
  构建Prompt (三个AI并行)
        ↓
    ┌─────┴─────┐
    ↓     ↓     ↓
 牌型AI 风格AI 局势AI
    ↓     ↓     ↓
    └─────┬─────┘
        ↓
  整合分析结果
        ↓
   主AI决策引擎（第四部分）
```

---

## ✅ 下一步

**第四部分**将详细设计：
- 主AI决策引擎的超级Prompt
- 如何整合三个分析AI的结果
- 上下文工程的最佳实践
- 完整的决策流程

---

*最后更新: 2025-11-06*
*依赖：第一部分（综述）、第二部分（信息收集层）*
