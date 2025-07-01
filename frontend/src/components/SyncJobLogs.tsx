'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { SyncJobLog, SyncJobLogsResponse } from '@/types/sync';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Loader2,
  FileText,
  AlertCircle,
  Info,
  AlertTriangle,
  XCircle,
} from 'lucide-react';

interface SyncJobLogsProps {
  jobId: string;
  isOpen: boolean;
  onClose: () => void;
}

const SyncJobLogs: React.FC<SyncJobLogsProps> = ({
  jobId,
  isOpen,
  onClose,
}) => {
  const [logs, setLogs] = useState<SyncJobLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [levelFilter, setLevelFilter] = useState<string>('ALL');
  const [page, setPage] = useState(1);
  const [totalLogs, setTotalLogs] = useState(0);
  const limit = 100;

  const fetchLogs = async () => {
    if (!jobId) return;

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      });

      if (levelFilter !== 'ALL') {
        params.append('level', levelFilter);
      }

      const response = await apiClient.get(
        `/api/v1/user/sync/job/${jobId}/logs?${params}`
      );

      if (response.ok) {
        const data: SyncJobLogsResponse = await response.json();
        setLogs(data.logs);
        setTotalLogs(data.total);
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to fetch logs');
      }
    } catch (err) {
      setError('Failed to fetch logs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && jobId) {
      fetchLogs();
    }
  }, [isOpen, jobId, levelFilter, page]);

  const getLogIcon = (level: string) => {
    switch (level) {
      case 'ERROR':
        return <XCircle className='h-4 w-4 text-red-500' />;
      case 'WARNING':
        return <AlertTriangle className='h-4 w-4 text-yellow-500' />;
      case 'INFO':
        return <Info className='h-4 w-4 text-blue-500' />;
      case 'DEBUG':
        return <FileText className='h-4 w-4 text-gray-500' />;
      default:
        return <AlertCircle className='h-4 w-4 text-gray-500' />;
    }
  };

  const getLevelVariant = (
    level: string
  ): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (level) {
      case 'ERROR':
        return 'destructive';
      case 'WARNING':
        return 'secondary';
      case 'INFO':
        return 'default';
      case 'DEBUG':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className='max-w-4xl max-h-[80vh]'>
        <DialogHeader>
          <DialogTitle>Sync Job Logs</DialogTitle>
          <DialogDescription>
            Detailed logs for sync job {jobId.slice(0, 8)}...
          </DialogDescription>
        </DialogHeader>

        <div className='space-y-4'>
          {/* Filters */}
          <div className='flex items-center justify-between'>
            <Select value={levelFilter} onValueChange={setLevelFilter}>
              <SelectTrigger className='w-[180px]'>
                <SelectValue placeholder='Filter by level' />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value='ALL'>All Levels</SelectItem>
                <SelectItem value='ERROR'>Errors Only</SelectItem>
                <SelectItem value='WARNING'>Warnings</SelectItem>
                <SelectItem value='INFO'>Info</SelectItem>
                <SelectItem value='DEBUG'>Debug</SelectItem>
              </SelectContent>
            </Select>

            <div className='text-sm text-muted-foreground'>
              Showing {logs.length} of {totalLogs} logs
            </div>
          </div>

          {/* Logs */}
          <ScrollArea className='h-[400px] w-full rounded-md border p-4'>
            {loading && (
              <div className='flex items-center justify-center py-8'>
                <Loader2 className='h-6 w-6 animate-spin' />
              </div>
            )}

            {error && (
              <div className='flex items-center justify-center py-8 text-red-500'>
                <AlertCircle className='h-5 w-5 mr-2' />
                {error}
              </div>
            )}

            {!loading && !error && logs.length === 0 && (
              <div className='flex items-center justify-center py-8 text-muted-foreground'>
                No logs found
              </div>
            )}

            {!loading && !error && logs.length > 0 && (
              <div className='space-y-3'>
                {logs.map(log => (
                  <div
                    key={log.id}
                    className='flex flex-col space-y-2 border-b pb-3 last:border-0'
                  >
                    <div className='flex items-start justify-between'>
                      <div className='flex items-center space-x-2'>
                        {getLogIcon(log.level)}
                        <Badge
                          variant={getLevelVariant(log.level)}
                          className='text-xs'
                        >
                          {log.level}
                        </Badge>
                        <span className='text-xs text-muted-foreground'>
                          {formatTimestamp(log.timestamp)}
                        </span>
                      </div>
                    </div>

                    <div className='text-sm'>{log.message}</div>

                    {log.details && Object.keys(log.details).length > 0 && (
                      <details className='text-xs'>
                        <summary className='cursor-pointer text-muted-foreground hover:text-foreground'>
                          View details
                        </summary>
                        <pre className='mt-2 p-2 bg-muted rounded overflow-x-auto'>
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>

          {/* Pagination */}
          {totalLogs > limit && (
            <div className='flex items-center justify-between'>
              <Button
                variant='outline'
                size='sm'
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1 || loading}
              >
                Previous
              </Button>

              <span className='text-sm text-muted-foreground'>
                Page {page} of {Math.ceil(totalLogs / limit)}
              </span>

              <Button
                variant='outline'
                size='sm'
                onClick={() => setPage(p => p + 1)}
                disabled={page >= Math.ceil(totalLogs / limit) || loading}
              >
                Next
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SyncJobLogs;
