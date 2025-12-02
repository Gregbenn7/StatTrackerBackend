from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import csv
import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Baseball Stats API", version="1.0.0")

# Enable CORS for all origins (Lovable needs this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required directories exist
RAW_GAMES_DIR = Path("./raw_games")
OUTPUT_DIR = Path("./output")

RAW_GAMES_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

logger.info(f"Ensured directories exist: {RAW_GAMES_DIR}, {OUTPUT_DIR}")


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Baseball Stats API",
        "endpoints": {
            "upload": "POST /upload",
            "totals": "GET /totals",
            "games": "GET /games"
        }
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV file, save it to ./raw_games/, and process it.
    Returns {"status": "ok"} on success or error details on failure.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Validate CSV extension
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read file content
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = RAW_GAMES_DIR / safe_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved uploaded file to: {file_path}")
        
        # Call process_stats.py
        try:
            process_script = Path("process_stats.py")
            if not process_script.exists():
                raise HTTPException(
                    status_code=500,
                    detail="process_stats.py not found. Please ensure it exists in the project root."
                )
            
            # Run process_stats.py
            result = subprocess.run(
                ["python", "process_stats.py"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                logger.error(f"process_stats.py failed: {result.stderr}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing stats: {result.stderr[:500]}"
                )
            
            logger.info(f"Successfully processed stats: {result.stdout}")
            
        except FileNotFoundError:
            raise HTTPException(
                status_code=500,
                detail="Python interpreter not found. Please ensure Python is installed and in PATH."
            )
        except Exception as e:
            logger.error(f"Error running process_stats.py: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing stats: {str(e)}"
            )
        
        # Return success response
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "message": "File uploaded and processed successfully",
                "filename": safe_filename,
                "file_path": str(file_path)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@app.get("/totals")
def get_totals(team: Optional[str] = Query(None)):
    """
    Read ./output/hitter_totals.csv and return JSON list of hitters.
    Teams are kept separate - stats are grouped by (player_name, team).
    
    Query parameters:
    - team (optional): Filter results to only return hitters from this team
    
    Returns empty list if file doesn't exist.
    """
    totals_file = OUTPUT_DIR / "hitter_totals.csv"
    
    if not totals_file.exists():
        logger.warning(f"totals file not found: {totals_file}")
        return JSONResponse(
            status_code=200,
            content=[]
        )
    
    try:
        hitters = []
        with open(totals_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter by team if specified
                if team:
                    row_team = row.get('team', '').strip()
                    if row_team.lower() != team.lower():
                        continue
                
                # Convert numeric fields
                cleaned_row = {}
                for key, value in row.items():
                    key = key.strip()
                    # Try to convert to number if possible
                    try:
                        if '.' in str(value):
                            cleaned_row[key] = float(value)
                        else:
                            cleaned_row[key] = int(value)
                    except (ValueError, TypeError):
                        cleaned_row[key] = value.strip() if value else ""
                
                hitters.append(cleaned_row)
        
        logger.info(f"Returning {len(hitters)} hitter totals" + (f" for team: {team}" if team else ""))
        return JSONResponse(
            status_code=200,
            content=hitters
        )
        
    except Exception as e:
        logger.error(f"Error reading totals file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error reading totals file: {str(e)}"
        )


@app.get("/games")
def get_games(team: Optional[str] = Query(None)):
    """
    Read ./output/all_games_combined.csv and return JSON list of game rows.
    Teams are kept separate - each row maintains its team information.
    
    Query parameters:
    - team (optional): Filter results to only return rows from this team
    
    Returns empty list if file doesn't exist.
    """
    games_file = OUTPUT_DIR / "all_games_combined.csv"
    
    if not games_file.exists():
        logger.warning(f"games file not found: {games_file}")
        return JSONResponse(
            status_code=200,
            content=[]
        )
    
    try:
        games = []
        with open(games_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter by team if specified
                if team:
                    row_team = row.get('team', row.get('Team', '')).strip()
                    if row_team.lower() != team.lower():
                        continue
                
                # Convert numeric fields
                cleaned_row = {}
                for key, value in row.items():
                    key = key.strip()
                    # Try to convert to number if possible
                    try:
                        if '.' in str(value):
                            cleaned_row[key] = float(value)
                        else:
                            cleaned_row[key] = int(value)
                    except (ValueError, TypeError):
                        cleaned_row[key] = value.strip() if value else ""
                
                games.append(cleaned_row)
        
        logger.info(f"Returning {len(games)} game rows" + (f" for team: {team}" if team else ""))
        return JSONResponse(
            status_code=200,
            content=games
        )
        
    except Exception as e:
        logger.error(f"Error reading games file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error reading games file: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("Baseball Stats API - Lovable Frontend Integration")
    print("="*60)
    print("\nEXACT URLs for Lovable to call:")
    print("  POST http://localhost:8000/upload")
    print("  GET  http://localhost:8000/totals")
    print("  GET  http://localhost:8000/games")
    print("\n" + "="*60)
    print("Starting server on http://0.0.0.0:8000")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)

