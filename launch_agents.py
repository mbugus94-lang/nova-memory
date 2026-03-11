#!/usr/bin/env python3
"""
Nova Memory 2.0 - Agent Launcher
Dynamically starts agents with proper environment configuration
"""

import subprocess
import os
import sys
import time
import argparse
from pathlib import Path

def setup_agent(agent_id: str, port: int):
    """Setup and start a single agent"""
    
    # Get the project root
    project_root = Path(__file__).parent.absolute()
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    env['AGENT_ID'] = agent_id
    env['API_PORT'] = str(port)
    
    # Agent name
    agent_name = f"Agent-{agent_id.split('_')[1]}"
    
    print(f"\n{'='*70}")
    print(f"🚀 Starting {agent_name}")
    print(f"{'='*70}")
    print(f"Agent ID:    {agent_id}")
    print(f"API Port:    {port}")
    print(f"Project:     {project_root}")
    print(f"Python Path: {env['PYTHONPATH']}")
    print(f"{'='*70}\n")
    
    # Start the agent
    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "api.integration:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--log-level", "info"
    ]
    
    try:
        print(f"Running: {' '.join(cmd)}\n")
        subprocess.run(cmd, cwd=str(project_root), env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting {agent_name}: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n⏹  {agent_name} stopped by user")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Launch Nova Memory 2.0 agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch_agents.py --agent 1        # Start Agent 1 on port 8001
  python launch_agents.py --agent 2        # Start Agent 2 on port 8002
  python launch_agents.py --agent 3        # Start Agent 3 on port 8003
  python launch_agents.py --all            # Start all 3 agents (in sequence)
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--agent", type=int, choices=[1, 2, 3],
                      help="Start specific agent (1-3)")
    group.add_argument("--all", action="store_true",
                      help="Start all 3 agents in sequence")
    
    args = parser.parse_args()
    
    agents = []
    if args.all:
        agents = [(f"agent_00{i}", 8000 + i) for i in range(1, 4)]
    elif args.agent:
        agents = [(f"agent_00{args.agent}", 8000 + args.agent)]
    
    print("\n" + "="*70)
    print("NOVA MEMORY 2.0 - AGENT LAUNCHER")
    print("="*70)
    
    for agent_id, port in agents:
        print(f"\nLaunching {agent_id} on port {port}...")
        setup_agent(agent_id, port)
        
        if len(agents) > 1:
            print(f"\n⏳ Waiting 10 seconds before next agent...")
            time.sleep(10)

if __name__ == "__main__":
    main()
