export const metadata = {
  title: 'Gibster - Booking Management',
  description: 'Gibney booking management system',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}