"""
掼蛋AI Agent示例
展示如何通过API与游戏服务器交互
"""

import requests
import time
import json
import threading
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
        
        # 玩家位置映射
        self.position_map = {
            1: '右侧',
            2: '对家',
            3: '左侧'
        }
        self.position = self.position_map.get(player_id, f'玩家{player_id}')
    
    def _log(self, message):
        """打印带方位的日志"""
        print(f"[{self.position}] {message}", flush=True)
    
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
                self._log(f"错误: 无效的回合信息: {info}")
                return False
            
            # 不是我的回合
            if not info['isMyTurn']:
                self._log("不是我的回合，等待...")
                return False
            
            hand = info.get('hand', [])
            last_play = info.get('lastPlay')
            
            self._log("轮到我了！")
            self._log(f"  手牌数: {len(hand)}")
            self._log(f"  最后出牌: {last_play}")
            
            # 简单的AI策略：
            # 1. 首轮出最小的单牌
            # 2. 非首轮30%概率过牌，70%概率尝试压牌
            
            if not last_play or last_play.get('isPass', True):
                # 首轮，出最小的单牌
                if hand:
                    card = hand[0]  # 已排序，最小的在前
                    result = self.play_cards([card])
                    if result['success']:
                        self._log(f"出了: {card['value']}{card['suit']}")
                        return True
                    else:
                        self._log(f"出牌失败: {result['message']}")
            else:
                # 非首轮
                import random
                if random.random() < 0.3:  # 30%过牌
                    result = self.pass_turn()
                    self._log("选择过牌")
                    return False
                else:
                    # 尝试找大于上家的单牌
                    last_cards = last_play['cards']
                    last_value = last_cards[0]['sortValue']
                    
                    for card in hand:
                        if card['sortValue'] > last_value:
                            result = self.play_cards([card])
                            if result['success']:
                                self._log(f"压牌: {card['value']}{card['suit']}")
                                return True
                    
                    # 没找到可以压的，过牌
                    result = self.pass_turn()
                    self._log("无法压牌，选择过牌")
                    return False
        
        except Exception as e:
            self._log(f"错误: {e}")
            return False
    
    def run(self, max_turns=None):
        """
        AI Agent主循环
        定期检查是否轮到自己，然后做出决策
        max_turns: 最大轮数，None 表示无限运行
        """
        self._log("AI Agent启动")
        turns = 0
        consecutive_errors = 0
        
        while (max_turns is None or turns < max_turns) and not self.stop_event.is_set():
            try:
                # 先检查是否应该停止
                if self.stop_event.is_set():
                    break
                
                info = self.get_turn_info()
                consecutive_errors = 0  # 重置错误计数
                
                # 检查响应数据
                if not isinstance(info, dict) or 'isMyTurn' not in info:
                    if turns == 0 or turns % 10 == 0:  # 定期打印，避免日志过多
                        self._log("等待游戏开始...")
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
                        self._log("⏳ 等待游戏开始...")
                # 连接错误
                elif "无法连接" in error_msg or "超时" in error_msg:
                    if consecutive_errors % 10 == 1:  # 每10次错误打印一次
                        self._log(f"⚠️  {error_msg}")
                else:
                    self._log(f"❌ {error_msg}")
                
                # 检查是否应该停止
                if self.stop_event.wait(2):  # 等待2秒或直到事件被设置
                    break
                turns += 1
        
        self._log("🛑 AI Agent已停止")


def start_ai_agents():
    """启动多个AI Agent（不阻塞主线程）"""
    global agents, threads

    agents = [
        GuandanAIAgent(player_id=1),
        GuandanAIAgent(player_id=2),
        GuandanAIAgent(player_id=3),
    ]

    threads = []
    for i, agent in enumerate(agents):
        def run_agent_safe(ag=agent, idx=i):
            """安全的 agent 运行包装"""
            try:
                print(f"[启动] 第 {idx+1} 个 Agent 线程已启动", flush=True)
                ag.run()
            except Exception as e:
                print(f"[启动] 第 {idx+1} 个 Agent 线程异常: {e}", flush=True)
                import traceback
                traceback.print_exc()
        
        # 使用 daemon=True，这样在极端情况下主进程退出时线程不会阻塞退出
        t = threading.Thread(target=run_agent_safe, daemon=True)
        t.start()
        threads.append(t)
        print(f"[启动] 已启动第 {i+1} 个 Agent 线程", flush=True)

    print("所有AI Agent已启动（按 Ctrl+C 退出）", flush=True)


def shutdown_agents():
    """优雅关闭所有 AI Agent"""
    print("\n🛑 正在关闭 AI Agent...")
    for agent in agents:
        agent.stop_event.set()
    # 给予线程一次机会完成当前循环（最大等待 session timeout + 1s）
    for t in threads:
        t.join(timeout=5)
    print("✅ 所有 AI Agent 已停止")
    print("=" * 50)


# 全局容器
agents: List[GuandanAIAgent] = []
threads: List[threading.Thread] = []


if __name__ == '__main__':
    print("掼蛋 AI Agent 示例")
    print("=" * 50)
    print("使用方式:")
    print("1. 启动游戏服务器: python server.py")
    print("2. 打开游戏前端: index.html")
    print("3. 在前端点击'开始游戏'")
    print("4. 在另一个终端运行这个脚本: python ai_agent.py")
    print("=" * 50)
    print("按 Ctrl+C 停止 AI Agent（可能有最多 ~3 秒等待，取决于当前网络请求 timeout）")
    print("=" * 50, flush=True)

    input("按Enter键启动AI Agent...")
    print("正在启动 AI Agent...", flush=True)
    start_ai_agents()
    print("AI Agent 启动完成，等待游戏开始...", flush=True)

    try:
        # 主线程保持轻量循环，确保 KeyboardInterrupt 能被捕获
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown_agents()
