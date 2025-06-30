import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingProps {
  message?: string;
}

export default function Loading({ message = 'Loading...' }: LoadingProps) {
  return (
    <div className='flex flex-col items-center justify-center min-h-[50vh] space-y-4'>
      <Loader2 className='h-8 w-8 animate-spin text-primary' />
      <p className='text-sm text-muted-foreground'>{message}</p>
    </div>
  );
}
