# 掼蛋游戏 - 服务器版本

这是一个基于Python Flask后端 + HTML5前端的掼蛋游戏。

## 项目结构

```
├── server.py           # Flask服务器（游戏逻辑）
├── game.js            # 前端游戏客户端（连接服务器）
├── index.html         # 游戏页面
├── style.css          # 样式文件
├── requirements.txt   # Python依赖
└── README.md          # 本文件
```

## 安装和运行

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
python server.py
```

服务器会在 `http://localhost:5000` 启动

### 3. 打开游戏

在浏览器中打开 `index.html` 文件

## API文档

### 1. 开始游戏
**POST** `/game/start`

初始化新游戏，发27张牌给每个玩家。

**响应示例：**
```json
{
    "success": true,
    "message": "游戏开始，已发牌",
    "currentPlayer": 0
}
```

### 2. 获取玩家手牌
**GET** `/game/player/{playerId}/hand`

获取某个玩家的所有手牌。

**响应示例：**
```json
{
    "playerId": 0,
    "cardCount": 27,
    "cards": [
        {"suit": "♠", "value": "2", "sortValue": 2},
        {"suit": "♥", "value": "3", "sortValue": 3}
    ]
}
```

### 3. 出牌
**POST** `/game/play`

玩家出牌，服务器会验证牌型、是否拥有这些牌、是否能压过上家。

**请求体：**
```json
{
    "playerId": 0,
    "cards": [
        {"suit": "♠", "value": "3", "sortValue": 3},
        {"suit": "♥", "value": "3", "sortValue": 3}
    ]
}
```

**响应示例（成功）：**
```json
{
    "success": true,
    "message": "出牌成功",
    "nextPlayer": 1
}
```

**响应示例（失败）：**
```json
{
    "success": false,
    "message": "无法压过上家的牌"
}
```

### 4. 过牌
**POST** `/game/pass`

玩家选择过牌。

**请求体：**
```json
{
    "playerId": 0
}
```

**响应示例：**
```json
{
    "success": true,
    "message": "已过牌",
    "nextPlayer": 1
}
```

### 5. 获取游戏状态
**GET** `/game/state`

获取当前游戏的完整状态。

**响应示例：**
```json
{
    "started": true,
    "currentPlayer": 0,
    "currentPlayerName": "我",
    "currentLevel": 2,
    "players": [
        {"id": 0, "name": "我", "isAI": false, "level": 2, "cardCount": 27},
        {"id": 1, "name": "右侧", "isAI": true, "level": 2, "cardCount": 27}
    ],
    "lastPlay": {
        "playerId": 0,
        "cards": [{"suit": "♠", "value": "3"}],
        "cardType": {"name": "单牌", "rank": 1}
    },
    "passCount": 0,
    "playHistory": [...]
}
```

### 6. 获取某玩家的回合信息
**GET** `/game/turn/{playerId}`

获取某个玩家当前的状态和决策信息（用于AI Agent）。

**响应示例：**
```json
{
    "playerId": 0,
    "isMyTurn": true,
    "currentPlayer": 0,
    "currentPlayerName": "我",
    "lastPlay": {...},
    "canPlay": true,
    "passCount": 0,
    "hand": [...],
    "gameState": {...}
}
```

### 7. 获取完整历史
**GET** `/game/history`

获取这一局所有的出牌历史。

**响应示例：**
```json
{
    "total": 5,
    "history": [
        {
            "playerName": "我",
            "playerId": 0,
            "cards": [...],
            "cardType": {"name": "单牌", "rank": 1},
            "isPass": false
        },
        {
            "playerName": "右侧",
            "playerId": 1,
            "cards": [],
            "cardType": null,
            "isPass": true
        }
    ]
}
```

## 架构设计说明

### 为什么采用这样的设计？

1. **前后端分离**
   - 服务器保存游戏状态，前端只是展示
   - AI Agent可以通过HTTP API访问游戏信息，做出决策
   - 便于日后添加多人网络对战

2. **API设计考虑**
   - `/game/turn/{playerId}` - 返回**该玩家视角**的信息
   - 每个玩家都能看到：自己的手牌、其他玩家的牌数、游戏历史
   - AI可以基于这些信息进行决策

3. **验证层**
   - 服务器验证是否是该玩家的回合
   - 验证玩家是否拥有出的牌
   - 验证牌型是否有效
   - 验证是否能压过上家

### AI Agent接入建议

1. **直接HTTP调用模式**
   ```python
   # AI Agent (Python)
   resp = requests.get('http://localhost:5000/game/turn/1')
   game_info = resp.json()
   
   # 分析游戏状态和历史
   decision = ai_agent.make_decision(game_info)
   
   # 执行决策
   requests.post('http://localhost:5000/game/play', json={
       'playerId': 1,
       'cards': decision['cards']
   })
   ```

2. **前端触发模式**
   - 前端定期轮询 `/game/turn/{playerId}`
   - 当轮到AI玩家时，前端调用AI服务
   - AI服务返回决策后，前端提交

## 当前支持的牌型

- ✅ 单牌
- ✅ 对子
- ✅ 三张
- ✅ 炸弹（4张及以上相同牌）

## TODO - 待实现的牌型

- ⏳ 顺子（5张及以上连续）
- ⏳ 连对（2对及以上连续的对子）
- ⏳ 三带二（三张+一对）
- ⏳ 逢人配（红桃当前等级牌作为万能牌）
- ⏳ 同花顺（同花色的顺子）

## 开发指南

### 添加新的牌型

编辑 `server.py` 中的 `GameState.validate_card_type()` 方法：

```python
def validate_card_type(self, cards):
    # ... 现有逻辑 ...
    
    # 新的牌型验证逻辑
    if len(cards) == 5:
        if self._is_straight(cards):
            return {'name': '顺子', 'rank': 4}
```

### 添加新的API

在 `server.py` 末尾添加：

```python
@app.route('/game/your-new-endpoint', methods=['GET/POST'])
def your_handler():
    # 你的逻辑
    return jsonify(result)
```

## 许可证

MIT
