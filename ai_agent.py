"""
掼蛋AI Agent示例
展示如何通过API与游戏服务器交互
"""

import requests
import time
import json
from typing import List, Dict

class GuandanAIAgent:
    def __init__(self, server_url='http://localhost:5000', player_id=1):
        self.server_url = server_url
        self.player_id = player_id
        self.game_history = []
        self.last_play = None
    
    def get_turn_info(self) -> Dict:
        """获取该玩家的回合信息"""
        url = f'{self.server_url}/game/turn/{self.player_id}'
        resp = requests.get(url)
        return resp.json()
    
    def get_hand(self) -> List[Dict]:
        """获取手牌"""
        url = f'{self.server_url}/game/player/{self.player_id}/hand'
        resp = requests.get(url)
        data = resp.json()
        return data['cards']
    
    def get_game_state(self) -> Dict:
        """获取游戏状态"""
        url = f'{self.server_url}/game/state'
        resp = requests.get(url)
        return resp.json()
    
    def play_cards(self, cards: List[Dict]) -> Dict:
        """出牌"""
        url = f'{self.server_url}/game/play'
        payload = {
            'playerId': self.player_id,
            'cards': cards
        }
        resp = requests.post(url, json=payload)
        return resp.json()
    
    def pass_turn(self) -> Dict:
        """过牌"""
        url = f'{self.server_url}/game/pass'
        payload = {'playerId': self.player_id}
        resp = requests.post(url, json=payload)
        return resp.json()
    
    def make_decision(self) -> bool:
        """
        做出决策
        返回: True=出牌成功, False=过牌或出牌失败
        """
        try:
            info = self.get_turn_info()
            
            # 不是我的回合
            if not info['isMyTurn']:
                print(f"[AI-{self.player_id}] 不是我的回合，等待...")
                return False
            
            hand = info['hand']
            last_play = info['lastPlay']
            
            print(f"[AI-{self.player_id}] 轮到我了！")
            print(f"  手牌数: {len(hand)}")
            print(f"  最后出牌: {last_play}")
            
            # 简单的AI策略：
            # 1. 首轮出最小的单牌
            # 2. 非首轮30%概率过牌，70%概率尝试压牌
            
            if not last_play or last_play['isPass']:
                # 首轮，出最小的单牌
                if hand:
                    card = hand[0]  # 已排序，最小的在前
                    result = self.play_cards([card])
                    if result['success']:
                        print(f"[AI-{self.player_id}] 出了: {card['value']}{card['suit']}")
                        return True
                    else:
                        print(f"[AI-{self.player_id}] 出牌失败: {result['message']}")
            else:
                # 非首轮
                import random
                if random.random() < 0.3:  # 30%过牌
                    result = self.pass_turn()
                    print(f"[AI-{self.player_id}] 选择过牌")
                    return False
                else:
                    # 尝试找大于上家的单牌
                    last_cards = last_play['cards']
                    last_value = last_cards[0]['sortValue']
                    
                    for card in hand:
                        if card['sortValue'] > last_value:
                            result = self.play_cards([card])
                            if result['success']:
                                print(f"[AI-{self.player_id}] 压牌: {card['value']}{card['suit']}")
                                return True
                    
                    # 没找到可以压的，过牌
                    result = self.pass_turn()
                    print(f"[AI-{self.player_id}] 无法压牌，选择过牌")
                    return False
        
        except Exception as e:
            print(f"[AI-{self.player_id}] 错误: {e}")
            return False
    
    def run(self, max_turns=100):
        """
        AI Agent主循环
        定期检查是否轮到自己，然后做出决策
        """
        print(f"[AI-{self.player_id}] AI Agent启动")
        turns = 0
        
        while turns < max_turns:
            try:
                info = self.get_turn_info()
                
                if info['isMyTurn']:
                    self.make_decision()
                
                # 每秒检查一次
                time.sleep(1)
                turns += 1
            
            except Exception as e:
                print(f"[AI-{self.player_id}] 连接错误: {e}")
                time.sleep(2)
                continue


def start_ai_agents():
    """启动多个AI Agent的示例"""
    import threading
    
    # 创建3个AI Agent（玩家1、2、3）
    agents = [
        GuandanAIAgent(player_id=1),
        GuandanAIAgent(player_id=2),
        GuandanAIAgent(player_id=3),
    ]
    
    threads = []
    for agent in agents:
        t = threading.Thread(target=agent.run, daemon=True)
        t.start()
        threads.append(t)
    
    print("所有AI Agent已启动")
    
    # 等待所有线程
    for t in threads:
        t.join()


if __name__ == '__main__':
    print("掼蛋 AI Agent 示例")
    print("=" * 50)
    print("使用方式:")
    print("1. 启动游戏服务器: python server.py")
    print("2. 打开游戏前端: index.html")
    print("3. 在前端点击'开始游戏'")
    print("4. 在另一个终端运行这个脚本: python ai_agent.py")
    print("=" * 50)
    
    # 等待用户准备
    input("按Enter键启动AI Agent...")
    
    # 启动AI Agent
    start_ai_agents()
