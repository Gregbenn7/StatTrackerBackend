# Baseball League Stat Tracker

A full-stack application for managing a HitTrax-based adult baseball league. The application consists of a FastAPI backend API and a React frontend that handles game CSV uploads, computes season-long hitting statistics, provides leaderboards, and generates AI-powered storylines using OpenAI.

## 🎯 Current Status

**✅ Backend Refactoring Complete** - Clean architecture with in-memory storage
**✅ Frontend Services Refactored** - TypeScript types, API services, React Query hooks
**⚠️ Components Need Updates** - Components still use old API (see REFACTORING_SUMMARY.md)

## Features

### Backend (FastAPI)
- 📊 CSV game data ingestion from HitTrax exports
- 📈 Automatic stat computation (AVG, OBP, SLG, OPS, etc.)
- 🏆 Leaderboard endpoints with filtering
- 📝 AI-generated game storylines using OpenAI
- 👤 Player scouting reports
- 🔄 CORS support for frontend integration
- 💾 **In-memory storage** (data resets on server restart)

### Frontend (React)
- 🎨 Modern UI built with React, TypeScript, and Tailwind CSS
- 📱 Responsive design with shadcn/ui components
- 📊 Interactive leaderboards and player statistics
- 📤 CSV file upload interface for game data
- 🎮 Game history and storyline viewer
- 📈 Real-time data fetching with React Query
- 🧭 Client-side routing with React Router

## Installation

### Backend Setup

1. **Navigate to the project root directory**

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   FRONTEND_ORIGIN=http://localhost:8080
   ```

### Frontend Setup

1. **Navigate to the frontend directory**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**
   
   Make sure you have [Node.js](https://nodejs.org/) installed (v18 or higher recommended), then:
   ```bash
   npm install
   ```

3. **Configure frontend environment (optional)**
   
   Create a `.env` file in the `frontend/` directory to customize the API URL:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```
   
   If not set, the frontend defaults to `http://localhost:8000`.

## Running the Application

### Backend

Start the FastAPI server from the project root:
```bash
# Make sure your virtual environment is activated
uvicorn app.main:app --reload
```

The API will be available at:
- **API:** http://localhost:8000
- **Interactive API docs:** http://localhost:8000/docs
- **Alternative docs:** http://localhost:8000/redoc

### Frontend

Start the development server from the `frontend/` directory:
```bash
cd frontend
npm run dev
```

The frontend will be available at:
- **Web App:** http://localhost:8080

### Running Both (Development)

For local development, you'll need to run both servers simultaneously:

**Terminal 1 (Backend):**
```bash
# From project root
uvicorn app.main:app --reload
```

**Terminal 2 (Frontend):**
```bash
# From frontend directory
cd frontend
npm run dev
```

## Architecture

### Backend Structure

```
app/
├── core/                  # Core functionality
│   ├── config.py          # Settings using pydantic-settings
│   └── exceptions.py      # Custom exception classes
│
├── api/                   # API layer
│   ├── routes/            # API routes
│   │   ├── games.py       # Game endpoints
│   │   ├── players.py     # Player endpoints
│   │   ├── stats.py       # Stats/leaderboard endpoints
│   │   └── storylines.py  # Storyline endpoints
│   └── deps.py            # Dependency injection
│
├── models/                # Pydantic models
│   ├── player.py
│   ├── game.py
│   ├── plate_appearance.py
│   ├── stats.py
│   └── storyline.py
│
├── repositories/          # Data access layer
│   ├── game_repository.py
│   ├── player_repository.py
│   └── stats_repository.py
│
├── services/              # Business logic layer
│   ├── game_service.py
│   ├── player_service.py
│   ├── stats_service.py
│   ├── ingest_service.py
│   └── storyline_service.py
│
├── storage/               # In-memory storage
│   └── memory_store.py
│
└── utils/                 # Utility functions
    ├── csv_helpers.py
    └── stat_calculators.py
```

### Frontend Structure

```
src/
├── config/                # Configuration
│   ├── env.ts            # Environment variables
│   └── routes.ts         # Route constants
│
├── types/                 # TypeScript types
│   ├── game.types.ts
│   ├── player.types.ts
│   ├── stats.types.ts
│   └── api.types.ts
│
├── services/              # API service layer
│   ├── api.ts            # API client
│   ├── gameService.ts
│   ├── playerService.ts
│   ├── statsService.ts
│   └── teamService.ts
│
├── hooks/                 # React Query hooks
│   ├── useGames.ts
│   ├── usePlayers.ts
│   ├── useStats.ts
│   └── useTeams.ts
│
├── components/            # React components
├── pages/                 # Page components
└── lib/                   # Utilities
```

## API Endpoints

### Game Management

- **POST `/games/upload_csv`** - Upload a CSV file with game stats
  - Form data: `file` (CSV), `league`, `season`, `date_str` (YYYY-MM-DD), `home_team`, `away_team`
  
- **GET `/games`** - List recent games (supports `limit`, `offset`, `league`, `season` query params)

- **GET `/games/{game_id}`** - Get game details with plate appearances

### Statistics

- **GET `/stats/leaderboard`** - Get hitting leaderboard (ordered by OPS)
  - Query params: `league` (optional), `season` (optional)

### Players

- **GET `/players`** - List all players with stats
  - Query params: `league` (optional), `season` (optional), `team` (optional)

- **GET `/players/{player_id}`** - Get player details with all season stats

- **GET `/players/{player_id}/scouting_report`** - Generate AI scouting report

### Teams

- **GET `/teams`** - Get list of unique teams
  - Query params: `league` (optional)

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

## Data Storage

**⚠️ Important:** The application currently uses **in-memory storage**. All data persists only during runtime and will be lost when the server restarts. This is intentional for the current architecture - if you need persistent storage, you can integrate a database by modifying the storage layer.

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

## Troubleshooting

### Backend Issues

**Issue: OpenAI API errors**
- Ensure `OPENAI_API_KEY` is set in your `.env` file
- Verify your OpenAI API key is valid and has credits

**Issue: CORS errors**
- Ensure `FRONTEND_ORIGIN` in `.env` matches your frontend URL (default: `http://localhost:8080`)
- Restart the backend server after changing `.env` file

**Issue: CSV upload fails**
- Check that required columns (player name, team, AB, H, HR) are present
- Ensure date format is YYYY-MM-DD
- Check server logs for specific row errors

### Frontend Issues

**Issue: Frontend can't connect to backend**
- Ensure the backend is running on port 8000
- Check that `VITE_API_BASE_URL` in `frontend/.env` matches your backend URL
- Check browser console for CORS or network errors

**Issue: Dependencies installation fails**
- Ensure you have Node.js v18+ installed
- Try deleting `node_modules` and `package-lock.json`, then run `npm install` again

## Development

### Building for Production

**Frontend:**
```bash
cd frontend
npm run build
```

This creates an optimized production build in the `frontend/dist/` directory.

**Backend:**
```bash
# Production server (using uvicorn with workers)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Refactoring Notes

See `REFACTORING_SUMMARY.md` for details on the recent refactoring:
- Removed database dependencies
- Implemented in-memory storage
- Reorganized code structure
- Added React Query hooks
- TypeScript type system

## License

MIT
