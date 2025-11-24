"""
Simple diagnostic API to check what's failing in Vercel
"""
from fastapi import FastAPI
from pathlib import Path
import sys
import os

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/debug")
async def debug():
    """Debug endpoint to check environment"""
    try:
        base_dir = Path(__file__).parent.parent
        
        return {
            "status": "ok",
            "cwd": os.getcwd(),
            "file_location": str(Path(__file__)),
            "base_dir": str(base_dir),
            "sys_path": sys.path[:5],
            "data_exists": (base_dir / "data").exists(),
            "customers_exists": (base_dir / "data" / "customers.json").exists(),
            "transactions_exists": (base_dir / "data" / "transactions.json").exists(),
            "files_in_data": list((base_dir / "data").iterdir()) if (base_dir / "data").exists() else [],
            "writable_tmp": os.access('/tmp', os.W_OK) if os.path.exists('/tmp') else False
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

# For Vercel
handler = app
