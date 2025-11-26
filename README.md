# Baseball League API

A FastAPI-based backend API for managing a HitTrax-based adult baseball league. This API handles game CSV uploads, computes season-long hitting statistics, provides leaderboards, and generates AI-powered storylines using OpenAI.

## Features

- 📊 CSV game data ingestion from HitTrax exports
- 🗄️ Relational database storage (SQLite by default, Postgres-ready)
- 📈 Automatic stat computation (AVG, OBP, SLG, OPS, etc.)
- 🏆 Leaderboard endpoints with filtering
- 📝 AI-generated game storylines using OpenAI
- 👤 Player scouting reports
- 🔄 CORS support for frontend integration

## Installation

1. **Clone or navigate to the project directory**

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   FRONTEND_ORIGIN=http://localhost:3000
   DATABASE_URL=sqlite:///./baseball_league.db
   ```
   
   **Note:** For production with Postgres/Supabase, update `DATABASE_URL`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost/dbname
   # or for Supabase:
   DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
   ```

## Running the Application

Start the FastAPI server with:
```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API:** http://localhost:8000
- **Interactive API docs:** http://localhost:8000/docs
- **Alternative docs:** http://localhost:8000/redoc

## API Endpoints

### Game Management

- **POST `/games/upload_csv`** - Upload a CSV file with game stats
  - Form data: `file` (CSV), `league`, `season`, `date` (YYYY-MM-DD), `home_team`, `away_team`
  
- **GET `/games`** - List recent games (supports `limit` and `offset` query params)

- **GET `/games/{game_id}`** - Get game details with plate appearances

### Statistics

- **GET `/stats/leaderboard`** - Get hitting leaderboard (ordered by OPS)
  - Query params: `league` (optional), `season` (optional)

### Players

- **GET `/players`** - List all players with stats
  - Query params: `league` (optional), `season` (optional)

- **GET `/players/{player_id}`** - Get player details with all season stats

- **GET `/players/{player_id}/scouting_report`** - Generate AI scouting report

### Storylines

- **POST `/games/{game_id}/storylines`** - Generate AI storylines for a game

- **GET `/games/{game_id}/storylines`** - Get saved storylines for a game

## CSV Format

The CSV upload endpoint expects a CSV file with the following columns (column names are normalized, so variations are accepted):

**Required columns:**
- Player name (column name: `player`, `name`, `Player Name`, etc.)
- Team (`team`, `Team`, etc.)
- AB (at bats)
- H (hits)
- HR (home runs)

**Optional columns:**
- 2B or double (doubles)
- 3B or triple (triples)
- BB (walks)
- HBP (hit by pitch)
- SF (sacrifice fly)
- SH (sacrifice bunt)
- SO or K (strikeouts)
- R (runs)
- RBI (runs batted in)
- SB (stolen bases)
- CS (caught stealing)

The ingestion logic automatically normalizes column names, so variations like "SO" vs "K", "2B" vs "double", etc. are handled automatically.

## Database Schema

The application uses SQLModel (which builds on SQLAlchemy) with the following models:

- **Player** - Player information (name, team, league)
- **Game** - Game metadata (date, teams, league, season)
- **PlateAppearance** - Individual game stat lines per player
- **HitterTotal** - Season-long aggregated stats per player/league/season
- **GameStorylines** - AI-generated game storylines and summaries

## Database

By default, the application uses SQLite (`baseball_league.db` in the project root). The database is created automatically on first run.

To use PostgreSQL or Supabase:
1. Update `DATABASE_URL` in your `.env` file
2. Ensure the database is created and accessible
3. The application will automatically use the new database

## Stat Calculations

The API automatically computes the following statistics:

- **AVG** (Batting Average) = H / AB
- **OBP** (On-Base Percentage) = (H + BB + HBP) / (AB + BB + HBP + SF)
- **SLG** (Slugging Percentage) = TB / AB
- **OPS** (On-Base Plus Slugging) = OBP + SLG

Where:
- **TB** (Total Bases) = singles + 2×doubles + 3×triples + 4×home runs
- **Singles** = H - doubles - triples - HR
- **PA** (Plate Appearances) = AB + BB + HBP + SF + SH

## Development

The project structure:
```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app and endpoints
│   ├── models.py            # SQLModel database models
│   ├── schemas.py           # Pydantic response models
│   ├── database.py          # Database engine and session management
│   ├── ingest.py            # CSV parsing and ingestion logic
│   └── services/
│       ├── __init__.py
│       ├── stats.py         # Stat computation helpers
│       └── storylines.py    # AI storyline generation
├── requirements.txt
├── README.md
└── .env                     # Environment variables (create this)
```

## Troubleshooting

**Issue: OpenAI API errors**
- Ensure `OPENAI_API_KEY` is set in your `.env` file
- Verify your OpenAI API key is valid and has credits

**Issue: Database errors**
- Delete `baseball_league.db` to reset the database (all data will be lost)
- For Postgres, ensure the database exists and connection string is correct

**Issue: CSV upload fails**
- Check that required columns (player name, team, AB, H, HR) are present
- Ensure date format is YYYY-MM-DD
- Check server logs for specific row errors

## License

MIT

