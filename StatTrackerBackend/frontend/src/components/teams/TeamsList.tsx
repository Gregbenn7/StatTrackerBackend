import { Team } from "@/types/league";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users } from "lucide-react";

interface TeamsListProps {
  teams: Team[];
  onTeamClick?: (teamId: string) => void;
}

export const TeamsList = ({ teams, onTeamClick }: TeamsListProps) => {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {teams.map((team) => (
        <Card
          key={team.id}
          className="cursor-pointer transition-all hover:shadow-md hover:border-primary/50"
          onClick={() => onTeamClick?.(team.id)}
        >
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                <Users className="h-4 w-4 text-primary" />
              </div>
              {team.name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Record</span>
                <span className="font-semibold">8-4</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Runs Scored</span>
                <span className="font-semibold">96</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Runs Allowed</span>
                <span className="font-semibold">78</span>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
