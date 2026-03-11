# Quick Start Guide - Nova Memory 2.0

Get Nova Memory 2.0 running in under 5 minutes!

## Choose Your Path

### 🚀 Fastest: Windows Users (30 seconds)

```bash
cd C:\Users\DAVID\nova-memory
setup.bat
```

Done! Your setup is complete and configured.

### 🚀 Fastest: macOS/Linux Users (1 minute)

```bash
cd ~/nova-memory
chmod +x setup.sh
./setup.sh
```

### 🐳 Using Docker (2 minutes)

```bash
cd nova-memory
docker-compose up
```

Access API at: `http://localhost:8000`

---

## Manual Setup (3-5 minutes)

### 1. Install Python (if needed)
**Check Python is installed:**
```bash
python --version
```
Should show Python 3.9 or higher.

If not, install from [python.org](https://www.python.org/downloads/)

### 2. Install Dependencies
```bash
# Navigate to project
cd nova-memory

# Install core packages
pip install -r requirements.txt
```

### 3. Start the API Server
```bash
python -m api.server
```

### 4. Access the API
- Open browser to: `http://localhost:8000/docs`
- You'll see interactive API documentation (Swagger UI)

---

## Common Tasks

### Run Tests
```bash
python main.py
```

### View Demo
```bash
python demo_scenarios.py
```

### Install All Features
```bash
pip install -e ".[all]"
```

### Stop the Server
Press `Ctrl+C` in the terminal

---

## Troubleshooting

### "Python not found"
```bash
# Make sure Python is installed
python --version

# If that doesn't work, try:
python3 --version
```

### "ModuleNotFoundError"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "Port 8000 already in use"
The API server is already running or another app is using port 8000.
- Find and close the other process
- Or start on a different port (edit `.env` and set `API_PORT=8001`)

---

## API Quick Reference

### Start Server
```bash
python -m api.server
```

### Access API Docs
Visit: `http://localhost:8000/docs`

### Test API Health
```bash
curl http://localhost:8000/health
```

### Python Example
```python
from enhanced_memory import EnhancedMemoryStorage

# Initialize
storage = EnhancedMemoryStorage('nova_memory.db')

# Store memory
storage.store_memory(
    memory_id="test_001",
    content="Important information",
    tags=["test"]
)

# Retrieve
memory = storage.retrieve_memory("test_001")
print(memory['content'])
```

---

## Next Steps

1. **Read Full Documentation**: See [README.md](README.md)
2. **Explore API**: Visit `http://localhost:8000/docs`
3. **Run Examples**: `python demo_scenarios.py`
4. **View Installation Guide**: See [INSTALL.md](INSTALL.md)

---

## Features

✅ Store and retrieve memories  
✅ Version control and history  
✅ Multi-agent collaboration  
✅ REST API with Swagger docs  
✅ Solana blockchain integration  
✅ Advanced analytics  

---

## Getting Help

- **Documentation**: [README.md](README.md)
- **Installation**: [INSTALL.md](INSTALL.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **API Docs**: `http://localhost:8000/docs` (when running)

---

**That's it! You're ready to use Nova Memory 2.0** 🎉

For more information, see [README.md](README.md) or visit the [GitHub repository](https://github.com/mbugus94-lang/nova-memory).
