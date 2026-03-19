#!/usr/bin/env python3
"""
Redis Setup Helper for Nova Memory
Automatically installs and starts Redis using the best available method
"""

import subprocess
import sys
import time

def run_cmd(cmd, shell=False):
    """Run a command and return output"""
    try:
        result = subprocess.run(
            cmd if shell else cmd.split(),
            capture_output=True,
            text=True,
            timeout=5,
            shell=shell
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "Command timeout"
    except Exception as e:
        return 1, "", str(e)

def check_redis_running():
    """Check if Redis is accessible"""
    try:
        import redis
        r = redis.Redis(host='127.0.0.1', port=6379, socket_connect_timeout=2)
        r.ping()
        return True
    except Exception:
        return False

def setup_wsl_redis():
    """Setup Redis in WSL2"""
    print("\n📦 Setting up Redis in WSL2...")

    # First, update package list and install Redis
    cmd1 = 'wsl bash -c "sudo apt-get update && sudo apt-get install -y redis-server"'
    print("  → Installing Redis in WSL...")
    code, out, err = run_cmd(cmd1, shell=True)

    if "already" in out or "already" in err or code == 0:
        print("  ✓ Redis package ready in WSL")
    else:
        print(f"  ⚠ Installation attempt: {err[:100]}")

    # Now start Redis as daemon
    print("  → Starting Redis server...")
    cmd2 = 'wsl bash -c "redis-server --daemonize yes --port 6379"'
    code, out, err = run_cmd(cmd2, shell=True)

    time.sleep(2)

    if check_redis_running():
        print("  ✓ Redis is running on port 6379")
        return True
    else:
        # Try alternative: start in background
        print("  → Trying alternative startup...")
        cmd3 = 'wsl bash -c "nohup redis-server --port 6379 > /tmp/redis.log 2>&1 &"'
        run_cmd(cmd3, shell=True)
        time.sleep(2)

        if check_redis_running():
            print("  ✓ Redis started successfully")
            return True

    return False

def main():
    print("\n" + "="*60)
    print("NOVA MEMORY 2.0 - REDIS SETUP")
    print("="*60)

    # Check if already running
    if check_redis_running():
        print("\n✓ Redis is already running on port 6379")
        return 0

    print("\nAttempting to start Redis...")

    # Try WSL2 method
    if setup_wsl_redis():
        print("\n" + "="*60)
        print("✅ REDIS SETUP COMPLETE!")
        print("="*60)
        print("\nRedis Server Details:")
        print("  Host: 127.0.0.1 (via WSL2)")
        print("  Port: 6379")
        print("  Status: Running")
        print("\nYou can now start the agents:")
        print(r"  .\start_agent_1.ps1")
        print("="*60)
        return 0

    print("\n⚠ Redis setup failed")
    print("\nAlternative: Start Redis manually")
    print("  wsl bash -c 'redis-server --port 6379'")
    print("\nOR install via:")
    print("  1. Chocolatey: choco install redis-64")
    print("  2. WSL2 manually: wsl && sudo apt-get install redis-server")
    print("  3. Docker: docker run -d -p 6379:6379 redis:7-alpine")

    return 1

if __name__ == "__main__":
    sys.exit(main())
