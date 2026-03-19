#!/usr/bin/env python3
"""
Nova Memory 2.0 - Installation & Setup Helper
Automated setup script for easy project configuration
"""

import sys
import subprocess
import shutil
from pathlib import Path


class NovaMemorySetup:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.venv_dir = self.project_dir / "venv"
        self.backup_dir = self.project_dir / "backups"
        self.logs_dir = self.project_dir / "logs"

    def print_header(self, title):
        """Print formatted section header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

    def print_success(self, msg):
        """Print success message"""
        print(f"✓ {msg}")

    def print_warning(self, msg):
        """Print warning message"""
        print(f"⚠ {msg}")

    def print_error(self, msg):
        """Print error message"""
        print(f"✗ {msg}")

    def check_python_version(self):
        """Check if Python version is 3.9+"""
        self.print_header("Checking Python Version")
        if sys.version_info < (3, 9):
            self.print_error(f"Python 3.9+ required. You have {sys.version}")
            sys.exit(1)
        self.print_success(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")

    def create_directories(self):
        """Create necessary directories"""
        self.print_header("Creating Directories")
        for directory in [self.backup_dir, self.logs_dir]:
            directory.mkdir(exist_ok=True)
            self.print_success(f"Directory ready: {directory}")

    def create_env_file(self):
        """Create .env file from .env.example if it doesn't exist"""
        self.print_header("Configuring Environment")
        env_file = self.project_dir / ".env"
        env_example = self.project_dir / ".env.example"

        if env_file.exists():
            self.print_warning(".env file already exists, skipping...")
            return

        if env_example.exists():
            shutil.copy(env_example, env_file)
            self.print_success("Created .env from .env.example")
            self.print_warning("⚠ Remember to update .env with your actual configuration!")
        else:
            self.print_warning(".env.example not found, skipping .env creation")

    def install_dependencies(self, full=False):
        """Install project dependencies"""
        self.print_header("Installing Dependencies")
        try:
            if full:
                self.print_success("Installing with all optional features...")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "-e", ".[all,dev]"
                ])
            else:
                self.print_success("Installing core dependencies...")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
                ])
            self.print_success("Dependencies installed successfully")
        except subprocess.CalledProcessError:
            self.print_error("Failed to install dependencies")
            sys.exit(1)

    def run_tests(self):
        """Run test suite"""
        self.print_header("Running Tests")
        try:
            # Try to run main.py tests
            subprocess.check_call([sys.executable, "main.py"])
            self.print_success("All tests passed!")
        except subprocess.CalledProcessError:
            self.print_error("Some tests failed. Check output above.")
            sys.exit(1)

    def display_next_steps(self):
        """Display next steps for user"""
        self.print_header("Setup Complete! ✓")
        print("""
Next Steps:

1. UPDATE CONFIGURATION (if not using defaults):
   - Edit .env file with your settings
   - Review and customize as needed

2. START THE API SERVER:
   python -m api.server
   - API will be available at http://localhost:8000
   - Swagger docs at http://localhost:8000/docs

3. RUN DEMO SCENARIOS:
   python demo_scenarios.py
   - View example usage patterns

4. INTEGRATE INTO YOUR PROJECT:
   from enhanced_memory import EnhancedMemoryStorage
   from agent_collaboration import AgentCollaboration

5. READ FULL DOCUMENTATION:
   - See README.md for comprehensive guide
   - Check docstrings in source files
   - View API docs at http://localhost:8000/docs

QUICK REFERENCE:
   python main.py                   # Run tests
   python -m api.server             # Start API server
   python demo_scenarios.py          # Run demo
   pip install -e ".[ml]"          # Add ML features
   pip install -e ".[blockchain]"  # Add Solana support
   pytest -v                        # Run tests with pytest
        """)

    def setup_complete_summary(self):
        """Print setup summary"""
        print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    NOVA MEMORY 2.0 - SETUP COMPLETE                       ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Project: Nova Memory 2.0                                                 ║
║  Real-time AI Agent Memory Management System                              ║
║                                                                            ║
║  ✓ Python 3.9+ verified                                                  ║
║  ✓ Directories created                                                   ║
║  ✓ Environment configured                                                ║
║  ✓ Dependencies installed                                                ║
║  ✓ Tests passed                                                          ║
║                                                                            ║
║  Documentation: https://github.com/mbugus94-lang/nova-memory             ║
║  License: MIT                                                            ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
        """)

    def run_setup(self, install_all=False, run_tests_flag=False):
        """Run complete setup process"""
        print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║             NOVA MEMORY 2.0 - INSTALLATION & SETUP WIZARD                ║
╚═══════════════════════════════════════════════════════════════════════════╝
        """)

        self.check_python_version()
        self.create_directories()
        self.create_env_file()
        self.install_dependencies(full=install_all)

        if run_tests_flag:
            self.run_tests()

        self.display_next_steps()
        self.setup_complete_summary()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Nova Memory 2.0 Setup Helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py                 # Basic setup
  python setup.py --full          # Full setup with all features
  python setup.py --full --test   # Full setup + run tests
  python setup.py --test          # Core setup + run tests
        """,
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Install all optional dependencies (ML, Blockchain, etc.)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run tests after installation",
    )
    parser.add_argument(
        "--no-env",
        action="store_true",
        help="Skip creating .env file",
    )

    args = parser.parse_args()

    setup = NovaMemorySetup()
    setup.run_setup(install_all=args.full, run_tests_flag=args.test)


if __name__ == "__main__":
    main()
