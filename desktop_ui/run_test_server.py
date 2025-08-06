import os
import sys
import subprocess
import time
import threading

def run_math_server():
    """Run the math server in a separate process"""
    # Get the absolute path to the math server script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    math_server_path = os.path.join(parent_dir, "mcp_server", "mathserver.py")
    
    # Run the math server
    print(f"Starting math server from: {math_server_path}")
    process = subprocess.Popen([sys.executable, math_server_path], 
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              text=True)
    
    # Print process output for debugging
    def print_output():
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(f"Math server: {line.strip()}")
    
    # Start thread to print output
    threading.Thread(target=print_output, daemon=True).start()
    
    return process

def main():
    # Start the math server
    math_process = run_math_server()
    
    try:
        # Keep the script running
        print("Test server running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping test server...")
    finally:
        # Terminate the math server process
        if math_process:
            math_process.terminate()
            math_process.wait()
            print("Math server stopped.")

if __name__ == "__main__":
    main()