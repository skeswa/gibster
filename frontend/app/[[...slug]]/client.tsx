'use client'

import dynamic from 'next/dynamic'

const App = dynamic(() => import('../../src/App'), { ssr: false })

export function ClientOnly(): React.JSX.Element {
  return <App />
}