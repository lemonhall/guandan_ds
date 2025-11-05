"""
掼蛋游戏服务器 - Flask后端
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import random
import json
from enum import Enum
import os

# 获取当前目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
CORS(app)

# 全局游戏状态
game_state = None

class CardSuit(Enum):
    """花色"""
    SPADE = '♠'
    HEART = '♥'
    DIAMOND = '♦'
    CLUB = '♣'
    JOKER = 'Joker'

class Card:
    """牌的表示"""
    def __init__(self, suit, value, sort_value=None):
        self.suit = suit
        self.value = value
        # 用于排序的值
        self.sort_value = sort_value or self._get_sort_value(value)
    
    @staticmethod
    def _get_sort_value(value):
        value_map = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
            '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14,
            '小王': 14.5, '大王': 15
        }
        return value_map.get(value, 0)
    
    def to_dict(self):
        return {
            'suit': self.suit,
            'value': self.value,
            'sortValue': self.sort_value
        }
    
    def __repr__(self):
        return f"{self.value}{self.suit}"


class Player:
    """玩家"""
    def __init__(self, player_id, name, is_ai=False):
        self.id = player_id
        self.name = name
        self.is_ai = is_ai
        self.cards = []  # 手牌
        self.level = 2   # 当前等级
    
    def add_card(self, card):
        self.cards.append(card)
    
    def remove_card(self, card):
        """移除手牌中的一张牌"""
        for i, c in enumerate(self.cards):
            if c.suit == card['suit'] and c.value == card['value']:
                self.cards.pop(i)
                return True
        return False
    
    def has_cards(self, cards):
        """检查玩家是否拥有这些牌"""
        for card in cards:
            found = False
            for hand_card in self.cards:
                if hand_card.suit == card['suit'] and hand_card.value == card['value']:
                    found = True
                    break
            if not found:
                return False
        return True
    
    def sort_cards(self):
        """排序手牌"""
        self.cards.sort(key=lambda c: (c.sort_value, self._suit_order(c.suit)))
    
    @staticmethod
    def _suit_order(suit):
        order = {CardSuit.SPADE.value: 0, CardSuit.HEART.value: 1, 
                 CardSuit.DIAMOND.value: 2, CardSuit.CLUB.value: 3, CardSuit.JOKER.value: 4}
        return order.get(suit, 5)
    
    def to_dict(self, show_cards=False):
        return {
            'id': self.id,
            'name': self.name,
            'isAI': self.is_ai,
            'level': self.level,
            'cardCount': len(self.cards),
            'cards': [c.to_dict() for c in self.cards] if show_cards else []
        }


class PlayRecord:
    """出牌记录"""
    def __init__(self, player_id, cards, card_type=None, is_pass=False):
        self.player_id = player_id
        self.cards = cards
        self.card_type = card_type
        self.is_pass = is_pass
    
    def to_dict(self):
        return {
            'playerId': self.player_id,
            'cards': self.cards,
            'cardType': self.card_type,
            'isPass': self.is_pass
        }


class GameState:
    """游戏状态"""
    def __init__(self):
        self.players = [
            Player(0, '我', is_ai=False),
            Player(1, '右侧', is_ai=True),
            Player(2, '对家', is_ai=True),
            Player(3, '左侧', is_ai=True)
        ]
        self.current_player_id = 0
        self.started = False
        self.play_history = []  # 出牌历史
        self.last_play = None   # 最后一次出牌
        self.pass_count = 0     # 连续过牌数
        self.current_level = 2  # 当前打的等级
    
    def start_game(self):
        """开始游戏，发牌"""
        self.started = True
        self.play_history = []
        self.last_play = None
        self.pass_count = 0
        
        # 创建牌组（2副牌）
        deck = self._create_deck()
        
        # 洗牌
        random.shuffle(deck)
        
        # 发牌给每个玩家（每人27张）
        for i, player in enumerate(self.players):
            player.cards = deck[i*27:(i+1)*27]
            player.sort_cards()
        
        # 玩家先手
        self.current_player_id = 0
        
        return {
            'success': True,
            'message': '游戏开始，已发牌',
            'currentPlayer': self.current_player_id
        }
    
    def _create_deck(self):
        """创建2副牌"""
        suits = [CardSuit.SPADE.value, CardSuit.HEART.value, 
                 CardSuit.DIAMOND.value, CardSuit.CLUB.value]
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = []
        
        # 创建2副牌
        for _ in range(2):
            for suit in suits:
                for value in values:
                    deck.append(Card(suit, value))
            # 添加大小王
            deck.append(Card(CardSuit.JOKER.value, '小王'))
            deck.append(Card(CardSuit.JOKER.value, '大王'))
        
        return deck
    
    def get_player_hand(self, player_id):
        """获取玩家的手牌"""
        if not (0 <= player_id < len(self.players)):
            return None
        return [c.to_dict() for c in self.players[player_id].cards]
    
    def validate_card_type(self, cards):
        """验证牌型"""
        if not cards:
            return None
        
        # 单牌
        if len(cards) == 1:
            return {'name': '单牌', 'rank': 1}
        
        # 对子
        if len(cards) == 2:
            if cards[0]['value'] == cards[1]['value']:
                return {'name': '对子', 'rank': 2}
        
        # 三张
        if len(cards) == 3:
            if cards[0]['value'] == cards[1]['value'] == cards[2]['value']:
                return {'name': '三张', 'rank': 3}
        
        # 炸弹（4张及以上相同）
        if len(cards) >= 4:
            values = [c['value'] for c in cards]
            if len(set(values)) == 1:
                return {'name': f'炸弹({len(cards)}张)', 'rank': 10 + len(cards)}
        
        return None
    
    def can_beat(self, cards, card_type, last_play):
        """判断是否能压过上家的牌"""
        if not last_play:
            return True  # 首轮可以出任何有效牌型
        
        last_type = last_play['cardType']
        last_cards = last_play['cards']
        
        # 炸弹可以压任何非炸弹
        if card_type['rank'] >= 10 and last_type['rank'] < 10:
            return True
        
        # 同类型比大小
        if card_type['name'] == last_type['name']:
            return cards[0]['sortValue'] > last_cards[0]['sortValue']
        
        return False
    
    def play(self, player_id, cards):
        """执行出牌"""
        if not self.started:
            return {'success': False, 'message': '游戏未开始'}
        
        if player_id != self.current_player_id:
            return {'success': False, 'message': '不是你的回合'}
        
        player = self.players[player_id]
        
        # 检查玩家是否拥有这些牌
        if not player.has_cards(cards):
            return {'success': False, 'message': '你没有这些牌'}
        
        # 验证牌型
        card_type = self.validate_card_type(cards)
        if not card_type:
            return {'success': False, 'message': '无效的牌型'}
        
        # 如果不是首轮，检查是否能压过上家
        if self.last_play and not self.can_beat(cards, card_type, self.last_play):
            return {'success': False, 'message': '无法压过上家的牌'}
        
        # 执行出牌
        for card in cards:
            player.remove_card(card)
        
        # 更新游戏状态
        self.last_play = {
            'playerId': player_id,
            'cards': cards,
            'cardType': card_type
        }
        self.pass_count = 0
        
        # 记录到历史
        record = {
            'playerName': player.name,
            'playerId': player_id,
            'cards': cards,
            'cardType': card_type,
            'isPass': False
        }
        self.play_history.append(record)
        
        # 检查是否获胜
        if len(player.cards) == 0:
            return {
                'success': True,
                'message': f'{player.name} 获胜！',
                'winner': player.name,
                'gameOver': True
            }
        
        # 转到下一个玩家
        self._next_player()
        
        return {
            'success': True,
            'message': '出牌成功',
            'nextPlayer': self.current_player_id
        }
    
    def pass_turn(self, player_id):
        """过牌"""
        if not self.started:
            return {'success': False, 'message': '游戏未开始'}
        
        if player_id != self.current_player_id:
            return {'success': False, 'message': '不是你的回合'}
        
        player = self.players[player_id]
        self.pass_count += 1
        
        # 记录到历史
        record = {
            'playerName': player.name,
            'playerId': player_id,
            'cards': [],
            'cardType': None,
            'isPass': True
        }
        self.play_history.append(record)
        
        # 如果连续3个人过牌，新一轮开始
        if self.pass_count >= 3:
            self.last_play = None
            self.pass_count = 0
        
        # 转到下一个玩家
        self._next_player()
        
        return {
            'success': True,
            'message': '已过牌',
            'nextPlayer': self.current_player_id
        }
    
    def _next_player(self):
        """转到下一个玩家"""
        self.current_player_id = (self.current_player_id + 1) % len(self.players)
    
    def get_state(self):
        """获取当前游戏状态"""
        return {
            'started': self.started,
            'currentPlayer': self.current_player_id,
            'currentPlayerName': self.players[self.current_player_id].name if self.started else None,
            'currentLevel': self.current_level,
            'players': [p.to_dict() for p in self.players],
            'lastPlay': self.last_play,
            'passCount': self.pass_count,
            'playHistory': self.play_history[-10:]  # 最近10条记录
        }
    
    def get_turn_info(self, player_id):
        """获取某个玩家的回合信息"""
        is_my_turn = player_id == self.current_player_id
        
        return {
            'playerId': player_id,
            'isMyTurn': is_my_turn,
            'currentPlayer': self.current_player_id,
            'currentPlayerName': self.players[self.current_player_id].name,
            'lastPlay': self.last_play,
            'canPlay': is_my_turn and self.started,
            'passCount': self.pass_count,
            'hand': self.get_player_hand(player_id),
            'gameState': self.get_state()
        }


# API 路由

@app.route('/game/start', methods=['POST'])
def start_game():
    """开始新游戏"""
    global game_state
    game_state = GameState()
    result = game_state.start_game()
    return jsonify(result)


@app.route('/game/player/<int:player_id>/hand', methods=['GET'])
def get_player_hand(player_id):
    """获取玩家手牌"""
    if not game_state or not game_state.started:
        return jsonify({'error': '游戏未开始'}), 400
    
    hand = game_state.get_player_hand(player_id)
    if hand is None:
        return jsonify({'error': '玩家不存在'}), 404
    
    return jsonify({
        'playerId': player_id,
        'cardCount': len(hand),
        'cards': hand
    })


@app.route('/game/play', methods=['POST'])
def play():
    """出牌"""
    if not game_state or not game_state.started:
        return jsonify({'error': '游戏未开始'}), 400
    
    data = request.json
    player_id = data.get('playerId')
    cards = data.get('cards', [])
    
    if player_id is None:
        return jsonify({'error': 'playerId 必须'}), 400
    
    result = game_state.play(player_id, cards)
    return jsonify(result)


@app.route('/game/pass', methods=['POST'])
def pass_turn():
    """过牌"""
    if not game_state or not game_state.started:
        return jsonify({'error': '游戏未开始'}), 400
    
    data = request.json
    player_id = data.get('playerId')
    
    if player_id is None:
        return jsonify({'error': 'playerId 必须'}), 400
    
    result = game_state.pass_turn(player_id)
    return jsonify(result)


@app.route('/game/state', methods=['GET'])
def get_state():
    """获取游戏状态"""
    if not game_state:
        return jsonify({'error': '游戏未开始'}), 400
    
    return jsonify(game_state.get_state())


@app.route('/game/turn/<int:player_id>', methods=['GET'])
def get_turn(player_id):
    """获取玩家的回合信息"""
    if not game_state:
        return jsonify({'error': '游戏未开始'}), 400
    
    return jsonify(game_state.get_turn_info(player_id))


@app.route('/game/history', methods=['GET'])
def get_history():
    """获取完整的出牌历史"""
    if not game_state:
        return jsonify({'error': '游戏未开始'}), 400
    
    return jsonify({
        'total': len(game_state.play_history),
        'history': game_state.play_history
    })


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})


# 静态文件路由
@app.route('/')
def index():
    """提供首页"""
    return send_file(os.path.join(BASE_DIR, 'index.html'))


@app.route('/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    filepath = os.path.join(BASE_DIR, filename)
    if os.path.isfile(filepath):
        return send_file(filepath)
    return jsonify({'error': '文件未找到'}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
