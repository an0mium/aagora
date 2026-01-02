import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'aragora live - Real-time Nomic Loop Dashboard',
  description: 'Watch aragora\'s self-improving nomic loop in real-time',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
