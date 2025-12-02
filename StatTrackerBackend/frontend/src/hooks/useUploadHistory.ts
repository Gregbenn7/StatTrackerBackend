import { useState, useEffect } from "react";
import { UploadRecord } from "@/components/upload/UploadHistory";

const STORAGE_KEY = "hittrax_upload_history";
const MAX_HISTORY = 10;

export const useUploadHistory = () => {
  const [uploads, setUploads] = useState<UploadRecord[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setUploads(JSON.parse(stored));
      } catch (e) {
        console.error("Failed to parse upload history:", e);
      }
    }
  }, []);

  const addUpload = (upload: Omit<UploadRecord, "id" | "timestamp">) => {
    const newUpload: UploadRecord = {
      ...upload,
      id: crypto.randomUUID(),
      timestamp: new Date(),
    };

    const updatedUploads = [newUpload, ...uploads].slice(0, MAX_HISTORY);
    setUploads(updatedUploads);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedUploads));
  };

  const clearHistory = () => {
    setUploads([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  return { uploads, addUpload, clearHistory };
};