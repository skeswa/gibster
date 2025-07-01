export interface SyncJob {
  id: string;
  status: string;
  progress?: string;
  bookings_synced: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  triggered_manually: boolean;
}

export interface SyncJobLog {
  id: string;
  sync_job_id: string;
  timestamp: string;
  level: string;
  message: string;
  details?: Record<string, any>;
}

export interface SyncJobLogsResponse {
  logs: SyncJobLog[];
  total: number;
  page: number;
  limit: number;
}
