"""
eCitizen Voice Assistant - Entry Point

This file serves as the main entry point for running the application.
It imports and runs the FastAPI backend server.

For development, you can run this directly:
    python app.py

Or use uvicorn directly:
    uvicorn backend.main:app --reload
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Run the FastAPI application."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   🇰🇪 eCitizen Voice Assistant                                ║
    ║   Accessible Government Services for All                     ║
    ║                                                              ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                                                              ║
    ║   Backend API:  http://{host}:{port}                         ║
    ║   API Docs:     http://{host}:{port}/docs                    ║
    ║   Health Check: http://{host}:{port}/health                  ║
    ║                                                              ║
    ║   Frontend:     Run 'npm start' in the frontend directory    ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=debug
    )

if __name__ == "__main__":
    main()

