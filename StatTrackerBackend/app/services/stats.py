from sqlmodel import Session, select
from typing import List, Optional
from app.models import HitterTotal, PlateAppearance, Player, Game


def compute_derived_stats(hitter_total: HitterTotal):
    """Compute derived stats (singles, PA, TB, AVG, OBP, SLG, OPS) for a HitterTotal."""
    # Singles = Hits - doubles - triples - HR
    hitter_total.singles = hitter_total.H - hitter_total.double - hitter_total.triple - hitter_total.HR
    
    # Plate appearances = AB + BB + HBP + SF + SH
    hitter_total.PA = hitter_total.AB + hitter_total.BB + hitter_total.HBP + hitter_total.SF + hitter_total.SH
    
    # Total bases = singles + 2*doubles + 3*triples + 4*HR
    hitter_total.TB = hitter_total.singles + 2 * hitter_total.double + 3 * hitter_total.triple + 4 * hitter_total.HR
    
    # AVG = H / AB (guard against AB=0)
    if hitter_total.AB > 0:
        hitter_total.AVG = round(hitter_total.H / hitter_total.AB, 3)
    else:
        hitter_total.AVG = 0.0
    
    # OBP = (H + BB + HBP) / (AB + BB + HBP + SF) (guard against denominator=0)
    obp_denom = hitter_total.AB + hitter_total.BB + hitter_total.HBP + hitter_total.SF
    if obp_denom > 0:
        hitter_total.OBP = round((hitter_total.H + hitter_total.BB + hitter_total.HBP) / obp_denom, 3)
    else:
        hitter_total.OBP = 0.0
    
    # SLG = TB / AB (guard against AB=0)
    if hitter_total.AB > 0:
        hitter_total.SLG = round(hitter_total.TB / hitter_total.AB, 3)
    else:
        hitter_total.SLG = 0.0
    
    # OPS = OBP + SLG
    hitter_total.OPS = round(hitter_total.OBP + hitter_total.SLG, 3)
    
    return hitter_total


def recompute_hitter_totals(session: Session, league: str, season: str):
    """Recompute all HitterTotal records for a given league and season."""
    # Get all plate appearances for this league/season
    statement = select(PlateAppearance, Game).join(
        Game, PlateAppearance.game_id == Game.id
    ).where(
        Game.league == league,
        Game.season == season
    )
    results = session.exec(statement).all()
    
    # Group by player_id
    player_stats = {}
    for plate_app, game in results:
        if plate_app.player_id not in player_stats:
            player_stats[plate_app.player_id] = {
                'AB': 0, 'H': 0, 'double': 0, 'triple': 0, 'HR': 0,
                'BB': 0, 'HBP': 0, 'SF': 0, 'SH': 0, 'K': 0,
                'R': 0, 'RBI': 0, 'SB': 0, 'CS': 0,
                'games': set()
            }
        
        stats = player_stats[plate_app.player_id]
        stats['AB'] += plate_app.AB
        stats['H'] += plate_app.H
        stats['double'] += plate_app.double
        stats['triple'] += plate_app.triple
        stats['HR'] += plate_app.HR
        stats['BB'] += plate_app.BB
        stats['HBP'] += plate_app.HBP
        stats['SF'] += plate_app.SF
        stats['SH'] += plate_app.SH
        stats['K'] += plate_app.K
        stats['R'] += plate_app.R
        stats['RBI'] += plate_app.RBI
        stats['SB'] += plate_app.SB
        stats['CS'] += plate_app.CS
        stats['games'].add(game.id)
    
    # Update or create HitterTotal records
    for player_id, stats in player_stats.items():
        # Try to find existing HitterTotal
        statement = select(HitterTotal).where(
            HitterTotal.player_id == player_id,
            HitterTotal.league == league,
            HitterTotal.season == season
        )
        hitter_total = session.exec(statement).first()
        
        if hitter_total is None:
            hitter_total = HitterTotal(
                player_id=player_id,
                league=league,
                season=season
            )
        
        # Update stats
        hitter_total.games = len(stats['games'])
        hitter_total.AB = stats['AB']
        hitter_total.H = stats['H']
        hitter_total.double = stats['double']
        hitter_total.triple = stats['triple']
        hitter_total.HR = stats['HR']
        hitter_total.BB = stats['BB']
        hitter_total.HBP = stats['HBP']
        hitter_total.SF = stats['SF']
        hitter_total.SH = stats['SH']
        hitter_total.K = stats['K']
        hitter_total.R = stats['R']
        hitter_total.RBI = stats['RBI']
        hitter_total.SB = stats['SB']
        hitter_total.CS = stats['CS']
        
        # Compute derived stats
        compute_derived_stats(hitter_total)
        
        session.add(hitter_total)
    
    session.commit()


def get_game_avg(h: int, ab: int) -> float:
    """Compute batting average for a single game plate appearance."""
    if ab > 0:
        return round(h / ab, 3)
    return 0.0


def compute_derived_stats_from_raw(
    ab: int,
    h: int,
    double: int,
    triple: int,
    hr: int,
    bb: int,
    hbp: int,
    sf: int,
    sh: int,
) -> dict:
    """
    Compute derived stats from raw counting stats.
    Returns dict with: singles, PA, TB, AVG, OBP, SLG, OPS
    """
    # Singles = Hits - doubles - triples - HR
    singles = h - double - triple - hr
    
    # Plate appearances = AB + BB + HBP + SF + SH
    pa = ab + bb + hbp + sf + sh
    
    # Total bases = singles + 2*doubles + 3*triples + 4*HR
    tb = singles + 2 * double + 3 * triple + 4 * hr
    
    # AVG = H / AB (guard against AB=0)
    if ab > 0:
        avg = round(h / ab, 3)
    else:
        avg = 0.0
    
    # OBP = (H + BB + HBP) / (AB + BB + HBP + SF) (guard against denominator=0)
    obp_denom = ab + bb + hbp + sf
    if obp_denom > 0:
        obp = round((h + bb + hbp) / obp_denom, 3)
    else:
        obp = 0.0
    
    # SLG = TB / AB (guard against AB=0)
    if ab > 0:
        slg = round(tb / ab, 3)
    else:
        slg = 0.0
    
    # OPS = OBP + SLG
    ops = round(obp + slg, 3)
    
    return {
        'singles': singles,
        'PA': pa,
        'TB': tb,
        'AVG': avg,
        'OBP': obp,
        'SLG': slg,
        'OPS': ops
    }


def get_player_stats_by_team(
    session: Session,
    league: Optional[str] = None,
    season: Optional[str] = None,
    team: Optional[str] = None
) -> List[dict]:
    """
    Get aggregated player stats grouped by (team, player_name, league, season).
    Returns list of dicts with all stats for each unique combination.
    """
    # Build query: join PlateAppearance with Game and Player
    statement = select(PlateAppearance, Game, Player).join(
        Game, PlateAppearance.game_id == Game.id
    ).join(
        Player, PlateAppearance.player_id == Player.id
    )
    
    # Apply filters
    conditions = []
    if league:
        conditions.append(Game.league == league)
    if season:
        conditions.append(Game.season == season)
    if team:
        conditions.append(PlateAppearance.team == team)
    
    if conditions:
        for condition in conditions:
            statement = statement.where(condition)
    
    results = session.exec(statement).all()
    
    # Group by (team, player_name, league, season)
    stats_dict = {}
    
    for plate_app, game, player in results:
        key = (plate_app.team, player.name, game.league, game.season)
        
        if key not in stats_dict:
            stats_dict[key] = {
                'player_id': player.id,
                'player_name': player.name,
                'team': plate_app.team,
                'league': game.league,
                'season': game.season,
                'games': set(),
                'AB': 0,
                'H': 0,
                'double': 0,
                'triple': 0,
                'HR': 0,
                'BB': 0,
                'HBP': 0,
                'SF': 0,
                'SH': 0,
                'K': 0,
                'R': 0,
                'RBI': 0,
                'SB': 0,
                'CS': 0,
            }
        
        stats = stats_dict[key]
        stats['AB'] += plate_app.AB
        stats['H'] += plate_app.H
        stats['double'] += plate_app.double
        stats['triple'] += plate_app.triple
        stats['HR'] += plate_app.HR
        stats['BB'] += plate_app.BB
        stats['HBP'] += plate_app.HBP
        stats['SF'] += plate_app.SF
        stats['SH'] += plate_app.SH
        stats['K'] += plate_app.K
        stats['R'] += plate_app.R
        stats['RBI'] += plate_app.RBI
        stats['SB'] += plate_app.SB
        stats['CS'] += plate_app.CS
        stats['games'].add(game.id)
    
    # Convert to list and compute derived stats
    result_list = []
    for key, stats in stats_dict.items():
        stats['games'] = len(stats['games'])
        
        # Compute derived stats
        derived = compute_derived_stats_from_raw(
            ab=stats['AB'],
            h=stats['H'],
            double=stats['double'],
            triple=stats['triple'],
            hr=stats['HR'],
            bb=stats['BB'],
            hbp=stats['HBP'],
            sf=stats['SF'],
            sh=stats['SH'],
        )
        
        stats.update(derived)
        result_list.append(stats)
    
    return result_list

