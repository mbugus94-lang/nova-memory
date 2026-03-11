#!/bin/bash

# Nova Memory 2.0 - Installation & Setup Script for macOS/Linux
# This script automates the setup process on Unix-like systems

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Functions for colored output
print_header() {
    echo ""
    echo "============================================================================="
    echo "  $1"
    echo "============================================================================="
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

# Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Print welcome message
cat << "EOF"

╔════════════════════════════════════════════════════════════════════════════╗
║                  NOVA MEMORY 2.0 - SETUP WIZARD                           ║
║            Real-time AI Agent Memory Management System                     ║
╚════════════════════════════════════════════════════════════════════════════╝

EOF

# Check Python version
print_header "Checking Python Installation"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    echo ""
    echo "Please install Python 3.9 or higher:"
    echo "  macOS: brew install python3"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_success "Python $PYTHON_VERSION detected"

# Check Python version requirement
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [[ $PYTHON_MINOR -lt 9 ]]; then
    print_error "Python 3.9+ is required. You have $PYTHON_VERSION"
    exit 1
fi

# Check pip
print_info "Checking pip availability..."
if ! python3 -m pip --version &> /dev/null; then
    print_error "pip is not available"
    exit 1
fi
print_success "pip is available"

# Create directories
print_header "Setting Up Directories"

for dir in backups logs; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_success "Created $dir directory"
    else
        print_warning "$dir directory already exists"
    fi
done

# Create .env file if needed
print_header "Configuring Environment"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp ".env.example" ".env"
        print_success "Created .env from .env.example"
        print_warning "Remember to update .env with your configuration!"
    else
        print_warning ".env.example not found, skipping .env creation"
    fi
else
    print_warning ".env already exists, skipping..."
fi

# Setup Python virtual environment
print_header "Setting Up Python Virtual Environment"

if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip, setuptools, wheel
print_header "Upgrading pip and Build Tools"
pip install --upgrade pip setuptools wheel
print_success "pip, setuptools, and wheel upgraded"

# Install dependencies
print_header "Installing Dependencies"

case "${1:-default}" in
    --full)
        print_info "Installing with all optional features (ML, Blockchain, Dev)..."
        pip install -e ".[all,dev]"
        print_success "Full installation complete with all features"
        ;;
    --dev)
        print_info "Installing with development tools..."
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        print_success "Core + development dependencies installed"
        ;;
    *)
        print_info "Installing core dependencies..."
        pip install -r requirements.txt
        print_success "Core dependencies installed"
        ;;
esac

# Run tests if requested
if [ "$2" = "--test" ]; then
    print_header "Running Tests"
    print_info "Executing test suite..."
    if python main.py; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed"
        exit 1
    fi
fi

# Display next steps
print_header "Setup Complete!"

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════╗
║                    SETUP SUCCESSFULLY COMPLETED                           ║
╚════════════════════════════════════════════════════════════════════════════╝

VIRTUAL ENVIRONMENT:
  Virtual environment is located in: ./venv/
  Activate it with: source venv/bin/activate
  Deactivate with: deactivate

NEXT STEPS:

1. UPDATE CONFIGURATION (if not using defaults):
   - Edit .env file with your settings

2. START THE API SERVER:
   python -m api.server
   → API available at http://localhost:8000
   → Swagger docs at http://localhost:8000/docs

3. RUN DEMO SCENARIOS:
   python demo_scenarios.py

4. RUN TESTS:
   python main.py

5. INSTALL ADDITIONAL FEATURES:
   - ML/AI capabilities: pip install -e ".[ml]"
   - Solana integration: pip install -e ".[blockchain]"
   - Advanced storage: pip install -e ".[storage]"

USEFUL COMMANDS:
  make help          # Show all available make commands
  make test          # Run tests
  make format        # Format code
  make lint          # Check code quality
  make run-api       # Start API server
  make clean         # Clean generated files

DOCUMENTATION:
  - Full guide: cat README.md
  - Installation: cat INSTALL.md
  - API docs: http://localhost:8000/docs (when server is running)

REMEMBER:
  - Always activate the virtual environment: source venv/bin/activate
  - The .env file contains your configuration
  - Keep your .env file secure and never commit it to version control

╚════════════════════════════════════════════════════════════════════════════╝

EOF

echo ""
print_success "All done! Happy coding! 🚀"
echo ""
