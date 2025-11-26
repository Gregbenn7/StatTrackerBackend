import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CalendarIcon } from "lucide-react";

interface GameCardProps {
  game: {
    id: number;
    league: string;
    season: string;
    date: string;
    home_team: string;
    away_team: string;
  };
  onClick?: () => void;
}

export const GameCard = ({ game, onClick }: GameCardProps) => {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <Card
      className="cursor-pointer transition-all hover:shadow-md hover:border-primary/50"
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">
            {game.away_team} @ {game.home_team}
          </CardTitle>
          <Badge variant="outline" className="flex items-center gap-1">
            <CalendarIcon className="h-3 w-3" />
            {formatDate(game.date)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>Click to view box score and AI recap</span>
          <span className="text-xs">Game #{game.id}</span>
        </div>
      </CardContent>
    </Card>
  );
};
