'use client';

import { useEffect, useState } from 'react';
import { isLoggedIn } from '@/lib/auth';
import UserMenu from './UserMenu';
import LoginButton from './LoginButton';
import Link from 'next/link';

export default function NavBar() {
    const [authenticated, setAuthenticated] = useState<boolean | null>(null);

    useEffect(() => {
        setAuthenticated(isLoggedIn());
    }, []);

    if (authenticated === null) {
        return <div className="h-16 border-b border-white/5 bg-[#0a0a0f]/80 backdrop-blur-md"></div>;
    }

    return (
        <header className="sticky top-0 z-50 h-16 border-b border-white/5 bg-[#0a0a0f]/80 backdrop-blur-md flex items-center justify-between px-6">
            <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
                    DC
                </div>
                <Link href={authenticated ? "/app" : "/"} className="text-xl font-semibold text-white tracking-tight">
                    Debate Colosseum
                </Link>
            </div>
            <div className="flex items-center">
                {authenticated ? <UserMenu /> : <LoginButton />}
            </div>
        </header>
    );
}
