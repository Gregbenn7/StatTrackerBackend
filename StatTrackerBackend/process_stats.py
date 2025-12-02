#!/usr/bin/env python3
"""
Process baseball game CSV files and generate hitter totals and combined games CSV.
This script reads all CSV files from ./raw_games/ and outputs processed data to ./output/
"""

import os
import csv
import logging
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RAW_GAMES_DIR = Path("./raw_games")
OUTPUT_DIR = Path("./output")

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)


def safe_int(value, default=0):
    """Safely convert value to int, handling NaN, None, and empty strings."""
    if value is None:
        return default
    try:
        s = str(value).strip()
        if s == "" or s.lower() == "nan" or s.lower() == "none":
            return default
        return int(float(s))
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Safely convert value to float, handling NaN, None, and empty strings."""
    if value is None:
        return default
    try:
        s = str(value).strip()
        if s == "" or s.lower() == "nan" or s.lower() == "none":
            return default
        return float(s)
    except (ValueError, TypeError):
        return default


def normalize_column_name(col: str) -> str:
    """Normalize column names by stripping whitespace."""
    if col is None:
        return ""
    return str(col).strip()


def process_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Process a single CSV file and return list of cleaned rows.
    Never crashes on bad data - logs errors and continues.
    """
    rows = []
    
    try:
        logger.info(f"Processing file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)
            delimiter = ',' if sample.count(',') > sample.count(';') else ';'
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Normalize column names
            original_columns = reader.fieldnames
            if not original_columns:
                logger.warning(f"No columns found in {file_path}")
                return rows
            
            normalized_columns = {col: normalize_column_name(col) for col in original_columns}
            
            row_count = 0
            for row in reader:
                try:
                    # Create normalized row
                    cleaned_row = {}
                    for old_col, new_col in normalized_columns.items():
                        cleaned_row[new_col] = row.get(old_col, "")
                    
                    # Add metadata
                    cleaned_row['_source_file'] = file_path.name
                    cleaned_row['_processed_at'] = datetime.now().isoformat()
                    
                    rows.append(cleaned_row)
                    row_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing row in {file_path}: {e}")
                    continue
            
            logger.info(f"Successfully processed {row_count} rows from {file_path}")
            
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
    
    return rows


def aggregate_hitter_totals(all_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate stats by (player_name, team) and compute totals.
    Handles missing columns gracefully.
    """
    logger.info("Aggregating hitter totals...")
    
    # Group by player and team
    player_stats = defaultdict(lambda: {
        'games': set(),
        'AB': 0,
        'H': 0,
        '2B': 0,
        '3B': 0,
        'HR': 0,
        'BB': 0,
        'HBP': 0,
        'SF': 0,
        'SH': 0,
        'SO': 0,
        'K': 0,
        'R': 0,
        'RBI': 0,
        'SB': 0,
        'CS': 0,
    })
    
    # Common column name mappings
    name_cols = ['player', 'player_name', 'name', 'batter', 'hitter', 'tetons']
    team_cols = ['team', 'team_name', 'team_name']
    
    for row in all_rows:
        try:
            # Find player name
            player_name = None
            for col in name_cols:
                val = row.get(col, "").strip()
                if val:
                    player_name = val
                    break
            
            if not player_name:
                continue
            
            # Find team
            team = None
            for col in team_cols:
                val = row.get(col, "").strip()
                if val:
                    team = val
                    break
            
            if not team:
                team = "Unknown"
            
            key = (player_name, team)
            stats = player_stats[key]
            
            # Track unique games
            source_file = row.get('_source_file', '')
            if source_file:
                stats['games'].add(source_file)
            
            # Aggregate numeric stats
            stats['AB'] += safe_int(row.get('AB', row.get('ab', 0)))
            stats['H'] += safe_int(row.get('H', row.get('h', 0)))
            stats['2B'] += safe_int(row.get('2B', row.get('2b', row.get('double', 0))))
            stats['3B'] += safe_int(row.get('3B', row.get('3b', row.get('triple', 0))))
            stats['HR'] += safe_int(row.get('HR', row.get('hr', 0)))
            stats['BB'] += safe_int(row.get('BB', row.get('bb', 0)))
            stats['HBP'] += safe_int(row.get('HBP', row.get('hbp', 0)))
            stats['SF'] += safe_int(row.get('SF', row.get('sf', 0)))
            stats['SH'] += safe_int(row.get('SH', row.get('sh', 0)))
            stats['SO'] += safe_int(row.get('SO', row.get('so', 0)))
            stats['K'] += safe_int(row.get('K', row.get('k', 0)))
            stats['R'] += safe_int(row.get('R', row.get('r', 0)))
            stats['RBI'] += safe_int(row.get('RBI', row.get('rbi', 0)))
            stats['SB'] += safe_int(row.get('SB', row.get('sb', 0)))
            stats['CS'] += safe_int(row.get('CS', row.get('cs', 0)))
            
        except Exception as e:
            logger.warning(f"Error aggregating row: {e}")
            continue
    
    # Compute derived stats and prepare output
    totals = []
    for (player_name, team), stats in player_stats.items():
        # Combine SO and K (some files use one, some use the other)
        total_k = stats['SO'] + stats['K']
        
        # Compute singles
        singles = stats['H'] - stats['2B'] - stats['3B'] - stats['HR']
        
        # Compute plate appearances
        PA = stats['AB'] + stats['BB'] + stats['HBP'] + stats['SF'] + stats['SH']
        
        # Compute total bases
        TB = singles + 2 * stats['2B'] + 3 * stats['3B'] + 4 * stats['HR']
        
        # Compute AVG
        AVG = round(stats['H'] / stats['AB'], 3) if stats['AB'] > 0 else 0.0
        
        # Compute OBP
        obp_denom = stats['AB'] + stats['BB'] + stats['HBP'] + stats['SF']
        OBP = round((stats['H'] + stats['BB'] + stats['HBP']) / obp_denom, 3) if obp_denom > 0 else 0.0
        
        # Compute SLG
        SLG = round(TB / stats['AB'], 3) if stats['AB'] > 0 else 0.0
        
        # Compute OPS
        OPS = round(OBP + SLG, 3)
        
        totals.append({
            'player_name': player_name,
            'team': team,
            'games': len(stats['games']),
            'AB': stats['AB'],
            'H': stats['H'],
            'singles': singles,
            '2B': stats['2B'],
            '3B': stats['3B'],
            'HR': stats['HR'],
            'BB': stats['BB'],
            'HBP': stats['HBP'],
            'SF': stats['SF'],
            'SH': stats['SH'],
            'K': total_k,
            'R': stats['R'],
            'RBI': stats['RBI'],
            'SB': stats['SB'],
            'CS': stats['CS'],
            'PA': PA,
            'TB': TB,
            'AVG': AVG,
            'OBP': OBP,
            'SLG': SLG,
            'OPS': OPS,
        })
    
    logger.info(f"Aggregated totals for {len(totals)} players")
    return totals


def write_hitter_totals(totals: List[Dict[str, Any]]):
    """Write hitter totals to CSV file."""
    output_file = OUTPUT_DIR / "hitter_totals.csv"
    
    if not totals:
        logger.warning("No totals to write")
        # Write empty file with headers
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'player_name', 'team', 'games', 'AB', 'H', 'singles', '2B', '3B', 'HR',
                'BB', 'HBP', 'SF', 'SH', 'K', 'R', 'RBI', 'SB', 'CS',
                'PA', 'TB', 'AVG', 'OBP', 'SLG', 'OPS'
            ])
            writer.writeheader()
        return
    
    fieldnames = list(totals[0].keys())
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(totals)
        
        logger.info(f"Wrote {len(totals)} hitter totals to {output_file}")
    except Exception as e:
        logger.error(f"Error writing hitter totals: {e}")


def write_all_games_combined(all_rows: List[Dict[str, Any]]):
    """Write all game rows to a combined CSV file."""
    output_file = OUTPUT_DIR / "all_games_combined.csv"
    
    if not all_rows:
        logger.warning("No game rows to write")
        return
    
    # Get all unique fieldnames from all rows
    fieldnames = set()
    for row in all_rows:
        fieldnames.update(row.keys())
    
    # Remove metadata fields from CSV output (keep them internal)
    fieldnames.discard('_source_file')
    fieldnames.discard('_processed_at')
    
    fieldnames = sorted(list(fieldnames))
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in all_rows:
                # Create clean row without metadata
                clean_row = {k: v for k, v in row.items() if k not in ['_source_file', '_processed_at']}
                writer.writerow(clean_row)
        
        logger.info(f"Wrote {len(all_rows)} game rows to {output_file}")
    except Exception as e:
        logger.error(f"Error writing combined games file: {e}")


def main():
    """Main processing function."""
    logger.info("="*60)
    logger.info("Starting stats processing")
    logger.info("="*60)
    
    # Check if raw_games directory exists
    if not RAW_GAMES_DIR.exists():
        logger.warning(f"Raw games directory not found: {RAW_GAMES_DIR}")
        logger.info("Creating directory...")
        RAW_GAMES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    csv_files = list(RAW_GAMES_DIR.glob("*.csv"))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {RAW_GAMES_DIR}")
        logger.info("Creating empty output files...")
        write_hitter_totals([])
        return
    
    logger.info(f"Found {len(csv_files)} CSV file(s) to process")
    
    # Process all files
    all_rows = []
    for csv_file in csv_files:
        rows = process_csv_file(csv_file)
        all_rows.extend(rows)
    
    logger.info(f"Total rows processed: {len(all_rows)}")
    
    # Aggregate hitter totals
    totals = aggregate_hitter_totals(all_rows)
    
    # Write output files
    write_hitter_totals(totals)
    write_all_games_combined(all_rows)
    
    logger.info("="*60)
    logger.info("Stats processing completed successfully")
    logger.info("="*60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error in process_stats.py: {e}", exc_info=True)
        exit(1)

