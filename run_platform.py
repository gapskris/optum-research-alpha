import os
import subprocess
import time
import sys
import webbrowser

def run_platform():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("## Launching Optum Strategic Alpha Platform")
    print("## Initializing Backend and Frontend Services...")

    # 1. Start the FastAPI Backend
    # Using the project's virtual environment
    python_executable = os.path.join(root_dir, "research_agent", "Scripts", "python.exe")
    backend_process = subprocess.Popen(
        [python_executable, "api.py"],
        cwd=root_dir
    )

    # 2. Start the Vite Frontend
    # Requires node/npm to be installed on the system
    frontend_process = subprocess.Popen(
        ["npm.cmd", "run", "dev"],
        cwd=os.path.join(root_dir, "frontend"),
        shell=True
    )

    print("\n[SUCCESS] Services are starting up.")
    print("-> Backend: http://localhost:8000")
    print("-> Frontend: http://localhost:5173")
    
    time.sleep(5) # Wait for Vite to initialize
    
    print("\n## Opening Mission Control in your browser...")
    webbrowser.open("http://localhost:5173")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n## Shutting down platform...")
        backend_process.terminate()
        frontend_process.terminate()
        print("## Offshore. Stay Alpha.")

if __name__ == "__main__":
    run_platform()
