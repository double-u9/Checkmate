import type { Metadata } from 'next';
import '../styles/globals.css';

export const metadata: Metadata = {
  title: 'Aethelred | Chess Strategy Analyzer',
  description: 'AI-powered chess analysis with computer vision, tactical explanations, and opponent profiling',
  keywords: ['chess', 'AI', 'analysis', 'computer vision', 'strategy', 'stockfish'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen text-slate-100 antialiased">
        <div className="grid-bg scan-lines relative min-h-screen">{children}</div>
      </body>
    </html>
  );
}
