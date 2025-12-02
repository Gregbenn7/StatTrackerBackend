import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Calendar, Users } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export interface UploadRecord {
  id: string;
  fileName: string;
  timestamp: Date;
  teamName?: string;
  opponent?: string;
  gameDate?: string;
}

interface UploadHistoryProps {
  uploads: UploadRecord[];
}

export const UploadHistory = ({ uploads }: UploadHistoryProps) => {
  if (uploads.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No upload history yet. Upload your first CSV to get started.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {uploads.map((upload) => (
        <Card key={upload.id} className="bg-muted/30">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                <CardTitle className="text-base">{upload.fileName}</CardTitle>
              </div>
              <Badge variant="secondary" className="text-xs">
                {formatDistanceToNow(new Date(upload.timestamp), { addSuffix: true })}
              </Badge>
            </div>
            {(upload.teamName || upload.opponent || upload.gameDate) && (
              <CardDescription className="flex flex-wrap gap-3 pt-2">
                {upload.teamName && (
                  <span className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {upload.teamName}
                  </span>
                )}
                {upload.opponent && (
                  <span className="text-muted-foreground">vs {upload.opponent}</span>
                )}
                {upload.gameDate && (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {upload.gameDate}
                  </span>
                )}
              </CardDescription>
            )}
          </CardHeader>
        </Card>
      ))}
    </div>
  );
}