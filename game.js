// 掼蛋游戏逻辑 - 服务器版本
class GuandanGame {
    constructor() {
        // 使用当前域名作为服务器地址，不需要每次改
        this.SERVER_URL = `${window.location.protocol}//${window.location.host}`;
        this.playerId = 0; // 当前玩家ID（人类）
        this.gameStarted = false;
        this.selectedCards = [];
        this.gameState = null;
        this.pollInterval = null;
        this.lastDisplayedPlayId = -1; // 追踪最后显示的出牌ID
        
        this.initEventListeners();
    }

    // 添加日志
    addLog(message, type = 'info') {
        const logContent = document.getElementById('gameLog');
        const logItem = document.createElement('div');
        logItem.className = `log-item ${type}`;
        logItem.textContent = message;
        logContent.appendChild(logItem);
        // 自动滚动到底部
        logContent.scrollTop = logContent.scrollHeight;
    }

    // 初始化事件监听
    initEventListeners() {
        document.getElementById('startBtn').addEventListener('click', () => this.startGame());
        document.getElementById('playBtn').addEventListener('click', () => this.playCards());
        document.getElementById('passBtn').addEventListener('click', () => this.pass());
    }

    // 开始游戏
    async startGame() {
        try {
            this.addLog('正在请求服务器开始游戏...', 'info');
            
            const response = await fetch(`${this.SERVER_URL}/game/start`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('服务器连接失败');
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.gameStarted = true;
                document.getElementById('startBtn').disabled = true;
                document.getElementById('roundInfo').textContent = '游戏进行中';
                this.addLog('✅ 游戏开始！', 'info');
                
                // 获取初始手牌
                await this.updatePlayerHand();
                await this.updateGameState();
                
                // 开始定期轮询游戏状态
                this.startPolling();
            } else {
                this.addLog(`❌ ${result.message}`, 'info');
            }
        } catch (error) {
            this.addLog(`❌ 错误: ${error.message}`, 'info');
            console.error(error);
        }
    }

    // 获取玩家手牌
    async updatePlayerHand() {
        try {
            const response = await fetch(
                `${this.SERVER_URL}/game/player/${this.playerId}/hand`
            );
            
            if (!response.ok) return;
            
            const data = await response.json();
            
            // 更新玩家对象
            const player = document.getElementById('bottomCards');
            player.innerHTML = '';
            
            data.cards.forEach((card, index) => {
                const cardDiv = this.createCardElement(card, index, data.cards);
                player.appendChild(cardDiv);
            });
            
            document.getElementById('bottomCount').textContent = data.cardCount;
        } catch (error) {
            console.error('获取手牌失败:', error);
        }
    }

    // 创建牌元素
    createCardElement(card, index, allCards) {
        const cardDiv = document.createElement('div');
        cardDiv.className = `card ${card.suit === '♥' || card.suit === '♦' ? 'red' : 'black'}`;
        cardDiv.innerHTML = `
            <div class="card-value">${card.value}</div>
            <div class="card-suit">${card.suit}</div>
        `;
        
        cardDiv.addEventListener('click', () => {
            this.toggleCardSelection(index, cardDiv, card);
        });
        
        return cardDiv;
    }

    // 切换牌的选择
    toggleCardSelection(index, cardDiv, card) {
        if (!this.gameStarted || !this.gameState?.isMyTurn) return;
        
        // 检查是否已选中
        const isSelected = this.selectedCards.some(c => 
            c.suit === card.suit && c.value === card.value
        );
        
        if (isSelected) {
            this.selectedCards = this.selectedCards.filter(c => 
                !(c.suit === card.suit && c.value === card.value)
            );
            cardDiv.classList.remove('selected');
        } else {
            this.selectedCards.push(card);
            cardDiv.classList.add('selected');
        }
        
        document.getElementById('playBtn').disabled = this.selectedCards.length === 0;
    }

    // 出牌
    async playCards() {
        if (this.selectedCards.length === 0) return;
        
        try {
            // 生成牌的显示字符串
            const cardStr = this.selectedCards
                .map(c => `${c.value}${c.suit}`)
                .join('、');
            
            const response = await fetch(`${this.SERVER_URL}/game/play`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    playerId: this.playerId,
                    cards: this.selectedCards
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 获取出牌后的游戏状态来显示牌型
                await this.updateGameState();
                const cardType = this.gameState?.lastPlay?.cardType?.name || '单牌';
                this.addLog(`✅ 我出了 ${cardType}: ${cardStr}`, 'play');
                
                if (result.gameOver && result.winner) {
                    this.addLog(`🎉 ${result.winner} 获胜！游戏结束！`, 'info');
                    this.endGame();
                    return;
                }
                
                this.selectedCards = [];
                document.getElementById('playBtn').disabled = true;
                await this.updatePlayerHand();
                await this.updateGameState();
            } else {
                this.addLog(`❌ 出牌失败: ${result.message}`, 'info');
            }
        } catch (error) {
            this.addLog(`❌ 错误: ${error.message}`, 'info');
            console.error(error);
        }
    }

    // 过牌
    async pass() {
        try {
            const response = await fetch(`${this.SERVER_URL}/game/pass`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    playerId: this.playerId
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addLog('我过了', 'pass');
                await this.updateGameState();
            } else {
                this.addLog(`❌ 错误: ${result.message}`, 'info');
            }
        } catch (error) {
            this.addLog(`❌ 错误: ${error.message}`, 'info');
            console.error(error);
        }
    }

    // 更新游戏状态
    async updateGameState() {
        try {
            const response = await fetch(
                `${this.SERVER_URL}/game/turn/${this.playerId}`
            );
            
            if (!response.ok) return;
            
            const data = await response.json();
            this.gameState = data;
            
            // 更新UI
            document.getElementById('roundInfo').textContent = `${data.currentPlayerName}的回合`;
            
            // 更新所有玩家的牌数
            if (data.gameState && data.gameState.players) {
                const playerMapping = {
                    0: 'bottomCount',
                    1: 'rightCount',
                    2: 'topCount',
                    3: 'leftCount'
                };
                
                data.gameState.players.forEach(p => {
                    const elementId = playerMapping[p.id];
                    if (elementId) {
                        document.getElementById(elementId).textContent = p.cardCount;
                    }
                });
            }
            
            // 更新出牌显示
            if (data.lastPlay) {
                this.displayPlayedCards(data.lastPlay);
                
                // 检查游戏历史中是否有新的出牌（来自其他玩家）
                if (data.gameState && data.gameState.playHistory) {
                    const history = data.gameState.playHistory;
                    if (history.length > this.lastDisplayedPlayId) {
                        // 有新的出牌记录
                        for (let i = this.lastDisplayedPlayId + 1; i < history.length; i++) {
                            const record = history[i];
                            if (record.playerId !== this.playerId) {  // 不显示自己的
                                if (record.isPass) {
                                    this.addLog(`${record.playerName} 过了`, 'pass');
                                } else {
                                    const cardStr = record.cards
                                        .map(c => `${c.value}${c.suit}`)
                                        .join('、');
                                    const cardType = record.cardType?.name || '出牌';
                                    this.addLog(`${record.playerName} 出了 ${cardType}: ${cardStr}`, 'play');
                                }
                            }
                        }
                        this.lastDisplayedPlayId = history.length - 1;
                    }
                }
            }
            
            // 更新按钮状态
            document.getElementById('passBtn').disabled = !data.canPlay;
            document.getElementById('playBtn').disabled = this.selectedCards.length === 0 || !data.canPlay;
            
        } catch (error) {
            console.error('更新游戏状态失败:', error);
        }
    }

    // 显示出的牌
    displayPlayedCards(lastPlay) {
        const playedCardsDiv = document.getElementById('playedCards');
        const playedInfoDiv = document.getElementById('playedInfo');
        
        playedCardsDiv.innerHTML = '';
        
        if (!lastPlay.isPass && lastPlay.cards.length > 0) {
            lastPlay.cards.forEach(card => {
                const cardDiv = document.createElement('div');
                cardDiv.className = `card ${card.suit === '♥' || card.suit === '♦' ? 'red' : 'black'}`;
                cardDiv.innerHTML = `
                    <div class="card-value">${card.value}</div>
                    <div class="card-suit">${card.suit}</div>
                `;
                playedCardsDiv.appendChild(cardDiv);
            });
        }
        
        if (lastPlay.isPass) {
            playedInfoDiv.textContent = `${this.getPlayerName(lastPlay.playerId)} 过了`;
        } else {
            playedInfoDiv.textContent = `${this.getPlayerName(lastPlay.playerId)} 出了 ${lastPlay.cardType?.name || ''}`;
        }
    }

    // 获取玩家名称
    getPlayerName(playerId) {
        const names = ['我', '右侧', '对家', '左侧'];
        return names[playerId] || '未知';
    }

    // 开始定期轮询
    startPolling() {
        // 每5秒更新一次游戏状态（减少服务器压力）
        this.pollInterval = setInterval(async () => {
            if (this.gameStarted) {
                await this.updateGameState();
            }
        }, 2000);
    }

    // 结束游戏
    endGame() {
        this.gameStarted = false;
        document.getElementById('startBtn').disabled = false;
        document.getElementById('playBtn').disabled = true;
        document.getElementById('passBtn').disabled = true;
        
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
    }
}

// 初始化游戏
var game = new GuandanGame();
