"""Stat calculation utilities."""

from typing import Dict
from app.models.stats import HitterTotal


def compute_derived_stats(hitter_total: HitterTotal) -> HitterTotal:
    """
    Compute derived stats (singles, PA, TB, AVG, OBP, SLG, OPS) for a HitterTotal.
    
    Args:
        hitter_total: HitterTotal model to compute stats for
        
    Returns:
        Updated HitterTotal with computed stats
    """
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
) -> Dict[str, float | int]:
    """
    Compute derived stats from raw counting stats.
    
    Args:
        ab: At bats
        h: Hits
        double: Doubles
        triple: Triples
        hr: Home runs
        bb: Walks
        hbp: Hit by pitch
        sf: Sacrifice fly
        sh: Sacrifice bunt
        
    Returns:
        Dict with: singles, PA, TB, AVG, OBP, SLG, OPS
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


def get_game_avg(h: int, ab: int) -> float:
    """
    Compute batting average for a single game plate appearance.
    
    Args:
        h: Hits
        ab: At bats
        
    Returns:
        Batting average
    """
    if ab > 0:
        return round(h / ab, 3)
    return 0.0

