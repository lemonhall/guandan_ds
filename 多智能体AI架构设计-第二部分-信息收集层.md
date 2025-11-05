# 多智能体AI架构设计 - 第二部分：信息收集层

## 📡 第一层：SSE事件流（已有）

服务器已实现SSE推送，端点：`/game/events`

### 推送的事件类型

#### 1. 连接事件
```json
{
  "type": "connected"
}
```

#### 2. 出牌事件
```json
{
  "type": "play",
  "playerName": "右侧",
  "playerId": 1,
  "cardType": "单牌",
  "cards": "3♠",
  "cardCount": 26
}
```

#### 3. 过牌事件
```json
{
  "type": "pass",
  "playerName": "对家",
  "playerId": 2,
  "cardCount": 27
}
```

---

## 🎯 第二层：信息收集器设计

### 核心类：GameEventCollector

```python
class GameEventCollector:
    """
    游戏事件收集器
    职责：
    1. 监听SSE事件流
    2. 解析并存储所有出牌历史
    3. 统计各家剩余牌数
    4. 提供数据查询接口
    """
```

### 数据结构设计

#### 1. 完整出牌历史
```python
self.play_history = [
    {
        'round': 1,              # 第几轮
        'player_id': 1,          # 玩家ID
        'player_name': '右侧',   # 玩家名称
        'action': 'play',        # 动作: play/pass
        'card_type': '单牌',     # 牌型
        'cards': ['3♠'],         # 具体牌
        'card_count': 26,        # 剩余牌数
        'timestamp': 1699200000  # 时间戳
    },
    # ...
]
```

#### 2. 各家剩余牌数统计
```python
self.player_stats = {
    1: {
        'name': '右侧',
        'cards_remaining': 26,
        'last_play': {'card_type': '单牌', 'cards': ['3♠']},
        'play_count': 15,         # 出牌次数
        'pass_count': 3           # 过牌次数
    },
    # ... 其他玩家
}
```

#### 3. 已出现的牌统计
```python
self.cards_played = {
    '3♠': 1,
    '3♥': 2,
    '4♦': 1,
    # ... 所有已出现的牌
}
```

#### 4. 剩余未出现的牌
```python
self.cards_remaining = {
    '3♣': 1,
    '4♠': 2,
    # ... 所有未出现的牌
}
```

---

## 🔧 核心功能实现

### 1. SSE事件监听

```python
import sseclient
import requests
from threading import Thread

def listen_sse_events(self):
    """
    在后台线程持续监听SSE事件
    """
    url = f'{self.server_url}/game/events'
    
    while not self.stop_event.is_set():
        try:
            response = requests.get(url, stream=True, timeout=60)
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if self.stop_event.is_set():
                    break
                
                data = json.loads(event.data)
                self._process_event(data)
        
        except Exception as e:
            print(f"SSE连接断开: {e}, 5秒后重连...")
            time.sleep(5)
```

### 2. 事件处理与解析

```python
def _process_event(self, event_data):
    """
    处理单个事件，更新内部数据
    """
    event_type = event_data.get('type')
    
    if event_type == 'connected':
        print("✅ SSE连接成功")
        return
    
    elif event_type == 'play':
        self._handle_play_event(event_data)
    
    elif event_type == 'pass':
        self._handle_pass_event(event_data)

def _handle_play_event(self, data):
    """
    处理出牌事件
    """
    player_id = data['playerId']
    cards_str = data['cards']
    card_type = data['cardType']
    card_count = data['cardCount']
    
    # 解析牌
    cards = self._parse_cards_string(cards_str)
    
    # 添加到历史
    self.play_history.append({
        'round': self.current_round,
        'player_id': player_id,
        'player_name': data['playerName'],
        'action': 'play',
        'card_type': card_type,
        'cards': cards,
        'card_count': card_count,
        'timestamp': time.time()
    })
    
    # 更新玩家统计
    self._update_player_stats(player_id, 'play', cards, card_count)
    
    # 更新已出牌记录
    self._update_cards_played(cards)

def _handle_pass_event(self, data):
    """
    处理过牌事件
    """
    player_id = data['playerId']
    card_count = data['cardCount']
    
    # 添加到历史
    self.play_history.append({
        'round': self.current_round,
        'player_id': player_id,
        'player_name': data['playerName'],
        'action': 'pass',
        'card_type': None,
        'cards': [],
        'card_count': card_count,
        'timestamp': time.time()
    })
    
    # 更新玩家统计
    self._update_player_stats(player_id, 'pass', [], card_count)
    
    # 检查是否新一轮
    self._check_new_round()
```

### 3. 牌字符串解析

```python
def _parse_cards_string(self, cards_str):
    """
    解析牌字符串 "3♠、4♥、5♦" -> [{'value': '3', 'suit': '♠'}, ...]
    """
    if not cards_str or cards_str == '无':
        return []
    
    cards = []
    card_tokens = cards_str.split('、')
    
    for token in card_tokens:
        # 提取花色（最后一个字符）
        suit = token[-1]
        # 提取牌值（除了最后一个字符）
        value = token[:-1]
        
        cards.append({
            'value': value,
            'suit': suit
        })
    
    return cards
```

### 4. 数据查询接口

```python
def get_player_history(self, player_id, limit=None):
    """
    获取某个玩家的出牌历史
    """
    history = [h for h in self.play_history if h['player_id'] == player_id]
    if limit:
        return history[-limit:]
    return history

def get_recent_history(self, limit=10):
    """
    获取最近N轮的出牌记录
    """
    return self.play_history[-limit:]

def get_cards_played_by_player(self, player_id):
    """
    获取某玩家已出的所有牌
    """
    played = []
    for record in self.play_history:
        if record['player_id'] == player_id and record['action'] == 'play':
            played.extend(record['cards'])
    return played

def get_remaining_cards_count(self, player_id):
    """
    获取某玩家剩余牌数
    """
    stats = self.player_stats.get(player_id)
    return stats['cards_remaining'] if stats else 27

def get_cards_not_seen_yet(self):
    """
    获取尚未出现的牌（全局视角）
    """
    return self.cards_remaining.copy()
```

---

## 🎨 完整类框架

```python
class GameEventCollector:
    """游戏事件收集器"""
    
    def __init__(self, server_url='http://localhost:5000', my_player_id=2):
        self.server_url = server_url
        self.my_player_id = my_player_id
        
        # 数据存储
        self.play_history = []              # 完整出牌历史
        self.player_stats = {}              # 玩家统计
        self.cards_played = {}              # 已出牌统计
        self.cards_remaining = self._init_deck()  # 剩余牌
        
        # 状态
        self.current_round = 1
        self.stop_event = threading.Event()
        self.listener_thread = None
    
    def start(self):
        """启动事件监听"""
        self.listener_thread = Thread(target=self.listen_sse_events)
        self.listener_thread.daemon = True
        self.listener_thread.start()
    
    def stop(self):
        """停止监听"""
        self.stop_event.set()
    
    # ... 其他方法（如上所述）
```

---

## 🚀 使用示例

```python
# 创建收集器
collector = GameEventCollector(
    server_url='http://localhost:5000',
    my_player_id=2
)

# 启动监听
collector.start()

# 查询数据
history = collector.get_recent_history(limit=10)
opponent_cards = collector.get_cards_played_by_player(player_id=1)
remaining = collector.get_remaining_cards_count(player_id=3)

# 停止监听
collector.stop()
```

---

## 📊 数据流向

```
服务器SSE推送 → SSE监听器 → 事件解析 → 数据存储
                                           ↓
                                    查询接口
                                           ↓
                              分析AI层（第三部分）
```

---

## 🔍 关键技术点

### 1. SSE客户端库
```bash
# 需要安装
pip install sseclient-py
```

### 2. 线程安全
- 使用 `threading.Lock()` 保护共享数据
- 读写操作加锁

### 3. 断线重连
- 捕获连接异常
- 自动重连机制
- 指数退避策略

### 4. 内存管理
- 历史记录限制长度（如保留最近1000条）
- 定期清理旧数据

---

## ✅ 下一步

**第三部分**将详细设计：
1. 牌型推断AI - 数学算法与LLM分析
2. 风格分析AI - 对手行为模式识别
3. 局势评估AI - 胜率与策略建议

---

*最后更新: 2025-11-06*
*依赖第一部分：综述*
