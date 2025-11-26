import { useState, useEffect, useRef } from "react";
import { Header } from "@/components/layout/Header";
import { HitterLeaderboard } from "@/components/stats/HitterLeaderboard";
import { GameCard } from "@/components/games/GameCard";
import { GameStorylineCard } from "@/components/games/GameStorylineCard";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { mockGames, mockStorylines } from "@/data/mockData";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { BarChart3, Users, CalendarDays, Upload, AlertCircle, RefreshCw, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { uploadCSV, getTotals, PlayerStats, fetchTeams, fetchGames, fetchGameStorylines, createGameStorylines } from "@/services/api";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { UploadHistory } from "@/components/upload/UploadHistory";
import { useUploadHistory } from "@/hooks/useUploadHistory";

const Dashboard = () => {
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState("leaderboard");
  const [hitterStats, setHitterStats] = useState<PlayerStats[]>([]);
  const [teams, setTeams] = useState<string[]>([]);
  const [games, setGames] = useState<any[]>([]);
  const [selectedStoryline, setSelectedStoryline] = useState<any>(null);
  const [isLoadingStoryline, setIsLoadingStoryline] = useState(false);
  const [storylineError, setStorylineError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingTeams, setIsLoadingTeams] = useState(false);
  const [isLoadingGames, setIsLoadingGames] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [league, setLeague] = useState("");
  const [season, setSeason] = useState("");
  const [dateStr, setDateStr] = useState("");
  const [homeTeam, setHomeTeam] = useState("");
  const [awayTeam, setAwayTeam] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const { uploads, addUpload, clearHistory } = useUploadHistory();

  useEffect(() => {
    loadStats();
    loadTeams();
    loadGames();
  }, [league]);

  useEffect(() => {
    loadStats();
    loadGames();
  }, [league, season]);

  const loadStats = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const stats = await getTotals(league.trim() || undefined, season.trim() || undefined);
      setHitterStats(stats);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load stats";
      setError(errorMessage);
      toast({
        title: "Error loading stats",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadTeams = async () => {
    setIsLoadingTeams(true);
    try {
      const teamList = await fetchTeams(league.trim() || undefined);
      setTeams(teamList);
    } catch (err) {
      console.error("Failed to load teams:", err);
      setTeams([]);
    } finally {
      setIsLoadingTeams(false);
    }
  };

  const loadGames = async () => {
    setIsLoadingGames(true);
    try {
      const gamesList = await fetchGames(league.trim() || undefined, season.trim() || undefined);
      setGames(gamesList || []);
    } catch (err) {
      console.error("Failed to load games:", err);
      setGames([]);
    } finally {
      setIsLoadingGames(false);
    }
  };

  const handleGameClick = async (gameId: string | number) => {
    setSelectedGameId(String(gameId));
    setIsLoadingStoryline(true);
    setSelectedStoryline(null);
    setStorylineError(null);
    
    try {
      // Try to fetch existing storylines
      let storyline = await fetchGameStorylines(gameId);
      
      // If no storylines exist, create them
      if (!storyline) {
        toast({
          title: "Generating game recap...",
          description: "This may take a moment",
        });
        try {
          storyline = await createGameStorylines(gameId);
          toast({
            title: "Recap generated!",
            description: "Game recap is ready",
          });
        } catch (createErr) {
          console.error("Failed to create storylines:", createErr);
          const createErrorMsg = createErr instanceof Error ? createErr.message : "Failed to generate recap";
          setStorylineError(createErrorMsg);
          throw createErr;
        }
      }
      
      setSelectedStoryline(storyline);
    } catch (err) {
      console.error("Failed to load game storylines:", err);
      const errorMessage = err instanceof Error ? err.message : "Failed to load game recap";
      setStorylineError(errorMessage);
      toast({
        title: "Error loading game recap",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoadingStoryline(false);
    }
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);

    // Validate upload form fields - all required
    if (!league.trim() || !season.trim() || !dateStr || !homeTeam.trim() || !awayTeam.trim()) {
      const errorMsg = "All fields are required: League, Season, Date, Home Team, and Away Team";
      setError(errorMsg);
      toast({
        title: "Upload failed",
        description: errorMsg,
        variant: "destructive",
      });
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      return;
    }

    try {
      console.log("Uploading CSV:", {
        fileName: file.name,
        league,
        season,
        dateStr,
        homeTeam,
        awayTeam,
      });
      await uploadCSV(file, {
        league,
        season,
        date_str: dateStr,
        home_team: homeTeam,
        away_team: awayTeam,
      });

      // Add to upload history
      addUpload({
        fileName: file.name,
        teamName: homeTeam,
        opponent: awayTeam,
        gameDate: dateStr,
      });

      toast({
        title: "Upload successful",
        description: "CSV file processed successfully",
      });
      
      // Reload stats, teams, and games after successful upload
      await loadStats();
      await loadTeams();
      await loadGames();
      
      // Clear form fields
      setDateStr("");
      setHomeTeam("");
      setAwayTeam("");
      
      // Switch to leaderboard tab to show updated stats
      setSelectedTab("leaderboard");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Upload failed";
      setError(errorMessage);
      toast({
        title: "Upload failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-foreground">Baseball League Dashboard</h2>
          <p className="text-muted-foreground">
            {league ? `${league}${season ? ` - ${season} Season` : ""}` : "All Leagues"}
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
                    onClick={loadStats}
                    disabled={isLoading}
                    className="gap-2"
                  >
                    <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
                    Refresh
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {error && (
                  <Alert variant="destructive" className="mb-4">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
                {isLoading ? (
                  <div className="flex items-center justify-center py-8 text-muted-foreground">
                    Loading stats...
                  </div>
                ) : hitterStats.length === 0 ? (
                  <div className="flex items-center justify-center py-8 text-muted-foreground">
                    No stats available. Upload a CSV to get started.
                  </div>
                ) : (
                  <HitterLeaderboard hitters={hitterStats} />
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
                    {teams.map((teamName, index) => (
                      <Card key={index} className="transition-all hover:shadow-md hover:border-primary/50">
                        <CardHeader className="pb-3">
                          <CardTitle className="flex items-center gap-2 text-lg">
                            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                              <Users className="h-4 w-4 text-primary" />
                            </div>
                            {teamName}
                          </CardTitle>
                        </CardHeader>
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
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
                
                <div className="space-y-6">
                  <div className="rounded-lg border border-border bg-muted/30 p-4">
                    <p className="text-sm font-semibold mb-3">View Filters (optional - leave empty to see all data)</p>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="filterLeague">League Filter</Label>
                        <Input
                          id="filterLeague"
                          placeholder="e.g., Pnw Winter League"
                          value={league}
                          onChange={(e) => setLeague(e.target.value)}
                          disabled={isUploading}
                        />
                        <p className="text-xs text-muted-foreground">Filter view by league (optional)</p>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="filterSeason">Season Filter</Label>
                        <Input
                          id="filterSeason"
                          placeholder="e.g., 2025"
                          value={season}
                          onChange={(e) => setSeason(e.target.value)}
                          disabled={isUploading}
                        />
                        <p className="text-xs text-muted-foreground">Filter view by season (optional)</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <p className="text-sm font-semibold">Upload Game Data (required fields)</p>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      <div className="space-y-2">
                        <Label htmlFor="uploadLeague">League *</Label>
                        <Input
                          id="uploadLeague"
                          placeholder="e.g., Pnw Winter League"
                          value={league}
                          onChange={(e) => setLeague(e.target.value)}
                          disabled={isUploading}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="uploadSeason">Season *</Label>
                        <Input
                          id="uploadSeason"
                          placeholder="e.g., 2025"
                          value={season}
                          onChange={(e) => setSeason(e.target.value)}
                          disabled={isUploading}
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
                          disabled={isUploading}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="homeTeam">Home Team *</Label>
                        <Input
                          id="homeTeam"
                          placeholder="e.g., Blue Jays"
                          value={homeTeam}
                          onChange={(e) => setHomeTeam(e.target.value)}
                          disabled={isUploading}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="awayTeam">Away Team *</Label>
                        <Input
                          id="awayTeam"
                          placeholder="e.g., Red Sox"
                          value={awayTeam}
                          onChange={(e) => setAwayTeam(e.target.value)}
                          disabled={isUploading}
                          required
                        />
                      </div>
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
                      disabled={isUploading}
                    >
                      {isUploading ? "Uploading..." : "Select File"}
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
        setSelectedStoryline(null);
        setStorylineError(null);
      }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Game Recap</DialogTitle>
          </DialogHeader>
          {isLoadingStoryline ? (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              Loading game recap...
            </div>
          ) : storylineError ? (
            <div className="flex flex-col items-center justify-center py-8 space-y-4">
              <p className="text-destructive font-semibold">Error loading recap</p>
              <p className="text-muted-foreground text-sm text-center">{storylineError}</p>
              <p className="text-muted-foreground text-xs text-center">
                {storylineError.includes("OpenAI") || storylineError.includes("API key")
                  ? "Please configure OPENAI_API_KEY in the backend .env file to generate recaps."
                  : "Please try again or check the backend logs for more details."}
              </p>
            </div>
          ) : selectedStoryline ? (
            <GameStorylineCard storyline={selectedStoryline} />
          ) : (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              No recap available for this game.
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Dashboard;
