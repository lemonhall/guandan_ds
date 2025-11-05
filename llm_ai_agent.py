"""
掼蛋 LLM AI Agent - 使用 Deepseek 或其他 LLM 驱动的 AI
"""

import requests
import time
import json
import threading
import sys
import os
from typing import List, Dict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from openai import OpenAI

class LLMGuandanAIAgent:
    def __init__(self, server_url='http://localhost:5000', player_id=2, 
                 api_key=None, api_base=None, model='deepseek-chat'):
        self.server_url = server_url
        self.player_id = player_id
        self.game_history = []
        self.last_play = None
        self.stop_event = threading.Event()
        
        # 创建带超时的 requests session
        self.session = requests.Session()
        self.session.timeout = 3
        
        # 玩家位置映射
        self.position_map = {
            1: '右侧',
            2: '对家',
            3: '左侧'
        }
        self.position = self.position_map.get(player_id, f'玩家{player_id}')
        
        # 初始化 LLM 客户端
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.api_base = api_base or os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com')
        self.model = model
        
        if not self.api_key:
            raise ValueError("需要提供 DEEPSEEK_API_KEY 环境变量或 api_key 参数")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
        
        # 可配置的延迟
        self.poll_interval = 0.1
        self.error_retry_interval = 0.5
        
        self._log(f"✅ LLM AI Agent 初始化完成 (model={model}, position={self.position})")
    
    def _log(self, message):
        """打印带方位的日志"""
        print(f"[{self.position}(LLM)] {message}", flush=True)
    
    def get_turn_info(self) -> Dict:
        """获取该玩家的回合信息"""
        if self.stop_event.is_set():
            raise Exception("已请求停止")
        
        url = f'{self.server_url}/game/turn/{self.player_id}'
        try:
            resp = self.session.get(url, timeout=3)
            resp.raise_for_status()
            data = resp.json()
            
            if 'error' in data:
                raise Exception(f"服务器错误: {data['error']}")
            
            return data
        except requests.exceptions.ConnectionError:
            raise Exception("无法连接到服务器")
        except requests.exceptions.Timeout:
            raise Exception("服务器响应超时")
        except requests.exceptions.HTTPError as e:
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
    
    def format_cards_for_llm(self, cards: List[Dict]) -> str:
        """格式化牌组给 LLM"""
        if not cards:
            return "无"
        return "、".join([f"{c['value']}{c['suit']}" for c in cards])
    
    def get_llm_decision(self, hand: List[Dict], last_play: Dict) -> str:
        """
        使用 LLM 做决策
        返回: 决策 ('play', 'pass', 或具体的牌组)
        """
        try:
            # 格式化手牌
            hand_str = self.format_cards_for_llm(hand)
            
            # 格式化上家出牌
            if last_play and not last_play.get('isPass', True):
                last_card_type = last_play['cardType']['name']
                last_cards_str = self.format_cards_for_llm(last_play['cards'])
                opponent_play = f"{last_card_type}: {last_cards_str}"
            else:
                opponent_play = "新一轮（首家出牌）"
            
            # 构建 prompt
            prompt = f"""你是一个掼蛋卡牌游戏的 AI 玩家。掼蛋是一个中国的四人纸牌游戏。

当前手牌: {hand_str}

对手最后出的牌: {opponent_play}

规则说明:
- 单牌可以压单牌（点数更大）
- 对子可以压对子（点数更大）
- 三张可以压三张（点数更大）
- 炸弹（4张及以上相同的牌）可以压任何其他牌型
- 不同牌型之间不能比较（除非你用炸弹）
- 牌的大小顺序: 3 < 4 < 5 < 6 < 7 < 8 < 9 < 10 < J < Q < K < A < 2 < 小王 < 大王

根据上述规则，决策如下：
1. 如果能压过对手，请选择最优的牌（尽量用小牌，节约大牌）
2. 如果无法压过对手，选择过牌
3. 如果是新一轮，出一个最小的单牌或对子

请直接回答:
- 如果过牌，回答: "过牌"
- 如果出牌，回答: "出牌: X X X" (用中文数字或花色字符，例如: "出牌: 3♠ 4♥ 5♦")

注意: 只回答一行，不要解释理由！"""

            # 调用 LLM
            response = self.client.messages.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            decision_text = response.choices[0].message.content.strip()
            self._log(f"LLM 决策: {decision_text}")
            return decision_text
        
        except Exception as e:
            self._log(f"❌ LLM 调用失败: {e}")
            return "过牌"  # 出错时默认过牌
    
    def parse_llm_decision(self, decision_text: str, hand: List[Dict]) -> tuple:
        """
        解析 LLM 的决策文本
        返回: (action, cards) 其中 action 是 'play' 或 'pass'，cards 是要出的牌列表
        """
        if "过牌" in decision_text:
            return ("pass", [])
        
        if "出牌:" in decision_text or "出牌：" in decision_text:
            # 提取出牌的牌面
            cards_str = decision_text.split("出牌")[1].strip().replace(":", "").replace("：", "").strip()
            
            # 尝试匹配手牌
            selected_cards = []
            
            # 分割牌
            card_tokens = cards_str.replace("、", " ").replace("，", " ").split()
            
            for token in card_tokens:
                if not token:
                    continue
                
                # 提取值和花色
                value = token[:-1] if len(token) > 1 else token
                suit = token[-1] if len(token) > 0 else None
                
                # 在手牌中查找
                for card in hand:
                    if card['value'] == value and card['suit'] == suit and card not in selected_cards:
                        selected_cards.append(card)
                        break
            
            if selected_cards:
                return ("play", selected_cards)
        
        # 默认过牌
        return ("pass", [])
    
    def make_decision(self) -> bool:
        """做出决策"""
        try:
            info = self.get_turn_info()
            
            if not isinstance(info, dict) or 'isMyTurn' not in info:
                self._log(f"错误: 无效的回合信息")
                return False
            
            if not info['isMyTurn']:
                self._log("不是我的回合，等待...")
                return False
            
            hand = info.get('hand', [])
            last_play = info.get('lastPlay')
            
            self._log(f"轮到我了！手牌数: {len(hand)}")
            
            # 使用 LLM 做决策
            decision_text = self.get_llm_decision(hand, last_play)
            action, cards = self.parse_llm_decision(decision_text, hand)
            
            if action == "pass":
                result = self.pass_turn()
                self._log("选择过牌")
                return False
            elif action == "play" and cards:
                card_str = self.format_cards_for_llm(cards)
                result = self.play_cards(cards)
                
                if result['success']:
                    card_type = result.get('cardType', {}).get('name', '?')
                    self._log(f"✅ 出了 {card_type}: {card_str}")
                    return True
                else:
                    self._log(f"❌ 出牌失败: {result.get('message', '未知错误')}")
                    # 出牌失败就过牌
                    self.pass_turn()
                    return False
            else:
                # 无法解析，过牌
                result = self.pass_turn()
                self._log("无法解析 LLM 决策，选择过牌")
                return False
        
        except Exception as e:
            self._log(f"错误: {e}")
            return False
    
    def run(self, max_turns=None):
        """AI Agent 主循环"""
        self._log("LLM AI Agent 启动")
        turns = 0
        consecutive_errors = 0
        
        while (max_turns is None or turns < max_turns) and not self.stop_event.is_set():
            try:
                if self.stop_event.is_set():
                    break
                
                info = self.get_turn_info()
                consecutive_errors = 0
                
                if not isinstance(info, dict) or 'isMyTurn' not in info:
                    if turns == 0 or turns % 10 == 0:
                        self._log("等待游戏开始...")
                else:
                    if info['isMyTurn']:
                        self.make_decision()
                
                if self.stop_event.wait(self.poll_interval):
                    break
                turns += 1
            
            except Exception as e:
                error_msg = str(e)
                consecutive_errors += 1
                
                if "已请求停止" in error_msg:
                    break
                
                if "游戏未开始" in error_msg:
                    if consecutive_errors <= 1:
                        self._log("⏳ 等待游戏开始...")
                elif "无法连接" in error_msg or "超时" in error_msg:
                    if consecutive_errors % 10 == 1:
                        self._log(f"⚠️  {error_msg}")
                else:
                    self._log(f"❌ {error_msg}")
                
                if self.stop_event.wait(self.error_retry_interval):
                    break
                turns += 1
        
        self._log("🛑 LLM AI Agent 已停止")
