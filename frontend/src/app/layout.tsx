import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Silly Merchants',
  description: 'Agent vs. Agents Arena',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
} 