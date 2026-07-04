import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Debate Colosseum',
  description: 'Multi-agent AI for complex business decisions',
};

import NavBar from '@/components/NavBar';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-[#0a0a0f] text-white antialiased min-h-screen flex flex-col`}>
        <NavBar />
        <main className="flex-1">
          {children}
        </main>
      </body>
    </html>
  );
}
