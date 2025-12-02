import { useState } from "react";
import { ArrowUpDown, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface PlayerStats {
  player_name: string;
  team_name: string;
  games_played: number;
  ab: number;
  h: number;
  avg: number;
  hr: number;
  rbi: number;
  obp: number;
  slg: number;
  ops: number;
}

interface HitterLeaderboardProps {
  hitters: PlayerStats[];
  onPlayerClick?: (playerId: string) => void;
}

type SortKey = keyof Pick<PlayerStats, "avg" | "ops" | "hr" | "rbi" | "h">;

export const HitterLeaderboard = ({ hitters, onPlayerClick }: HitterLeaderboardProps) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState<SortKey>("ops");
  const [sortDesc, setSortDesc] = useState(true);

  const filteredHitters = hitters
    .filter((h) => h.player_name?.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => {
      const aVal = a[sortBy] || 0;
      const bVal = b[sortBy] || 0;
      return sortDesc ? bVal - aVal : aVal - bVal;
    });

  const handleSort = (key: SortKey) => {
    if (sortBy === key) {
      setSortDesc(!sortDesc);
    } else {
      setSortBy(key);
      setSortDesc(true);
    }
  };

  const formatStat = (value: number, decimals: number = 3) => {
    return value.toFixed(decimals);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search players..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="stats-table">
          <thead>
            <tr>
              <th className="sticky left-0 bg-table-header">Player</th>
              <th>Team</th>
              <th className="text-center">G</th>
              <th className="text-center">AB</th>
              <th className="text-center">H</th>
              <th className="cursor-pointer text-center" onClick={() => handleSort("avg")}>
                <div className="flex items-center justify-center gap-1">
                  AVG <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="cursor-pointer text-center" onClick={() => handleSort("hr")}>
                <div className="flex items-center justify-center gap-1">
                  HR <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="cursor-pointer text-center" onClick={() => handleSort("rbi")}>
                <div className="flex items-center justify-center gap-1">
                  RBI <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="text-center">OBP</th>
              <th className="text-center">SLG</th>
              <th className="cursor-pointer text-center" onClick={() => handleSort("ops")}>
                <div className="flex items-center justify-center gap-1">
                  OPS <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredHitters.map((hitter, index) => (
              <tr
                key={`${hitter.player_name}-${index}`}
                className="cursor-pointer"
              >
                <td className="sticky left-0 bg-card font-medium">{hitter.player_name}</td>
                <td className="text-muted-foreground">{hitter.team_name}</td>
                <td className="stat-number text-center">{hitter.games_played}</td>
                <td className="stat-number text-center">{hitter.ab}</td>
                <td className="stat-number text-center">{hitter.h}</td>
                <td className="stat-number text-center">{formatStat(hitter.avg)}</td>
                <td className="stat-number text-center font-bold text-accent">{hitter.hr}</td>
                <td className="stat-number text-center">{hitter.rbi}</td>
                <td className="stat-number text-center">{formatStat(hitter.obp)}</td>
                <td className="stat-number text-center">{formatStat(hitter.slg)}</td>
                <td className="stat-number text-center font-bold text-primary">
                  {formatStat(hitter.ops)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <p>Showing {filteredHitters.length} players</p>
        <p>Sorted by {sortBy.toUpperCase()} {sortDesc ? "↓" : "↑"}</p>
      </div>
    </div>
  );
};
