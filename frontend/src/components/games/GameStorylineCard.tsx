import { GameStoryline } from "@/types/league";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, TrophyIcon } from "lucide-react";

interface GameStorylineCardProps {
  storyline: GameStoryline;
}

export const GameStorylineCard = ({ storyline }: GameStorylineCardProps) => {
  return (
    <Card className="border-accent/20">
      <CardHeader className="space-y-4">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent/10">
            <Sparkles className="h-5 w-5 text-accent" />
          </div>
          <div className="flex-1">
            <Badge variant="secondary" className="mb-2">
              AI-Generated Recap
            </Badge>
            <h2 className="text-2xl font-bold leading-tight">{storyline.primary_headline}</h2>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {storyline.recap_body && storyline.recap_body.trim() ? (
          <div className="prose prose-sm max-w-none">
            {storyline.recap_body.split("\n\n").filter(p => p.trim()).map((paragraph, idx) => (
              <p key={idx} className="text-foreground/90 leading-relaxed">
                {paragraph.trim()}
              </p>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground italic">No recap available for this game.</p>
        )}

        {storyline.key_moments && storyline.key_moments.length > 0 && (
          <div className="border-t border-border pt-4">
            <h3 className="mb-3 font-semibold text-foreground">Key Moments</h3>
            <ul className="space-y-2">
              {storyline.key_moments.map((moment, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-foreground/80">
                  <span className="mt-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                    {idx + 1}
                  </span>
                  <span>{moment}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {storyline.player_of_game && storyline.player_of_game.trim() && (
          <div className="flex items-center gap-2 rounded-lg bg-accent/5 p-4">
            <TrophyIcon className="h-5 w-5 text-accent" />
            <div>
              <p className="text-xs font-medium text-muted-foreground">Player of the Game</p>
              <p className="font-bold text-accent">{storyline.player_of_game}</p>
            </div>
          </div>
        )}

        {storyline.social_captions && storyline.social_captions.length > 0 && (
          <div className="border-t border-border pt-4">
            <h3 className="mb-3 text-sm font-semibold text-foreground">Social Media Captions</h3>
            <div className="space-y-2">
              {storyline.social_captions.map((caption, idx) => (
                <div
                  key={idx}
                  className="rounded-md bg-muted/50 p-3 text-sm text-foreground/90 font-medium"
                >
                  {caption}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
