/**
 * Team filter dropdown component for filtering leaderboards by team.
 */

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface TeamFilterProps {
  teams: string[];
  selectedTeam: string | null;
  onTeamChange: (team: string | null) => void;
  className?: string;
}

export function TeamFilter({ 
  teams, 
  selectedTeam, 
  onTeamChange,
  className = ""
}: TeamFilterProps) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <label className="font-medium text-sm whitespace-nowrap">Filter by Team:</label>
      <Select
        value={selectedTeam || "all"}
        onValueChange={(value) => onTeamChange(value === "all" ? null : value)}
      >
        <SelectTrigger className="w-[220px]">
          <SelectValue placeholder="Select team" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Teams</SelectItem>
          {teams.map(team => (
            <SelectItem key={team} value={team}>
              {team}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      {selectedTeam && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onTeamChange(null)}
          className="h-8 px-2 text-xs text-muted-foreground hover:text-foreground"
        >
          <X className="h-3 w-3 mr-1" />
          Clear filter
        </Button>
      )}
    </div>
  );
}

