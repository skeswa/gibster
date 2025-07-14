'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Calendar,
  RefreshCw,
  Settings,
  ExternalLink,
  Copy,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  AlertCircle,
  FileText,
  ChevronDown,
} from 'lucide-react';
import SyncJobLogs from '@/components/SyncJobLogs';

interface User {
  id: string;
  email: string;
  [key: string]: any;
}

interface Booking {
  id: string;
  name: string;
  start_time: string;
  end_time: string;
  studio: string;
  location: string;
  status: string;
  price?: number;
  record_url: string;
  last_seen: string;
}

interface SyncJob {
  id: string;
  status: string;
  progress?: string;
  bookings_synced: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  triggered_manually: boolean;
}

interface SyncStatus {
  job: SyncJob;
  last_sync_at?: string;
}

interface SyncHistory {
  jobs: SyncJob[];
}

interface DashboardProps {
  user: User;
  bookings: Booking[];
  calendarUrl: string;
}

const Dashboard: React.FC<DashboardProps> = ({
  user,
  bookings,
  calendarUrl,
}) => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [syncHistory, setSyncHistory] = useState<SyncJob[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string>('');
  const [isPolling, setIsPolling] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState<string>('');
  const [retryCount, setRetryCount] = useState(0);
  const [pollingIntervalId, setPollingIntervalId] =
    useState<NodeJS.Timeout | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [calendarInfoOpen, setCalendarInfoOpen] = useState(false);

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone, // Use user's local timezone
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatCompactDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const getStatusVariant = (
    status: string
  ): 'default' | 'secondary' | 'destructive' | 'outline' => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('confirmed') || statusLower.includes('completed'))
      return 'default';
    if (statusLower.includes('pending')) return 'secondary';
    if (statusLower.includes('canceled')) return 'destructive';
    return 'outline';
  };

  const getSyncStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className='h-4 w-4 text-green-600' />;
      case 'failed':
        return <XCircle className='h-4 w-4 text-red-600' />;
      case 'running':
        return <Loader2 className='h-4 w-4 animate-spin text-blue-600' />;
      case 'pending':
        return <Clock className='h-4 w-4 text-yellow-600' />;
      default:
        return <AlertCircle className='h-4 w-4 text-gray-600' />;
    }
  };

  // Fetch sync status
  const fetchSyncStatus = async () => {
    try {
      const response = await apiClient.get('/api/v1/user/sync/status');

      if (response.ok) {
        const status = await response.json();
        setSyncStatus(status);
      }
    } catch (error) {
      console.error('Failed to fetch sync status:', error);
    }
  };

  // Handle viewing logs
  const handleViewLogs = (jobId: string) => {
    setSelectedJobId(jobId);
    setShowLogsModal(true);
  };

  // Fetch sync history
  const fetchSyncHistory = async () => {
    try {
      const response = await apiClient.get('/api/v1/user/sync/history?limit=5');

      if (response.ok) {
        const history: SyncHistory = await response.json();
        setSyncHistory(history.jobs || []);
      }
    } catch (error) {
      console.error('Failed to fetch sync history:', error);
    }
  };

  // Start manual sync
  const handleSyncNow = async () => {
    setIsLoading(true);
    setSyncMessage('');
    setRetryCount(0);

    try {
      const response = await apiClient.post('/api/v1/user/sync');

      if (response.ok) {
        await response.json();
        setSyncMessage('Sync started successfully! Checking for updates...');
        setIsPolling(true);

        // Immediately fetch the initial status and history
        await Promise.all([fetchSyncStatus(), fetchSyncHistory()]);

        // Start polling for status updates after a short delay
        setTimeout(() => {
          let pollCount = 0;
          const maxPollCount = 200; // 5 minutes at 1.5 second intervals

          const interval = setInterval(async () => {
            pollCount++;

            try {
              const statusResponse = await apiClient.get(
                '/api/v1/user/sync/status'
              );

              if (statusResponse.ok) {
                const freshStatus = await statusResponse.json();
                setSyncStatus(freshStatus);

                // Refresh history periodically
                if (pollCount % 10 === 0) {
                  fetchSyncHistory();
                }

                // Update message based on current status
                if (freshStatus?.job?.status === 'running') {
                  setSyncMessage(
                    `Sync in progress... ${freshStatus.job.progress || 'Fetching your bookings from Gibney'}`
                  );
                }

                // Check the fresh status, not the stale component state
                if (
                  freshStatus?.job?.status === 'completed' ||
                  freshStatus?.job?.status === 'failed'
                ) {
                  clearInterval(interval);
                  setPollingIntervalId(null);
                  setIsLoading(false);
                  setIsPolling(false);

                  // Fetch final history
                  await fetchSyncHistory();

                  if (freshStatus.job.status === 'completed') {
                    setSyncMessage(
                      `Sync completed! ${freshStatus.job.bookings_synced} bookings were synced.`
                    );
                    // Refresh the page to show updated bookings
                    setTimeout(() => window.location.reload(), 2000);
                  } else {
                    setSyncMessage(
                      `Sync failed: ${freshStatus.job.error_message || 'Unknown error'}`
                    );

                    // Allow retry after failure
                    setRetryCount(prev => prev + 1);
                  }
                }
              } else {
                console.error('Failed to fetch sync status during polling');

                // If polling fails multiple times, stop
                if (pollCount > 5) {
                  clearInterval(interval);
                  setPollingIntervalId(null);
                  setIsLoading(false);
                  setIsPolling(false);
                  setSyncMessage(
                    'Failed to check sync status. Please refresh the page.'
                  );
                }
              }
            } catch (error) {
              console.error('Error during status polling:', error);
            }

            // Stop polling after max attempts
            if (pollCount >= maxPollCount) {
              clearInterval(interval);
              setPollingIntervalId(null);
              setIsLoading(false);
              setIsPolling(false);
              setSyncMessage(
                'Sync is taking longer than expected. It may still be running in the background. Please check back later.'
              );
            }
          }, 1500); // Poll every 1.5 seconds for more responsive updates

          // Store the interval ID so we can cancel it if needed
          setPollingIntervalId(interval);
        }, 500); // Wait 500ms before starting polling to allow job creation
      } else {
        const error = await response.json();
        setSyncMessage(
          `Failed to start sync: ${error.detail || 'Unknown error'}`
        );
        setIsLoading(false);

        // Allow retry
        setRetryCount(prev => prev + 1);
      }
    } catch (error) {
      setSyncMessage(
        'Failed to start sync. Please check your connection and try again.'
      );
      setIsLoading(false);
      setRetryCount(prev => prev + 1);
    }
  };

  // Handle canceling sync
  const handleCancelSync = () => {
    if (pollingIntervalId) {
      clearInterval(pollingIntervalId);
      setPollingIntervalId(null);
    }
    setIsPolling(false);
    setIsLoading(false);
    setSyncMessage(
      'Sync monitoring cancelled. The sync may still be running in the background.'
    );
  };

  // Fetch initial sync status and history
  useEffect(() => {
    fetchSyncStatus();
    fetchSyncHistory();
  }, []);

  // Auto-expand calendar info when sync history changes
  useEffect(() => {
    // If there's no sync history or very few items, collapse the calendar info
    // Otherwise, expand it
    setCalendarInfoOpen(syncHistory.length > 2);
  }, [syncHistory]);

  return (
    <div className='space-y-6'>
      <div className='grid gap-6 md:grid-cols-2'>
        {/* Calendar URL Card */}
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Calendar className='h-5 w-5' />
              Your Calendar Feed
            </CardTitle>
            <CardDescription>
              Subscribe to your Gibney bookings in your calendar app
            </CardDescription>
          </CardHeader>
          <CardContent>
            {calendarUrl ? (
              <div className='space-y-4'>
                {/* Quick subscription buttons */}
                <div className='space-y-3'>
                  <p className='text-sm font-medium'>Quick Add:</p>
                  <div className='flex flex-wrap gap-2'>
                    <Button asChild>
                      <a
                        href={`https://calendar.google.com/calendar/r?cid=${encodeURIComponent(calendarUrl.replace('https://', 'webcal://'))}`}
                        target='_blank'
                        rel='noopener noreferrer'
                      >
                        <Calendar className='mr-2 h-4 w-4' />
                        Google Calendar
                      </a>
                    </Button>
                    <Button
                      variant='outline'
                      onClick={() => {
                        const webcalUrl = calendarUrl.replace(
                          'https://',
                          'webcal://'
                        );
                        window.location.href = webcalUrl;
                      }}
                    >
                      <Calendar className='mr-2 h-4 w-4' />
                      Apple Calendar
                    </Button>
                    <Button variant='outline' asChild>
                      <a
                        href={`https://outlook.live.com/calendar/0/addfromweb?url=${encodeURIComponent(calendarUrl)}&name=${encodeURIComponent(`Gibster - ${user.email}`)}`}
                        target='_blank'
                        rel='noopener noreferrer'
                      >
                        <Calendar className='mr-2 h-4 w-4' />
                        Outlook
                      </a>
                    </Button>
                  </div>
                </div>

                {/* Manual copy section */}
                <div className='space-y-3'>
                  <p className='text-sm font-medium'>
                    Or copy the URL manually:
                  </p>
                  <div className='relative'>
                    <div className='flex items-center gap-2 rounded-md border bg-muted p-3 pr-20'>
                      <code className='text-xs break-all'>{calendarUrl}</code>
                    </div>
                    <Button
                      size='sm'
                      variant='outline'
                      className='absolute right-2 top-1/2 -translate-y-1/2'
                      onClick={() => {
                        navigator.clipboard
                          .writeText(calendarUrl)
                          .then(() => {
                            setCopyFeedback('Copied!');
                            setTimeout(() => setCopyFeedback(''), 2000);
                          })
                          .catch(() => {
                            setCopyFeedback('Failed to copy');
                            setTimeout(() => setCopyFeedback(''), 2000);
                          });
                      }}
                    >
                      {copyFeedback ? (
                        copyFeedback
                      ) : (
                        <>
                          <Copy className='h-4 w-4' />
                        </>
                      )}
                    </Button>
                  </div>
                </div>

                {/* Additional information about calendar sync - Collapsible */}
                <Collapsible
                  open={calendarInfoOpen}
                  onOpenChange={setCalendarInfoOpen}
                >
                  <div className='mt-6 border-t pt-4'>
                    <CollapsibleTrigger className='flex w-full items-center justify-between text-sm font-medium hover:text-primary transition-colors'>
                      <span>More information</span>
                      <ChevronDown
                        className={`h-4 w-4 transition-transform duration-200 ${calendarInfoOpen ? 'rotate-180' : ''}`}
                      />
                    </CollapsibleTrigger>
                    <CollapsibleContent className='mt-4 space-y-4'>
                      <div>
                        <h4 className='text-sm font-medium mb-3'>
                          How it works
                        </h4>
                        <div className='space-y-2 text-sm text-muted-foreground'>
                          <p className='flex items-start gap-2'>
                            <span className='text-primary'>•</span>
                            <span>
                              Your calendar automatically syncs with Gibney
                              every 2 hours
                            </span>
                          </p>
                          <p className='flex items-start gap-2'>
                            <span className='text-primary'>•</span>
                            <span>
                              New bookings, cancellations, and changes appear
                              automatically
                            </span>
                          </p>
                          <p className='flex items-start gap-2'>
                            <span className='text-primary'>•</span>
                            <span>
                              Most calendar apps check for updates every 2-24
                              hours
                            </span>
                          </p>
                          <p className='flex items-start gap-2'>
                            <span className='text-primary'>•</span>
                            <span>
                              You can manually refresh your calendar app to see
                              updates sooner
                            </span>
                          </p>
                        </div>
                      </div>
                    </CollapsibleContent>
                  </div>
                </Collapsible>
              </div>
            ) : (
              <div className='flex items-center justify-center py-8'>
                <Loader2 className='h-6 w-6 animate-spin text-muted-foreground' />
              </div>
            )}

            {calendarUrl && (
              <Alert className='mt-4'>
                <AlertCircle className='h-4 w-4' />
                <AlertDescription>
                  Pro tip: For instant updates, use the &quot;Sync Now&quot;
                  button in the settings card to manually refresh your bookings.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Sync Control Card */}
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <RefreshCw className='h-5 w-5' />
              Sync Settings
            </CardTitle>
            <CardDescription>Sync your latest Gibney bookings</CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Your calendar automatically updates every 2 hours, or you can
              manually sync now.
            </p>

            {syncStatus && syncStatus.last_sync_at && (
              <div className='flex items-center gap-2 text-sm text-muted-foreground'>
                <Clock className='h-4 w-4' />
                Last sync: {formatDate(syncStatus.last_sync_at)}
              </div>
            )}

            <div className='flex flex-wrap gap-3'>
              <Button
                onClick={isPolling ? handleCancelSync : handleSyncNow}
                disabled={isLoading}
                variant={isPolling ? 'destructive' : 'default'}
              >
                {isLoading ? (
                  <>
                    <Loader2 className='mr-2 h-4 w-4 animate-spin' />
                    Starting Sync...
                  </>
                ) : isPolling ? (
                  <>
                    <XCircle className='mr-2 h-4 w-4' />
                    Cancel Sync
                  </>
                ) : (
                  <>
                    <RefreshCw className='mr-2 h-4 w-4' />
                    Sync Now
                  </>
                )}
              </Button>

              <Button variant='outline' asChild>
                <Link href='/credentials'>
                  <Settings className='mr-2 h-4 w-4' />
                  Update Credentials
                </Link>
              </Button>
            </div>

            {/* Sync Status Display */}
            {syncStatus && (
              <div className='rounded-lg border bg-muted/50 p-4 space-y-3'>
                <div className='flex items-center justify-between'>
                  <p className='text-sm font-medium'>Sync Status</p>
                  <div className='flex items-center gap-2'>
                    {getSyncStatusIcon(syncStatus.job.status)}
                    <span className='text-sm capitalize'>
                      {syncStatus.job.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                {syncStatus.job.progress && (
                  <p className='text-sm text-muted-foreground'>
                    {syncStatus.job.progress}
                  </p>
                )}
                {syncStatus.job.bookings_synced > 0 && (
                  <p className='text-sm text-muted-foreground'>
                    Bookings synced: {syncStatus.job.bookings_synced}
                  </p>
                )}
                {syncStatus.job.error_message && (
                  <Alert className='bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900'>
                    <AlertCircle className='h-4 w-4 text-red-600 dark:text-red-400' />
                    <AlertDescription className='text-red-900 dark:text-red-200'>
                      {syncStatus.job.error_message ||
                        'An unknown error occurred. Please check the logs for details.'}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}

            {syncMessage && !syncMessage.includes('failed') && (
              <Alert>
                {isPolling ? (
                  <Loader2 className='h-4 w-4 animate-spin' />
                ) : (
                  <CheckCircle2 className='h-4 w-4' />
                )}
                <AlertDescription>{syncMessage}</AlertDescription>
              </Alert>
            )}

            {/* Retry button for failed syncs */}
            {retryCount > 0 &&
              !isLoading &&
              !isPolling &&
              syncMessage.includes('failed') && (
                <Button onClick={handleSyncNow} variant='outline' size='sm'>
                  <RefreshCw className='mr-2 h-4 w-4' />
                  Retry Sync
                </Button>
              )}

            {/* Sync History */}
            {syncHistory.length > 0 && (
              <div className='mt-4 space-y-2'>
                <p className='text-sm font-medium text-muted-foreground'>
                  Recent Sync History
                </p>
                <div className='space-y-1'>
                  {syncHistory.slice(0, 3).map(job => (
                    <div
                      key={job.id}
                      className='flex items-center justify-between rounded-md border bg-muted/30 px-3 py-2 text-sm'
                    >
                      <div className='flex items-center gap-2'>
                        {getSyncStatusIcon(job.status)}
                        <span className='text-muted-foreground'>
                          {formatDate(job.started_at)}
                        </span>
                      </div>
                      <div className='flex items-center gap-2'>
                        {job.bookings_synced > 0 && (
                          <span className='text-xs text-muted-foreground'>
                            {job.bookings_synced} bookings
                          </span>
                        )}
                        <Badge
                          variant={
                            job.status === 'completed'
                              ? 'default'
                              : job.status === 'failed'
                                ? 'destructive'
                                : 'secondary'
                          }
                          className='text-xs'
                        >
                          {job.status}
                        </Badge>
                        <Button
                          variant='ghost'
                          size='sm'
                          className='h-6 w-6 p-0'
                          onClick={() => handleViewLogs(job.id)}
                          title='View logs'
                        >
                          <FileText className='h-3 w-3' />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <p className='text-xs text-muted-foreground italic'>
              Manual sync may take a few moments to complete. The page will
              refresh automatically when finished.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Bookings Table */}
      <Card>
        <CardHeader>
          <CardTitle>Your Bookings ({bookings.length})</CardTitle>
          <CardDescription>
            All your Gibney dance studio bookings
          </CardDescription>
        </CardHeader>
        <CardContent>
          {bookings.length === 0 ? (
            <div className='flex flex-col items-center justify-center py-12 text-center'>
              <Calendar className='h-12 w-12 text-muted-foreground mb-4' />
              <p className='text-lg font-medium mb-2'>No bookings found</p>
              <p className='text-sm text-muted-foreground mb-4'>
                Sync your Gibney account to see your bookings here
              </p>
              <Button asChild>
                <Link href='/credentials'>
                  <Settings className='mr-2 h-4 w-4' />
                  Update Credentials
                </Link>
              </Button>
            </div>
          ) : (
            <div className='rounded-md border'>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Booking</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Studio</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead className='text-right'>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {bookings.map(booking => (
                    <TableRow key={booking.id}>
                      <TableCell className='font-medium'>
                        {booking.name}
                      </TableCell>
                      <TableCell>
                        {formatCompactDate(booking.start_time)}
                      </TableCell>
                      <TableCell>
                        <div className='text-sm'>
                          {formatTime(booking.start_time)} -{' '}
                          {formatTime(booking.end_time)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className='font-medium'>{booking.studio}</div>
                          <div className='text-sm text-muted-foreground'>
                            {booking.location}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(booking.status)}>
                          {booking.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {booking.price ? `$${booking.price}` : 'Free'}
                      </TableCell>
                      <TableCell className='text-right'>
                        <Button size='sm' variant='outline' asChild>
                          <a
                            href={booking.record_url}
                            target='_blank'
                            rel='noopener noreferrer'
                          >
                            <ExternalLink className='h-4 w-4' />
                          </a>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Sync Job Logs Modal */}
      {selectedJobId && (
        <SyncJobLogs
          jobId={selectedJobId}
          isOpen={showLogsModal}
          onClose={() => {
            setShowLogsModal(false);
            setSelectedJobId(null);
          }}
        />
      )}
    </div>
  );
};

export default Dashboard;
