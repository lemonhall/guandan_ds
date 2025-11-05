"""
快速测试脚本 - 验证API功能
"""

import requests
import json
import time

BASE_URL = 'http://localhost:5000'

def test_health():
    """测试服务器是否在线"""
    try:
        resp = requests.get(f'{BASE_URL}/health')
        print(f"✅ 服务器在线: {resp.json()}")
        return True
    except Exception as e:
        print(f"❌ 服务器离线: {e}")
        return False

def test_static_files():
    """测试静态文件是否能访问"""
    files_to_test = ['index.html', 'game.js', 'style.css']
    
    for file in files_to_test:
        try:
            resp = requests.get(f'{BASE_URL}/{file}')
            if resp.status_code == 200:
                size = len(resp.content)
                print(f"✅ {file} ({size} bytes)")
            else:
                print(f"❌ {file} - HTTP {resp.status_code}")
        except Exception as e:
            print(f"❌ {file} - {e}")

def test_game_flow():
    """测试游戏流程"""
    print("\n=== 游戏流程测试 ===")
    
    # 1. 开始游戏
    print("1. 开始游戏...")
    resp = requests.post(f'{BASE_URL}/game/start')
    if resp.status_code != 200:
        print(f"❌ 开始游戏失败: {resp.text}")
        return
    
    result = resp.json()
    print(f"✅ {result['message']}")
    
    # 2. 获取玩家手牌
    print("2. 获取玩家手牌...")
    resp = requests.get(f'{BASE_URL}/game/player/0/hand')
    if resp.status_code != 200:
        print(f"❌ 获取手牌失败: {resp.text}")
        return
    
    data = resp.json()
    print(f"✅ 玩家0有 {data['cardCount']} 张牌")
    print(f"   前3张: {[f\"{c['value']}{c['suit']}\" for c in data['cards'][:3]]}")
    
    # 3. 获取游戏状态
    print("3. 获取游戏状态...")
    resp = requests.get(f'{BASE_URL}/game/state')
    if resp.status_code != 200:
        print(f"❌ 获取状态失败: {resp.text}")
        return
    
    state = resp.json()
    print(f"✅ 当前玩家: {state['currentPlayerName']}")
    print(f"   开始状态: {state['started']}")
    print(f"   玩家数: {len(state['players'])}")
    
    # 4. 出第一张牌
    print("4. 玩家0出第一张牌...")
    first_card = data['cards'][0]
    resp = requests.post(f'{BASE_URL}/game/play', json={
        'playerId': 0,
        'cards': [first_card]
    })
    
    if resp.status_code != 200:
        print(f"❌ 出牌失败: {resp.text}")
        return
    
    result = resp.json()
    if result['success']:
        print(f"✅ 出牌成功")
        print(f"   下一个玩家: {result['nextPlayer']}")
    else:
        print(f"❌ 出牌失败: {result['message']}")
    
    # 5. 获取历史
    print("5. 获取出牌历史...")
    resp = requests.get(f'{BASE_URL}/game/history')
    if resp.status_code != 200:
        print(f"❌ 获取历史失败: {resp.text}")
        return
    
    history = resp.json()
    print(f"✅ 历史记录: {history['total']} 条")
    if history['history']:
        last = history['history'][-1]
        print(f"   最后一次: {last['playerName']} {'过' if last['isPass'] else f\"出{last['cardType']['name']}\"}")

if __name__ == '__main__':
    print("="*50)
    print("掼蛋游戏 - API测试")
    print("="*50)
    
    # 测试服务器
    if not test_health():
        print("\n❌ 服务器未运行，请先启动: python server.py")
        exit(1)
    
    print("\n=== 静态文件测试 ===")
    test_static_files()
    
    # 测试游戏流程
    test_game_flow()
    
    print("\n" + "="*50)
    print("✅ 所有测试完成！")
    print("="*50)
