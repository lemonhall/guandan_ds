"""
掼蛋 AI Agent - 支持混合 LLM + 规则引擎
可以启动 3 个规则引擎 AI，或 2 个规则引擎 + 1 个 LLM AI
"""

import sys
import time
import threading
from typing import List
from ai_agent import GuandanAIAgent
from llm_ai_agent import LLMGuandanAIAgent

# 全局容器
agents: List = []
threads: List[threading.Thread] = []


def start_ai_agents(use_llm_for_player2=False):
    """
    启动 AI Agent
    use_llm_for_player2: 如果为 True，则 player_id=2 使用 LLM AI
    """
    global agents, threads

    agents = []
    
    # Player 1: 规则引擎 AI（右侧）
    agents.append(GuandanAIAgent(player_id=1))
    
    # Player 2: LLM AI 或规则引擎 AI（对家）
    if use_llm_for_player2:
        try:
            agents.append(LLMGuandanAIAgent(player_id=2))
        except ValueError as e:
            print(f"⚠️  LLM AI 初始化失败: {e}")
            print("    降级使用规则引擎 AI")
            agents.append(GuandanAIAgent(player_id=2))
    else:
        agents.append(GuandanAIAgent(player_id=2))
    
    # Player 3: 规则引擎 AI（左侧）
    agents.append(GuandanAIAgent(player_id=3))

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
    for t in threads:
        t.join(timeout=5)
    print("✅ 所有 AI Agent 已停止")
    print("=" * 50)


if __name__ == '__main__':
    print("掼蛋 AI Agent 混合启动器")
    print("=" * 50)
    print("使用方式:")
    print("1. 启动游戏服务器: python server.py")
    print("2. 打开游戏前端: index.html")
    print("3. 在前端点击'开始游戏'")
    print("4. 在另一个终端运行这个脚本")
    print("=" * 50)
    print()
    
    # 选择模式
    print("选择启动模式:")
    print("1. 全规则引擎 AI（3 个规则引擎）")
    print("2. 混合 AI（2 个规则引擎 + 1 个 LLM AI）")
    print()
    
    choice = input("请选择 (1 或 2，默认 1): ").strip() or "1"
    use_llm = choice == "2"
    
    if use_llm:
        print("\n⚠️  使用 LLM AI 需要设置环境变量:")
        print("   export DEEPSEEK_API_KEY=你的API密钥")
        print("   (或传入 api_key 参数)")
        print()
    
    print("按 Ctrl+C 停止 AI Agent")
    print("=" * 50, flush=True)

    input("按Enter键启动AI Agent...")
    print("正在启动 AI Agent...", flush=True)
    start_ai_agents(use_llm_for_player2=use_llm)
    print("AI Agent 启动完成，等待游戏开始...", flush=True)

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown_agents()
