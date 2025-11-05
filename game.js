// 掼蛋游戏逻辑
class GuandanGame {
    constructor() {
        this.players = [
            { id: 0, name: '我', cards: [], isAI: false, level: 2 },
            { id: 1, name: '右侧', cards: [], isAI: true, level: 2 },
            { id: 2, name: '对家', cards: [], isAI: true, level: 2 },
            { id: 3, name: '左侧', cards: [], isAI: true, level: 2 }
        ];
        this.currentPlayer = 0;
        this.lastPlay = null;
        this.passCount = 0;
        this.selectedCards = [];
        this.gameStarted = false;
        this.currentLevel = 2; // 当前打的等级
        
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

    // 创建牌组（2副牌）
    createDeck() {
        const suits = ['♠', '♥', '♦', '♣'];
        const values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
        const deck = [];

        // 创建两副牌
        for (let i = 0; i < 2; i++) {
            for (let suit of suits) {
                for (let value of values) {
                    deck.push({
                        suit: suit,
                        value: value,
                        isRed: suit === '♥' || suit === '♦',
                        sortValue: this.getCardSortValue(value)
                    });
                }
            }
            // 添加大小王
            deck.push({ suit: 'Joker', value: '小王', isRed: true, sortValue: 14 });
            deck.push({ suit: 'Joker', value: '大王', isRed: true, sortValue: 15 });
        }

        return deck;
    }

    // 获取牌的排序值
    getCardSortValue(value) {
        const valueMap = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
            '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        };
        return valueMap[value] || 0;
    }

    // 洗牌
    shuffle(deck) {
        for (let i = deck.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [deck[i], deck[j]] = [deck[j], deck[i]];
        }
        return deck;
    }

    // 开始游戏
    startGame() {
        this.gameStarted = true;
        document.getElementById('startBtn').disabled = true;
        document.getElementById('roundInfo').textContent = '游戏进行中';
        this.addLog('游戏开始！', 'info');
        this.addLog('正在发牌...', 'info');

        // 创建并洗牌
        let deck = this.createDeck();
        deck = this.shuffle(deck);

        // 发牌（每人27张）
        for (let i = 0; i < 4; i++) {
            this.players[i].cards = deck.splice(0, 27);
            this.sortCards(this.players[i].cards);
        }

        // 渲染所有玩家的牌
        this.renderAllPlayers();
        
        // 玩家先手
        this.currentPlayer = 0;
        this.updateTurnInfo();
    }

    // 排序手牌
    sortCards(cards) {
        cards.sort((a, b) => {
            if (a.sortValue !== b.sortValue) {
                return a.sortValue - b.sortValue;
            }
            const suitOrder = { '♠': 0, '♥': 1, '♦': 2, '♣': 3, 'Joker': 4 };
            return suitOrder[a.suit] - suitOrder[b.suit];
        });
    }

    // 渲染所有玩家
    renderAllPlayers() {
        // 渲染玩家（下方）
        this.renderPlayerCards(0, 'bottomCards', false);
        
        // 渲染AI玩家（显示牌背）
        this.renderPlayerCards(1, 'rightCards', true);
        this.renderPlayerCards(2, 'topCards', true);
        this.renderPlayerCards(3, 'leftCards', true);

        // 更新牌数
        this.updateCardCounts();
    }

    // 渲染玩家手牌
    renderPlayerCards(playerId, containerId, isCardBack) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        
        const player = this.players[playerId];
        
        player.cards.forEach((card, index) => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'card';
            
            if (isCardBack) {
                cardDiv.classList.add('card-back');
                cardDiv.innerHTML = '?';
            } else {
                cardDiv.classList.add(card.isRed ? 'red' : 'black');
                cardDiv.innerHTML = `
                    <div class="card-value">${card.value}</div>
                    <div class="card-suit">${card.suit}</div>
                `;
                
                // 玩家的牌可以点击选择
                if (playerId === 0) {
                    cardDiv.addEventListener('click', () => this.toggleCardSelection(index, cardDiv));
                }
            }
            
            container.appendChild(cardDiv);
        });
    }

    // 切换牌的选择状态
    toggleCardSelection(index, cardDiv) {
        if (!this.gameStarted || this.currentPlayer !== 0) return;

        if (this.selectedCards.includes(index)) {
            this.selectedCards = this.selectedCards.filter(i => i !== index);
            cardDiv.classList.remove('selected');
        } else {
            this.selectedCards.push(index);
            cardDiv.classList.add('selected');
        }

        // 更新出牌按钮状态
        document.getElementById('playBtn').disabled = this.selectedCards.length === 0;
    }

    // 出牌
    playCards() {
        if (this.selectedCards.length === 0) return;

        const player = this.players[0];
        const cards = this.selectedCards.map(i => player.cards[i]);
        
        // 验证牌型
        const cardType = this.validateCardType(cards);
        if (!cardType) {
            alert('无效的牌型！');
            return;
        }

        // 如果不是首轮，需要验证是否能压过上家的牌
        if (this.lastPlay && !this.canBeat(cards, cardType, this.lastPlay)) {
            alert('无法压过上家的牌！');
            return;
        }

        // 出牌
        this.executePlay(0, cards, cardType);
    }

    // 执行出牌
    executePlay(playerId, cards, cardType) {
        const player = this.players[playerId];
        
        // 从手牌中移除
        cards.forEach(card => {
            const index = player.cards.findIndex(c => c.suit === card.suit && c.value === card.value);
            if (index > -1) player.cards.splice(index, 1);
        });

        // 更新最后出牌
        this.lastPlay = {
            playerId: playerId,
            cards: cards,
            type: cardType
        };
        this.passCount = 0;

        // 显示出的牌
        this.displayPlayedCards(playerId, cards, cardType);
        
        // 添加到日志
        const cardStr = cards.map(c => c.value + c.suit).join('');
        this.addLog(`${player.name} 出了 ${cardType.name}: ${cardStr}`, 'play');

        // 清空选择
        this.selectedCards = [];

        // 检查是否获胜
        if (player.cards.length === 0) {
            alert(`${player.name} 获胜！`);
            this.addLog(`🎉 ${player.name} 获胜！游戏结束！`, 'info');
            this.endGame();
            return;
        }

        // 更新显示
        this.renderAllPlayers();

        // 下一个玩家
        this.nextPlayer();
    }

    // 显示出的牌
    displayPlayedCards(playerId, cards, cardType) {
        const playedCardsDiv = document.getElementById('playedCards');
        const playedInfoDiv = document.getElementById('playedInfo');
        
        playedCardsDiv.innerHTML = '';
        cards.forEach(card => {
            const cardDiv = document.createElement('div');
            cardDiv.className = `card ${card.isRed ? 'red' : 'black'}`;
            cardDiv.innerHTML = `
                <div class="card-value">${card.value}</div>
                <div class="card-suit">${card.suit}</div>
            `;
            playedCardsDiv.appendChild(cardDiv);
        });

        playedInfoDiv.textContent = `${this.players[playerId].name} 出了 ${cardType.name}`;
    }

    // 过牌
    pass() {
        this.passCount++;
        this.addLog(`${this.players[this.currentPlayer].name} 过`, 'pass');
        
        // 如果连续3个人过牌，新一轮开始
        if (this.passCount >= 3) {
            this.lastPlay = null;
            document.getElementById('playedInfo').textContent = '新一轮开始';
            this.addLog('新一轮开始', 'info');
        }

        this.nextPlayer();
    }

    // 下一个玩家
    nextPlayer() {
        this.currentPlayer = (this.currentPlayer + 1) % 4;
        this.updateTurnInfo();

        // 如果是AI玩家，自动出牌
        if (this.players[this.currentPlayer].isAI) {
            setTimeout(() => this.aiPlay(), 1000);
        } else {
            // 玩家回合，启用按钮
            document.getElementById('playBtn').disabled = true;
            document.getElementById('passBtn').disabled = false;
        }
    }

    // AI出牌逻辑（简单实现）
    aiPlay() {
        const player = this.players[this.currentPlayer];
        
        // 30%概率过牌（如果不是首轮）
        if (this.lastPlay && Math.random() < 0.3) {
            this.pass();
            return;
        }

        // 尝试找到可以出的牌
        let cards = this.findAIPlayableCards(player.cards);
        
        if (cards.length > 0) {
            const cardType = this.validateCardType(cards);
            this.executePlay(this.currentPlayer, cards, cardType);
        } else {
            this.pass();
        }
    }

    // 查找AI可以出的牌（简化版）
    findAIPlayableCards(cards) {
        if (!this.lastPlay) {
            // 首轮，出最小的单牌
            return [cards[0]];
        }

        const lastType = this.lastPlay.type;
        
        // 尝试找同样类型但更大的牌
        if (lastType.name === '单牌') {
            for (let card of cards) {
                if (card.sortValue > this.lastPlay.cards[0].sortValue) {
                    return [card];
                }
            }
        }

        return [];
    }

    // 验证牌型
    validateCardType(cards) {
        if (cards.length === 0) return null;

        // 单牌
        if (cards.length === 1) {
            return { name: '单牌', rank: 1 };
        }

        // 对子
        if (cards.length === 2 && cards[0].value === cards[1].value) {
            return { name: '对子', rank: 2 };
        }

        // 三张
        if (cards.length === 3 && cards[0].value === cards[1].value && cards[1].value === cards[2].value) {
            return { name: '三张', rank: 3 };
        }

        // 炸弹（4张及以上相同）
        if (cards.length >= 4) {
            const allSame = cards.every(c => c.value === cards[0].value);
            if (allSame) {
                return { name: `炸弹(${cards.length}张)`, rank: 10 + cards.length };
            }
        }

        return null;
    }

    // 判断是否能压过上家的牌
    canBeat(cards, cardType, lastPlay) {
        // 炸弹可以压任何非炸弹
        if (cardType.rank >= 10 && lastPlay.type.rank < 10) {
            return true;
        }

        // 同类型比大小
        if (cardType.name === lastPlay.type.name) {
            return cards[0].sortValue > lastPlay.cards[0].sortValue;
        }

        return false;
    }

    // 更新回合信息
    updateTurnInfo() {
        const player = this.players[this.currentPlayer];
        document.getElementById('roundInfo').textContent = `${player.name}的回合`;
    }

    // 更新牌数显示
    updateCardCounts() {
        document.getElementById('bottomCount').textContent = this.players[0].cards.length;
        document.getElementById('rightCount').textContent = this.players[1].cards.length;
        document.getElementById('topCount').textContent = this.players[2].cards.length;
        document.getElementById('leftCount').textContent = this.players[3].cards.length;
    }

    // 结束游戏
    endGame() {
        this.gameStarted = false;
        document.getElementById('startBtn').disabled = false;
        document.getElementById('playBtn').disabled = true;
        document.getElementById('passBtn').disabled = true;
    }
}

// 初始化游戏
const game = new GuandanGame();
