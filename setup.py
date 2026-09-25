"""Install JARVIS dependencies. Run with Python 3.11 or 3.12."""
import subprocess
import sys
from pathlib import Path


def main():
    if not (3, 11) <= sys.version_info[:2] < (3, 13):
        raise SystemExit("Use Python 3.11 or 3.12 to install JARVIS.")
    requirements = Path(__file__).resolve().with_name("requirements.txt")
    print("Installing requirements...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements)], check=True)
    print("Installing Playwright browsers...")
    subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)
    print("Setup complete! Run 'python main.py' to start JARVIS.")


if __name__ == "__main__":
    main()
