import React from 'react';

interface LoadingProps {
  message?: string;
}

export default function Loading({ message = 'Loading...' }: LoadingProps) {
  return (
    <div className='loading'>
      <div className='spinner'></div>
      <p>{message}</p>
    </div>
  );
}
