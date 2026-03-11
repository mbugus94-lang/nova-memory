# Installation Guide - Nova Memory 2.0

Complete guide to installing and setting up Nova Memory 2.0 on your system.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Quick Start (Recommended)](#quick-start-recommended)
3. [Detailed Installation](#detailed-installation)
4. [Platform-Specific Guides](#platform-specific-guides)
5. [Optional Features](#optional-features)
6. [Troubleshooting](#troubleshooting)
7. [Verification](#verification)

---

## System Requirements

### Minimum Requirements
- **Python**: 3.9 or higher
- **Disk Space**: 100 MB (core) + database size
- **RAM**: 512 MB minimum (2 GB recommended)
- **OS**: Windows, macOS, Linux

### Recommended for Development
- **Python**: 3.10 or 3.11
- **RAM**: 4 GB or more
- **Disk Space**: 500 MB for development tools

### Verify Python Installation
```bash
python --version
# or
python3 --version
```

If Python is not found, [download from python.org](https://www.python.org/downloads/)

---

## Quick Start (Recommended)

The easiest way to get started in 30 seconds:

### On Windows
```bash
# Navigate to project directory
cd C:\Users\DAVID\nova-memory

# Run setup script
setup.bat

# Start the API server
python -m api.server
```

### On macOS/Linux
```bash
# Navigate to project directory
cd ~/nova-memory

# Make setup executable and run
chmod +x setup.sh
./setup.sh

# Or use Python setup helper
python3 setup_helper.py

# Start the API server
python -m api.server
```

---

## Detailed Installation

### Step 1: Clone the Repository

```bash
# Using git
git clone https://github.com/mbugus94-lang/nova-memory.git
cd nova-memory

# Or download ZIP and extract
# Then navigate to the extracted folder
cd nova-memory
```

### Step 2: Verify Python

```bash
python --version
# Output should be: Python 3.9.x or higher
```

### Step 3: Create Virtual Environment (Optional but Recommended)

Virtual environments isolate project dependencies from system Python.

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

After activation, your terminal should show `(venv)` prefix.

### Step 4: Install Dependencies

#### Basic Installation (Core Only)
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Development Installation (With Testing Tools)
```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

#### Full Installation (All Features)
```bash
pip install --upgrade pip
pip install -e ".[all,dev]"
```

#### Specific Features
```bash
# ML/AI capabilities
pip install -e ".[ml]"

# Solana blockchain support
pip install -e ".[blockchain]"

# Advanced storage backends
pip install -e ".[storage]"

# Multiple features
pip install -e ".[ml,blockchain]"
```

### Step 5: Create Configuration File

```bash
# Copy the example configuration
cp .env.example .env

# Edit .env with your settings (optional for defaults)
# nano .env          # On macOS/Linux
# notepad .env       # On Windows
```

### Step 6: Verify Installation

```bash
# Run tests to verify everything works
python main.py

# If tests pass, installation is successful!
```

---

## Platform-Specific Guides

### Windows Installation

#### With Python Installer
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer
3. **Important**: Check "Add Python to PATH"
4. Click "Disable path length limit" (Recommended)
5. Complete installation

#### Using PowerShell
```powershell
# Navigate to project
cd C:\Users\DAVID\nova-memory

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -e ".[all,dev]"
```

#### Using Command Prompt (cmd.exe)
```cmd
cd C:\Users\DAVID\nova-memory
python -m venv venv
venv\Scripts\activate.bat
pip install -e ".[all,dev]"
```

#### Using setup.bat (Easiest)
```bash
setup.bat
```

---

### macOS Installation

```bash
# Install using Homebrew (if not already installed)
brew install python3

# Verify installation
python3 --version

# Navigate to project
cd ~/nova-memory

# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -e ".[all,dev]"
```

---

### Linux Installation (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Verify installation
python3 --version

# Navigate to project
cd ~/nova-memory

# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e ".[all,dev]"
```

#### Using apt for development tools (optional)
```bash
sudo apt install build-essential python3-dev
```

---

## Optional Features

### Machine Learning / AI Features

Adds support for embeddings and fine-tuning:

```bash
pip install -e ".[ml]"
```

**Includes**:
- PyTorch
- Sentence Transformers
- Advanced NLP capabilities

**Note**: This adds ~2 GB to installation size

### Blockchain / Solana Support

Adds Solana blockchain integration:

```bash
pip install -e ".[blockchain]"
```

**Includes**:
- Solana SDK
- Blockchain verification
- Wallet integration

### Advanced Storage

Adds LevelDB and advanced storage backends:

```bash
pip install -e ".[storage]"
```

### Development Tools

Adds testing, linting, and documentation tools:

```bash
pip install -r requirements-dev.txt
# Or
pip install -e ".[dev]"
```

**Includes**:
- pytest (testing)
- black (formatting)
- mypy (type checking)
- sphinx (documentation)

---

## Troubleshooting

### Issue: "Python not found"

**Solution**:
- Verify Python is installed: `python --version`
- Add Python to PATH:
  - Windows: Reinstall with "Add Python to PATH" checked
  - macOS: Use `python3` instead of `python`
  - Linux: Install via package manager

### Issue: "Permission denied"

**On macOS/Linux**:
```bash
# Make scripts executable
chmod +x setup.sh
chmod +x setup_helper.py

# Then run
./setup.sh
```

### Issue: "pip: command not found"

**Solution**:
```bash
# Use Python module instead
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Issue: "Module not found" errors

**Solution 1**: Install missing feature set
```bash
# For Solana: Module Solana not found
pip install -e ".[blockchain]"

# For ML: Module torch not found
pip install -e ".[ml]"
```

**Solution 2**: Reinstall all packages
```bash
pip install --upgrade --force-reinstall -e ".[all]"
```

### Issue: Virtual Environment not activating

**Windows PowerShell**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

**macOS/Linux**:
```bash
source venv/bin/activate
```

### Issue: Port 8000 already in use

**Change the port**:
```bash
# Edit API_PORT in .env
API_PORT=8001

# Or start server on different port
python -m api.server --port 8001
```

### Issue: Database locked

**Solution**:
```bash
# Close all instances of the application
# Delete the database (it will be recreated)
rm nova_memory.db nova_memory.db-shm nova_memory.db-wal

# Or rename for backup
mv nova_memory.db nova_memory.db.backup
```

### Issue: Out of disk space

Nova Memory creates:
- Main database: 10-100 MB (depending on usage)
- Backups: Up to 200 MB
- Logs: 10-50 MB

**Solution**:
- Clean old backups: `rm backups/*`
- Rotate logs: Clear `logs/` directory
- Use external storage for large databases

---

## Verification

### Test Installation

```bash
# Run comprehensive tests
python main.py

# Expected output:
# ✓ Solana integration initialized
# ✓ Enhanced memory storage functional
# ✓ Agent collaboration operational
# ✓ Database initialization complete
```

### Verify API Server

```bash
# Start server
python -m api.server

# In another terminal, test:
curl http://localhost:8000/health
# or
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"
```

### Check Installed Packages

```bash
# View installed packages
pip list

# Looking for:
# - fastapi
# - uvicorn
# - pydantic
# - numpy
```

### Run Demo

```bash
python demo_scenarios.py
```

---

## Next Steps

After successful installation:

1. **Read the Documentation**: See [README.md](README.md) for comprehensive guide
2. **Start the Server**: `python -m api.server`
3. **Explore API**: Visit `http://localhost:8000/docs`
4. **Run Demos**: `python demo_scenarios.py`
5. **Read Code**: Check docstrings in source files
6. **Configure**: Update `.env` for your specific use case

---

## Getting Help

If you encounter issues:

1. Check this guide's [Troubleshooting](#troubleshooting) section
2. Review the [README.md](README.md)
3. Check the [GitHub Issues](https://github.com/mbugus94-lang/nova-memory/issues)
4. Review API documentation at `http://localhost:8000/docs`

---

## Uninstallation

To remove Nova Memory:

### Keep Source Code
```bash
# Remove Python packages only
pip uninstall nova-memory fastapi uvicorn pydantic numpy

# Remove virtual environment (if created)
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows
```

### Complete Removal
```bash
# Remove entire project directory
rm -rf nova-memory  # macOS/Linux
rmdir /s nova-memory  # Windows
```

---

## Version Compatibility

| Python | Status | Notes |
|--------|--------|-------|
| 3.8 | ❌ Not Supported | Minimum is 3.9 |
| 3.9 | ✅ Supported | Minimum requirement |
| 3.10 | ✅ Recommended | Stable, tested |
| 3.11 | ✅ Recommended | Latest stable |
| 3.12 | ⚠️ Experimental | May work, not fully tested |

---

**Installation Guide Version**: 1.0  
**Last Updated**: March 2026  
**Compatible with**: Nova Memory 2.0+
