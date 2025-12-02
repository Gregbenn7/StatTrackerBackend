import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { GameStoryline } from "@/types/league";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { 
  Sparkles, 
  Trophy, 
  Target,
  TrendingUp,
  Share2,
  Copy,
  Check,
  Loader2
} from "lucide-react";
import { toast } from "sonner";
import * as gameService from "@/services/gameService";

interface GameStorylineCardProps {
  storyline: GameStoryline;
  onRegenerate?: () => void;
  isRegenerating?: boolean;
  homeTeam?: string;
  awayTeam?: string;
  homeScore?: number;
  awayScore?: number;
}

export const GameStorylineCard = ({ 
  storyline,
  onRegenerate,
  isRegenerating = false,
  homeTeam: propHomeTeam,
  awayTeam: propAwayTeam,
  homeScore: propHomeScore,
  awayScore: propAwayScore
}: GameStorylineCardProps) => {
  const [copied, setCopied] = useState(false);

  // Fetch game details if not fully provided
  const needsGameData = !propHomeTeam || !propAwayTeam || 
    propHomeScore === undefined || propAwayScore === undefined;

  const { data: gameData } = useQuery({
    queryKey: ['game', storyline.game_id],
    queryFn: () => gameService.fetchGame(Number(storyline.game_id)),
    enabled: needsGameData,
  });

  // Use props or fallback to fetched data
  const finalHomeTeam = propHomeTeam || gameData?.home_team || 'Home';
  const finalAwayTeam = propAwayTeam || gameData?.away_team || 'Away';
  
  // Handle scores - use nullish coalescing to distinguish 0 (valid) from undefined
  const finalHomeScore = propHomeScore !== undefined 
    ? propHomeScore 
    : (gameData?.home_score !== undefined ? gameData.home_score : null);
  const finalAwayScore = propAwayScore !== undefined 
    ? propAwayScore 
    : (gameData?.away_score !== undefined ? gameData.away_score : null);

  // Only show score if we have valid data
  const hasValidScores = finalHomeScore !== null && finalAwayScore !== null;

  // Copy to clipboard
  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success('Copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  // Share function
  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: storyline.primary_headline,
          text: storyline.recap_body.substring(0, 200),
          url: window.location.href,
        });
        toast.success('Shared successfully!');
      } catch (err) {
        // User cancelled share
      }
    }
  };

  // Parse recap into sections
  const sections = parseRecap(storyline.recap_body);

  return (
    <Card className="border-2 overflow-hidden">
      {/* Header with gradient */}
      <div className="bg-gradient-to-r from-primary to-primary/80 p-6 text-white">
        <div className="flex items-start justify-between mb-4">
          <Badge variant="secondary" className="bg-white/20 text-white border-0">
            <Sparkles className="h-3 w-3 mr-1" />
            AI-Generated Recap
          </Badge>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-white hover:bg-white/20"
              onClick={() => handleCopy(storyline.recap_body)}
            >
              {copied ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
            {navigator.share && (
              <Button
                variant="ghost"
                size="sm"
                className="text-white hover:bg-white/20"
                onClick={handleShare}
              >
                <Share2 className="h-4 w-4" />
              </Button>
            )}
            {onRegenerate && (
              <Button
                variant="ghost"
                size="sm"
                className="text-white hover:bg-white/20"
                onClick={onRegenerate}
                disabled={isRegenerating}
              >
                {isRegenerating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  'Regenerate'
                )}
              </Button>
            )}
          </div>
        </div>

        {/* Headline */}
        <h1 className="text-3xl md:text-4xl font-bold mb-3 leading-tight">
          {storyline.primary_headline}
        </h1>

        {/* Game Score - Show if we have valid team names and scores */}
        {finalHomeTeam && finalAwayTeam && hasValidScores && (
          <div className="mt-4 flex items-center justify-center gap-3 text-white/90">
            <span className="text-xl font-semibold">{finalHomeTeam}</span>
            <span className="text-3xl font-bold">{finalHomeScore}</span>
            <span className="text-white/80">-</span>
            <span className="text-3xl font-bold">{finalAwayScore}</span>
            <span className="text-xl font-semibold">{finalAwayTeam}</span>
          </div>
        )}
        
        {/* Fallback: Show just team names if scores not available */}
        {finalHomeTeam && finalAwayTeam && !hasValidScores && (
          <div className="mt-4 flex items-center justify-center gap-3 text-white/80 text-lg">
            <span>{finalHomeTeam}</span>
            <span>vs</span>
            <span>{finalAwayTeam}</span>
          </div>
        )}
      </div>

      <CardContent className="p-6 space-y-8">
        {/* Opening Summary */}
        {sections.summary && (
          <div>
            <p className="text-lg leading-relaxed text-foreground/90">
              {sections.summary}
            </p>
          </div>
        )}

        {/* Full Recap Body */}
        {storyline.recap_body && storyline.recap_body.trim() && !sections.summary && (
          <div className="prose prose-lg max-w-none">
            {storyline.recap_body.split("\n\n").filter(p => p.trim()).map((paragraph, idx) => (
              <p key={idx} className="text-foreground/90 leading-relaxed mb-4">
                {paragraph.trim()}
              </p>
            ))}
          </div>
        )}

        <Separator />

        {/* Key Moments */}
        {(sections.keyMoments && sections.keyMoments.length > 0) || (storyline.key_moments && storyline.key_moments.length > 0) ? (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Target className="h-5 w-5 text-primary" />
              <h2 className="text-2xl font-bold">Key Moments</h2>
            </div>
            <div className="space-y-4">
              {(sections.keyMoments || storyline.key_moments || []).map((moment, idx) => (
                <div
                  key={idx}
                  className="flex gap-4 p-4 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                >
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <span className="text-sm font-bold text-primary">
                        {idx + 1}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm leading-relaxed flex-1">{moment}</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {/* Star Performers - extract from player_of_game */}
        {storyline.player_of_game && (
          <>
            <Separator />
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Trophy className="h-5 w-5 text-amber-500" />
                <h2 className="text-2xl font-bold">Star Performers</h2>
              </div>
              <div className="flex flex-wrap gap-3">
                {/* Try to extract multiple players from player_of_game string */}
                {(() => {
                  const playerText = storyline.player_of_game;
                  // Try to extract player names (look for patterns like "Player 1, Player 2" or "Player 1 and Player 2")
                  const players = playerText
                    .replace(/^Top performers:?\s*/i, '')
                    .replace(/was the standout player/i, '')
                    .split(/[,&]|and/)
                    .map(p => p.trim())
                    .filter(p => p.length > 0 && !p.toLowerCase().includes('player'));
                  
                  // If we found multiple players, show them separately
                  if (players.length > 1) {
                    return players.map((player, idx) => (
                      <div
                        key={idx}
                        className={`px-6 py-3 bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 rounded-full ${
                          idx === 0 ? 'ring-2 ring-amber-400' : ''
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          {idx === 0 && (
                            <Trophy className="h-4 w-4 text-amber-600" />
                          )}
                          <span className="font-semibold text-amber-900">
                            {player}
                          </span>
                        </div>
                      </div>
                    ));
                  }
                  
                  // Single player - show in centered card
                  return (
                    <div className="flex items-center gap-2 rounded-lg bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 p-4">
                      <Trophy className="h-5 w-5 text-amber-600" />
                      <div>
                        <p className="text-xs font-medium text-amber-700">Player of the Game</p>
                        <p className="font-bold text-amber-900 text-lg">{playerText}</p>
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>
          </>
        )}

        {/* Team Analysis */}
        {sections.teamNotes && (
          <>
            <Separator />
            <div>
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="h-5 w-5 text-primary" />
                <h2 className="text-2xl font-bold">Team Analysis</h2>
              </div>
              <div className="p-4 bg-blue-50/50 rounded-lg border-l-4 border-primary">
                <p className="leading-relaxed">{sections.teamNotes}</p>
              </div>
            </div>
          </>
        )}

        {/* Closing Line */}
        {sections.closing && (
          <>
            <Separator />
            <div className="text-center">
              <p className="text-lg font-medium italic text-muted-foreground">
                "{sections.closing}"
              </p>
            </div>
          </>
        )}

        {/* Social Media Captions */}
        {storyline.social_captions && storyline.social_captions.length > 0 && (
          <>
            <Separator />
            <div>
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
          </>
        )}

        {/* Timestamp */}
        <div className="pt-4 text-center border-t">
          <p className="text-xs text-muted-foreground">
            Generated {new Date(storyline.created_at).toLocaleString()} • 
            Powered by AI
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

// Helper function to parse recap into sections
function parseRecap(recap: string) {
  const sections: {
    summary?: string;
    keyMoments?: string[];
    standoutPlayers?: string;
    teamNotes?: string;
    closing?: string;
  } = {};

  if (!recap || !recap.trim()) {
    return sections;
  }

  // Split by markdown headers
  const lines = recap.split('\n');
  let currentSection = 'summary';
  let buffer: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();
    
    if (trimmed.startsWith('####') || trimmed.startsWith('###') || trimmed.startsWith('##')) {
      // Save previous section
      if (buffer.length > 0) {
        const content = buffer.join(' ').trim();
        if (currentSection === 'summary') sections.summary = content;
        else if (currentSection === 'teamNotes') sections.teamNotes = content;
        else if (currentSection === 'closing') sections.closing = content;
      }
      buffer = [];
      
      // Determine new section
      const lower = trimmed.toLowerCase();
      if (lower.includes('key') || lower.includes('moment')) {
        currentSection = 'keyMoments';
        sections.keyMoments = [];
      } else if (lower.includes('team') || lower.includes('note') || lower.includes('analysis')) {
        currentSection = 'teamNotes';
      } else if (lower.includes('closing') || lower.includes('conclusion')) {
        currentSection = 'closing';
      } else if (lower.includes('standout') || lower.includes('player')) {
        currentSection = 'standoutPlayers';
      }
    } else if (trimmed.startsWith('-') || trimmed.startsWith('*') || trimmed.match(/^\d+[.)]\s+/)) {
      // Bullet point or numbered list - add to key moments
      const cleaned = trimmed
        .replace(/^[-*]\s*/, '')
        .replace(/^\d+[.)]\s+/, '')
        .replace(/\*\*/g, '')
        .trim();
      if (cleaned && sections.keyMoments) {
        sections.keyMoments.push(cleaned);
      } else if (cleaned && currentSection === 'keyMoments') {
        if (!sections.keyMoments) sections.keyMoments = [];
        sections.keyMoments.push(cleaned);
      }
    } else if (trimmed && !trimmed.startsWith('#')) {
      buffer.push(trimmed);
    }
  }

  // Save last section
  if (buffer.length > 0) {
    const content = buffer.join(' ').trim();
    if (currentSection === 'summary') sections.summary = content;
    else if (currentSection === 'teamNotes') sections.teamNotes = content;
    else if (currentSection === 'closing') sections.closing = content;
  }

  return sections;
}
