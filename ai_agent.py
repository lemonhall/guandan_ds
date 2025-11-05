"""
掼蛋AI Agent示例
展示如何通过API与游戏服务器交互
"""

import requests
import time
import json
import threading
import signal
import sys
from typing import List, Dict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class GuandanAIAgent:
    def __init__(self, server_url='http://localhost:5000', player_id=1):
        self.server_url = server_url
        self.player_id = player_id
        self.game_history = []
        self.last_play = None
        self.stop_event = threading.Event()  # 用事件替代 running 标志
        
        # 创建带超时的 requests session
        self.session = requests.Session()
        self.session.timeout = 3  # 3秒超时
    
    def get_turn_info(self) -> Dict:
        """获取该玩家的回合信息"""
        # 检查是否已被请求停止
        if self.stop_event.is_set():
            raise Exception("已请求停止")
        
        url = f'{self.server_url}/game/turn/{self.player_id}'
        try:
            resp = self.session.get(url, timeout=3)
            resp.raise_for_status()
            data = resp.json()
            
            # 检查响应中是否有 error 字段
            if 'error' in data:
                raise Exception(f"服务器错误: {data['error']}")
            
            return data
        except requests.exceptions.ConnectionError:
            raise Exception("无法连接到服务器")
        except requests.exceptions.Timeout:
            raise Exception("服务器响应超时")
        except requests.exceptions.HTTPError as e:
            # 400 错误表示游戏还没开始
            if e.response.status_code == 400:
                raise Exception("游戏未开始")
            raise Exception(f"HTTP {e.response.status_code}")
        except Exception as e:
            raise Exception(f"获取回合信息失败: {e}")
    
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
            
            # 检查返回数据结构
            if not isinstance(info, dict) or 'isMyTurn' not in info:
                print(f"[AI-{self.player_id}] 错误: 无效的回合信息: {info}")
                return False
            
            # 不是我的回合
            if not info['isMyTurn']:
                print(f"[AI-{self.player_id}] 不是我的回合，等待...")
                return False
            
            hand = info.get('hand', [])
            last_play = info.get('lastPlay')
            
            print(f"[AI-{self.player_id}] 轮到我了！")
            print(f"  手牌数: {len(hand)}")
            print(f"  最后出牌: {last_play}")
            
            # 简单的AI策略：
            # 1. 首轮出最小的单牌
            # 2. 非首轮30%概率过牌，70%概率尝试压牌
            
            if not last_play or last_play.get('isPass', True):
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
        consecutive_errors = 0
        
        while turns < max_turns and not self.stop_event.is_set():
            try:
                # 先检查是否应该停止
                if self.stop_event.is_set():
                    break
                
                info = self.get_turn_info()
                consecutive_errors = 0  # 重置错误计数
                
                # 检查响应数据
                if not isinstance(info, dict) or 'isMyTurn' not in info:
                    if turns == 0 or turns % 10 == 0:  # 定期打印，避免日志过多
                        print(f"[AI-{self.player_id}] 等待游戏开始...")
                else:
                    if info['isMyTurn']:
                        self.make_decision()
                
                # 使用 wait 替代 sleep，支持被中断
                if self.stop_event.wait(1):  # 等待1秒或直到事件被设置
                    break
                turns += 1
            
            except Exception as e:
                error_msg = str(e)
                consecutive_errors += 1
                
                # 已请求停止
                if "已请求停止" in error_msg:
                    break
                
                # 游戏未开始
                if "游戏未开始" in error_msg:
                    if consecutive_errors <= 1:  # 只打印第一次
                        print(f"[AI-{self.player_id}] ⏳ 等待游戏开始...")
                # 连接错误
                elif "无法连接" in error_msg or "超时" in error_msg:
                    if consecutive_errors % 10 == 1:  # 每10次错误打印一次
                        print(f"[AI-{self.player_id}] ⚠️  {error_msg}")
                else:
                    print(f"[AI-{self.player_id}] ❌ {error_msg}")
                
                # 检查是否应该停止
                if self.stop_event.wait(2):  # 等待2秒或直到事件被设置
                    break
                turns += 1
        
        print(f"[AI-{self.player_id}] 🛑 AI Agent已停止")


def start_ai_agents():
    """启动多个AI Agent的示例"""
    global agents, threads
    
    # 创建3个AI Agent（玩家1、2、3）
    agents = [
        GuandanAIAgent(player_id=1),
        GuandanAIAgent(player_id=2),
        GuandanAIAgent(player_id=3),
    ]
    
    threads = []
    for agent in agents:
        t = threading.Thread(target=agent.run, daemon=False)  # 改为 daemon=False
        t.start()
        threads.append(t)
    
    print("所有AI Agent已启动")
    
    # 等待所有线程（会被 signal handler 中断）
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        pass


def signal_handler(signum, frame):
    """处理 Ctrl+C 信号"""
    print("\n\n🛑 正在关闭 AI Agent...")
    # 设置所有 agent 的 stop_event
    for agent in agents:
        agent.stop_event.set()
    
    # 等待线程结束（最多等待3秒）
    for t in threads:
        t.join(timeout=3)
    
    print("✅ 所有 AI Agent 已停止")
    sys.exit(0)


# 全局变量
agents = []
threads = []


if __name__ == '__main__':
    print("掼蛋 AI Agent 示例")
    print("=" * 50)
    print("使用方式:")
    print("1. 启动游戏服务器: python server.py")
    print("2. 打开游戏前端: index.html")
    print("3. 在前端点击'开始游戏'")
    print("4. 在另一个终端运行这个脚本: python ai_agent.py")
    print("=" * 50)
    print("按 Ctrl+C 停止 AI Agent")
    print("=" * 50)
    
    # 注册 Ctrl+C 信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    # 等待用户准备
    input("按Enter键启动AI Agent...")
    
    # 启动AI Agent
    start_ai_agents()
