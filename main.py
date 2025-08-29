"""
Main runner for Document Intelligence Application
Combines Streamlit frontend with FastAPI backend
"""

import os
import sys
import subprocess
import threading
import time
import signal
from pathlib import Path

def run_fastapi():
    """Run FastAPI backend server"""
    try:
        import uvicorn
        from fastapi_app import app
        
        print("🚀 Starting FastAPI backend on port 8001...")
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
    except Exception as e:
        print(f"❌ FastAPI server failed to start: {e}")

def run_streamlit():
    """Run Streamlit frontend"""
    try:
        print("🚀 Starting Streamlit frontend on port 8000...")
        # Wait a moment for FastAPI to start
        time.sleep(2)
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8000",
            "--server.address", "0.0.0.0",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false"
        ])
    except Exception as e:
        print(f"❌ Streamlit server failed to start: {e}")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down Document Intelligence application...")
    sys.exit(0)

def main():
    """Main application entry point"""
    print("📄 Document Intelligence Web App")
    print("=" * 50)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Change to the document_intelligence directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    try:
        # Start FastAPI in a separate thread
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()
        
        # Start Streamlit in the main thread
        run_streamlit()
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Application error: {e}")

if __name__ == "__main__":
    main()