import { useState, useRef } from "react";
import { Header } from "@/components/layout/Header";
import { HitterLeaderboard } from "@/components/stats/HitterLeaderboard";
import { TeamFilter } from "@/components/stats/TeamFilter";
import { GameCard } from "@/components/games/GameCard";
import { GameStorylineCard } from "@/components/games/GameStorylineCard";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { BarChart3, Users, CalendarDays, Upload, AlertCircle, RefreshCw, History, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { UploadHistory } from "@/components/upload/UploadHistory";
import { useUploadHistory } from "@/hooks/useUploadHistory";

// Import new hooks
import { useLeaderboard } from "@/hooks/useStats";
import { useTeams } from "@/hooks/useTeams";
import { useGames, useGameStorylines, useCheckStorylineExists, useUploadGameCsv, useCreateGameStorylines } from "@/hooks/useGames";
import type { UploadMetadata, LeaderboardEntry } from "@/types";

const Dashboard = () => {
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState("leaderboard");
  
  // Upload form fields (for CSV upload only)
  const [uploadLeague, setUploadLeague] = useState("");
  const [uploadSeason, setUploadSeason] = useState("");
  const [dateStr, setDateStr] = useState("");
  
  // View filters (for displaying data - optional, shows ALL if empty)
  const [viewLeague, setViewLeague] = useState("");
  const [viewSeason, setViewSeason] = useState("");
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const { uploads, addUpload, clearHistory } = useUploadHistory();

  // Use React Query hooks - use view filters (empty = show ALL data)
  const { data: leaderboardData = [], isLoading: isLoadingStats, error: statsError, refetch: refetchStats } = useLeaderboard(
    viewLeague.trim() || undefined,
    viewSeason.trim() || undefined,
    selectedTeam
  );
  const { data: teams = [], isLoading: isLoadingTeams } = useTeams(viewLeague.trim() || undefined, viewSeason.trim() || undefined);
  const { data: games = [], isLoading: isLoadingGames } = useGames(
    viewLeague.trim() || undefined,
    viewSeason.trim() || undefined
  );
  
  // STEP 1: Check if storyline exists (always run this first)
  const { 
    data: existsData, 
    isLoading: checkingExists 
  } = useCheckStorylineExists(
    selectedGameId || null
  );
  
  // STEP 2: Only fetch storyline if it exists
  const { 
    data: selectedStoryline, 
    isLoading: isLoadingStoryline,
    error: storylineError 
  } = useGameStorylines(
    selectedGameId || null,
    existsData === true  // CRITICAL: Only fetch if exists is true
  );
  
  const uploadMutation = useUploadGameCsv();
  const createStorylineMutation = useCreateGameStorylines();

  // Transform leaderboard data to match HitterLeaderboard component format
  const hitterStats = leaderboardData.map((entry: LeaderboardEntry) => ({
    player_name: entry.player_name,
    team_name: entry.team,
    games_played: entry.games,
    ab: entry.AB,
    h: entry.H,
    avg: entry.AVG,
    hr: entry.HR,
    rbi: entry.RBI,
    obp: entry.OBP,
    slg: entry.SLG,
    ops: entry.OPS,
  }));

  const handleGameClick = (gameId: string | number) => {
    setSelectedGameId(String(gameId));
    // Storylines will load automatically via the useGameStorylines hook
    // User can click "Generate Recap" button if none exist
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate upload form fields - teams are now auto-detected from CSV
    if (!uploadLeague.trim() || !uploadSeason.trim() || !dateStr) {
      const errorMsg = "All fields are required: League, Season, and Date. Teams are automatically detected from CSV.";
      toast({
        title: "Upload failed",
        description: errorMsg,
        variant: "destructive",
      });
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      return;
    }

    const metadata: UploadMetadata = {
      league: uploadLeague.trim(),
      season: uploadSeason.trim(),
      date_str: dateStr,
      // Teams are optional - will be auto-detected from CSV
    };

    try {
      await uploadMutation.mutateAsync({ file, metadata });

      // Add to upload history
        // Extract team names from response message if available
        const message = uploadMutation.data?.message || "";
        const teamMatch = message.match(/(\w+)\s+vs\s+(\w+)/);
        addUpload({
          fileName: file.name,
          teamName: teamMatch ? teamMatch[1] : "Unknown",
          opponent: teamMatch ? teamMatch[2] : "Unknown",
          gameDate: dateStr,
        });

      toast({
        title: "Upload successful",
        description: uploadMutation.data?.message || "CSV file processed successfully",
      });
      
      // Switch to leaderboard tab to show new data
      setSelectedTab("leaderboard");
      
      // Clear upload form fields only (keep view filters as they are)
      setDateStr("");
      setUploadLeague("");
      setUploadSeason("");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Upload failed";
      toast({
        title: "Upload failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const errorMessage = statsError instanceof Error ? statsError.message : null;

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-foreground">Baseball League Dashboard</h2>
          <p className="text-muted-foreground">
            {viewLeague ? `${viewLeague}${viewSeason ? ` - ${viewSeason} Season` : ""}` : "All Leagues & Seasons"}
          </p>
        </div>

        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-grid">
            <TabsTrigger value="leaderboard" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              <span className="hidden sm:inline">Leaderboard</span>
            </TabsTrigger>
            <TabsTrigger value="teams" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              <span className="hidden sm:inline">Teams</span>
            </TabsTrigger>
            <TabsTrigger value="games" className="flex items-center gap-2">
              <CalendarDays className="h-4 w-4" />
              <span className="hidden sm:inline">Games</span>
            </TabsTrigger>
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              <span className="hidden sm:inline">Upload</span>
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2">
              <History className="h-4 w-4" />
              <span className="hidden sm:inline">History</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="leaderboard" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Hitter Leaderboard</CardTitle>
                    <CardDescription>Top performers ranked by OPS</CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => refetchStats()}
                    disabled={isLoadingStats}
                    className="gap-2"
                  >
                    <RefreshCw className={`h-4 w-4 ${isLoadingStats ? "animate-spin" : ""}`} />
                    Refresh
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {errorMessage && (
                  <Alert variant="destructive" className="mb-4">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{errorMessage}</AlertDescription>
                  </Alert>
                )}
                
                {/* Team Filter - Show loading state or filter */}
                <div className="mb-6">
                  {isLoadingTeams ? (
                    <div className="text-sm text-muted-foreground">Loading teams...</div>
                  ) : teams.length > 0 ? (
                    <TeamFilter
                      teams={teams.map((t: any) => t.name)}
                      selectedTeam={selectedTeam}
                      onTeamChange={setSelectedTeam}
                    />
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      No teams found. Upload a CSV to get started.
                    </div>
                  )}
                </div>
                
                {isLoadingStats ? (
                  <div className="flex items-center justify-center py-8 text-muted-foreground">
                    Loading stats...
                  </div>
                ) : hitterStats.length === 0 ? (
                  <div className="flex items-center justify-center py-8 text-muted-foreground">
                    {selectedTeam 
                      ? `No stats available for ${selectedTeam}. Try selecting a different team or uploading CSV data.`
                      : "No stats available. Upload a CSV to get started."
                    }
                  </div>
                ) : (
                  <>
                    <HitterLeaderboard hitters={hitterStats} />
                    <div className="mt-4 text-sm text-muted-foreground">
                      Showing {hitterStats.length} player{hitterStats.length !== 1 ? "s" : ""}
                      {selectedTeam && ` from ${selectedTeam}`}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="teams" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Teams</CardTitle>
                <CardDescription>League standings and team statistics</CardDescription>
              </CardHeader>
              <CardContent>
                {isLoadingTeams ? (
                  <div className="flex items-center justify-center py-8 text-muted-foreground">
                    Loading teams...
                  </div>
                ) : teams.length === 0 ? (
                  <div className="flex items-center justify-center py-8 text-muted-foreground">
                    No teams found. Upload a CSV to get started.
                  </div>
                ) : (
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {teams.map((team, index) => (
                      <Card key={index} className="transition-all hover:shadow-md hover:border-primary/50">
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
                              <span className="text-muted-foreground">Record:</span>
                              <span className="font-semibold">{team.wins}-{team.losses}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Win %:</span>
                              <span className="font-semibold">{(team.win_pct * 100).toFixed(1)}%</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Runs Scored:</span>
                              <span className="font-semibold">{team.runs_scored}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Run Diff:</span>
                              <span className={`font-semibold ${team.run_differential >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {team.run_differential > 0 ? '+' : ''}{team.run_differential}
                              </span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="games" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent Games</CardTitle>
                <CardDescription>Game results and AI-powered recaps</CardDescription>
              </CardHeader>
              <CardContent>
                {isLoadingGames ? (
                  <div className="flex items-center justify-center py-8 text-muted-foreground">
                    Loading games...
                  </div>
                ) : games.length === 0 ? (
                  <div className="flex items-center justify-center py-8 text-muted-foreground">
                    No games found. Upload a CSV to get started.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {games.map((game) => (
                      <GameCard
                        key={game.id}
                        game={game}
                        onClick={() => handleGameClick(game.id)}
                      />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="upload" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Upload Game CSV</CardTitle>
                <CardDescription>
                  Upload HitTrax CSV files to automatically process game statistics
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {uploadMutation.isError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {uploadMutation.error instanceof Error
                        ? uploadMutation.error.message
                        : "Upload failed"}
                    </AlertDescription>
                  </Alert>
                )}
                
                  <div className="space-y-6">
                  <div className="rounded-lg border border-border bg-muted/30 p-4">
                    <p className="text-sm font-semibold mb-3">View Filters (optional - leave empty to see ALL data from all uploads)</p>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="filterLeague">League Filter</Label>
                        <Input
                          id="filterLeague"
                          placeholder="Leave empty to see all leagues"
                          value={viewLeague}
                          onChange={(e) => setViewLeague(e.target.value)}
                          disabled={uploadMutation.isPending}
                        />
                        <p className="text-xs text-muted-foreground">Filter view by league (optional - empty shows ALL)</p>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="filterSeason">Season Filter</Label>
                        <Input
                          id="filterSeason"
                          placeholder="Leave empty to see all seasons"
                          value={viewSeason}
                          onChange={(e) => setViewSeason(e.target.value)}
                          disabled={uploadMutation.isPending}
                        />
                        <p className="text-xs text-muted-foreground">Filter view by season (optional - empty shows ALL)</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <p className="text-sm font-semibold">Upload Game Data (teams are automatically detected from CSV)</p>
                    <p className="text-xs text-muted-foreground mb-4">
                      Ensure your CSV is in HitTrax format with two team sections. Teams are automatically detected from the header rows containing "Batting Order". The system will automatically detect and separate them.
                    </p>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      <div className="space-y-2">
                        <Label htmlFor="uploadLeague">League *</Label>
                        <Input
                          id="uploadLeague"
                          placeholder="e.g., Pnw Winter League"
                          value={uploadLeague}
                          onChange={(e) => setUploadLeague(e.target.value)}
                          disabled={uploadMutation.isPending}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="uploadSeason">Season *</Label>
                        <Input
                          id="uploadSeason"
                          placeholder="e.g., 2025"
                          value={uploadSeason}
                          onChange={(e) => setUploadSeason(e.target.value)}
                          disabled={uploadMutation.isPending}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="gameDate">Game Date *</Label>
                        <Input
                          id="gameDate"
                          type="date"
                          value={dateStr}
                          onChange={(e) => setDateStr(e.target.value)}
                          disabled={uploadMutation.isPending}
                          required
                        />
                      </div>
                      {/* Teams are now automatically detected from CSV - no input needed */}
                    </div>
                  </div>
                  
                  <div className="rounded-lg border-2 border-dashed border-border bg-muted/20 p-12 text-center">
                    <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
                    <h3 className="mt-4 text-lg font-semibold">Upload CSV File</h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Select a HitTrax CSV file to process game statistics
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".csv"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                    <Button 
                      className="mt-4" 
                      onClick={handleFileSelect}
                      disabled={uploadMutation.isPending}
                    >
                      {uploadMutation.isPending ? "Uploading..." : "Select File"}
                    </Button>
                  </div>

                  <div className="space-y-2 rounded-lg bg-primary/5 p-4 text-sm">
                    <p className="font-semibold text-primary">Features:</p>
                    <ul className="space-y-1 text-muted-foreground">
                      <li>• Automatic stat computation and aggregation</li>
                      <li>• Real-time leaderboard updates</li>
                      <li>• Player performance tracking</li>
                      <li>• Optional game metadata tracking</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Upload History</CardTitle>
                    <CardDescription>Recent CSV file uploads</CardDescription>
                  </div>
                  {uploads.length > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={clearHistory}
                    >
                      Clear History
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <UploadHistory uploads={uploads} />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      <Dialog open={!!selectedGameId} onOpenChange={() => {
        setSelectedGameId(null);
      }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Game Recap</DialogTitle>
          </DialogHeader>
          {/* Loading state while checking if recap exists */}
          {checkingExists ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-primary" />
              <p>Checking for game recap...</p>
            </div>
          ) : isLoadingStoryline ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-primary" />
              <p>Loading game recap...</p>
            </div>
          ) : createStorylineMutation.isPending ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-primary" />
              <p>Generating game recap...</p>
            </div>
          ) : createStorylineMutation.isError ? (
            <div className="flex flex-col items-center justify-center py-8 space-y-4">
              <p className="text-destructive font-semibold">Failed to generate game recap</p>
              <p className="text-muted-foreground text-sm text-center">
                {(createStorylineMutation.error as any)?.response?.data?.detail || 
                 (createStorylineMutation.error as Error)?.message ||
                 "Please check that OPENAI_API_KEY is configured in the backend."}
              </p>
              <p className="text-muted-foreground text-xs text-center">
                Contact your administrator to configure OpenAI API access.
              </p>
              <Button
                variant="outline"
                onClick={() => {
                  if (selectedGameId) {
                    createStorylineMutation.mutate(selectedGameId);
                  }
                }}
                disabled={createStorylineMutation.isPending}
              >
                {createStorylineMutation.isPending ? "Generating..." : "Try Again"}
              </Button>
            </div>
          ) : selectedStoryline ? (
            (() => {
              // Find the selected game to get team names and scores
              const selectedGame = games.find(g => String(g.id) === selectedGameId);
              return (
                <GameStorylineCard 
                  storyline={selectedStoryline}
                  onRegenerate={() => {
                    if (selectedGameId) {
                      createStorylineMutation.mutate(selectedGameId);
                    }
                  }}
                  isRegenerating={createStorylineMutation.isPending}
                  homeTeam={selectedGame?.home_team}
                  awayTeam={selectedGame?.away_team}
                  homeScore={selectedGame?.home_score}
                  awayScore={selectedGame?.away_score}
                />
              );
            })()
          ) : existsData === false ? (
            <div className="flex flex-col items-center justify-center py-8 space-y-4">
              <div className="text-center">
                <Sparkles className="h-12 w-12 mx-auto mb-4 text-primary opacity-50" />
                <p className="text-muted-foreground mb-6">
                  Generate an ESPN-style recap of this game powered by AI
                </p>
              </div>
              <Button
                onClick={() => {
                  if (selectedGameId) {
                    createStorylineMutation.mutate(selectedGameId);
                  }
                }}
                disabled={createStorylineMutation.isPending}
                size="lg"
                className="min-w-[200px]"
              >
                {createStorylineMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating Recap...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Game Recap
                  </>
                )}
              </Button>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 space-y-4">
              <p className="text-muted-foreground">Unable to load game recap.</p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Dashboard;
