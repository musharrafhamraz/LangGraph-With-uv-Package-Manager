import os
import subprocess
import sys

def main():
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the directory containing the main.py file
    os.chdir(current_dir)
    
    # Run the Streamlit app
    cmd = [sys.executable, "-m", "streamlit", "run", "main.py"]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()