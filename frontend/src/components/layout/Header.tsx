import { Trophy } from "lucide-react";

export const Header = () => {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-card">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
            <Trophy className="h-6 w-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">HitTrax League Hub</h1>
            <p className="text-xs text-muted-foreground">Adult Baseball Analytics</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <select className="rounded-md border border-border bg-background px-3 py-2 text-sm">
            <option>Championship League</option>
            <option>Spring League</option>
            <option>Summer League</option>
          </select>
        </div>
      </div>
    </header>
  );
};
