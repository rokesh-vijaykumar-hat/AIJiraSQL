"""
Packager tool for installing OpenAI Python package.
"""
import subprocess
import sys

def install_openai():
    """Install the OpenAI Python package."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"])
        print("OpenAI package installed successfully.")
    except Exception as e:
        print(f"Error installing OpenAI package: {str(e)}")

if __name__ == "__main__":
    install_openai()