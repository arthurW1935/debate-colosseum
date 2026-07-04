import type { Metadata } from 'next';
import { GeistSans } from 'geist/font/sans';
import { Source_Serif_4 } from 'next/font/google';
import './globals.css';

const sourceSerif = Source_Serif_4({
  subsets: ['latin'],
  variable: '--font-source-serif',
});

export const metadata: Metadata = {
  title: 'Debate Colosseum',
  description: 'Multi-agent AI for complex business decisions',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${GeistSans.className} ${GeistSans.variable} ${sourceSerif.variable} bg-[var(--app-bg)] text-[var(--text-primary)] antialiased`}>
        {children}
      </body>
    </html>
  );
}
