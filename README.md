# Nova Memory 2.0 - Real-Time AI Agent Memory Management

<p align="center">
  <a href="https://github.com/mbugus94-lang/nova-memory/stargazers">
    <img src="https://img.shields.io/github/stars/mbugus94-lang/nova-memory?style=social" alt="Stars">
  </a>
  <img src="https://img.shields.io/badge/Version-2.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

<p align="center">
  <strong>🧠 AI Agent Memory System with Real-Time Learning</strong>
</p>

---

## ⚡ Quick Install (2 minutes!)

```bash
# Clone
git clone https://github.com/mbugus94-lang/nova-memory.git
cd nova-memory

# Install
pip install -r requirements.txt

# Run demo
python demo_scenarios.py
```

---

## 💻 Quick Start

```python
from enhanced_memory import EnhancedMemoryStorage

# Initialize
memory = EnhancedMemoryStorage()

# Store a memory
memory_id = memory.add_memory(
    content="User prefers concise responses",
    tags=["preferences", "style"]
)

# Retrieve memories
results = memory.search_memories("user preferences")
print(f"Found {len(results)} memories")
```

---

## 📦 What's Included

| File | Description |
|------|-------------|
| `enhanced_memory.py` | Core memory storage with compression |
| `agent_collaboration.py` | Multi-agent coordination |
| `demo_scenarios.py` | Working demos |
| `api/server.py` | REST API server |

---

## 🔌 API Server

```bash
# Start server
python -m api.server

# Visit http://localhost:8000/docs
```

---

## 🧪 Test Results

✅ Memory storage - WORKING  
✅ Agent collaboration - WORKING  
✅ Database initialization - WORKING

---

## 📝 License

MIT

---

<p align="center">Built with ❤️ by <a href="https://github.com/mbugus94-lang">David Gakere</a></p>