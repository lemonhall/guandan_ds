# 掼蛋游戏 - 快速开始

## 一键启动（推荐）

### Windows
```bash
.\run_server.ps1
```

### Linux/Mac
```bash
./run_server.sh
```

然后在浏览器打开 `http://localhost:5000`

---

## 手动启动

## 方式1：本地单机版（推荐新手）

### 步骤1：激活虚拟环境
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 步骤2：启动服务器
```bash
python server.py
```

你会看到输出：
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### 步骤3：打开游戏
在浏览器中打开：
```
http://localhost:5000
```

### 步骤4：开始游戏
1. 点击"开始游戏"按钮 
2. 你的手牌会显示在下方
3. 选择要出的牌，点击"出牌"
4. 3个AI对手会自动出牌

## 方式2：AI Agent方式（推荐开发者）

这种方式适合测试自定义的AI Agent逻辑。

### 步骤1：启动游戏服务器
终端1：
```bash
python server.py
```

### 步骤2：启动AI Agent
终端2：
```bash
python ai_agent.py
```

按Enter键启动AI Agent。你会看到：
```
[AI-1] AI Agent启动
[AI-2] AI Agent启动
[AI-3] AI Agent启动
```

### 步骤3：打开游戏前端
在浏览器中打开 `index.html`

### 步骤4：开始游戏
1. 点击"开始游戏"
2. 你可以出牌或过牌，3个AI Agent会同时行动

## API测试

### 用curl测试API

启动服务器后，可以在另一个终端测试：

```bash
# 1. 开始游戏
curl -X POST http://localhost:5000/game/start

# 2. 获取玩家0的手牌
curl http://localhost:5000/game/player/0/hand

# 3. 出牌（示例：出一张3）
curl -X POST http://localhost:5000/game/play \
  -H "Content-Type: application/json" \
  -d '{
    "playerId": 0,
    "cards": [{"suit": "♠", "value": "3", "sortValue": 3}]
  }'

# 4. 过牌
curl -X POST http://localhost:5000/game/pass \
  -H "Content-Type: application/json" \
  -d '{"playerId": 0}'

# 5. 获取游戏状态
curl http://localhost:5000/game/state

# 6. 获取玩家0的回合信息
curl http://localhost:5000/game/turn/0

# 7. 获取历史
curl http://localhost:5000/game/history
```

## 常见问题

### Q: 游戏连接不上服务器？
A: 确保服务器正在运行，检查 `game.js` 中的 `SERVER_URL` 是否正确

### Q: AI Agent无法连接？
A: 
1. 确保服务器在运行
2. 确保游戏已开始（前端点击了"开始游戏"）
3. 检查防火墙设置

### Q: 如何自定义AI逻辑？
A: 编辑 `ai_agent.py` 中的 `make_decision()` 方法

### Q: 支持多人网络游戏吗？
A: 架构已支持，但前端和AI Agent还需要完善以支持真实的多人网络模式

## 文件说明

| 文件 | 说明 |
|------|------|
| `server.py` | Flask后端服务器，包含游戏逻辑 |
| `game.js` | 前端游戏客户端代码 |
| `index.html` | 游戏主页面 |
| `style.css` | 游戏样式 |
| `ai_agent.py` | AI Agent示例代码 |
| `requirements.txt` | Python依赖列表 |
| `README.md` | API文档 |

## 后续改进方向

- [ ] 支持LLM驱动的AI（接入OpenAI/Claude等）
- [ ] WebSocket支持，减少轮询延迟
- [ ] 更多牌型支持（顺子、连对、三带二等）
- [ ] 等级升级系统
- [ ] 逢人配规则实现
- [ ] 游戏录像功能
- [ ] 排行榜系统

祝玩得开心！🎮
