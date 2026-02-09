
import React from 'react';

interface AuthLayoutProps {
    children: React.ReactNode;
    title: string;
    subtitle?: string;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children, title, subtitle }) => {
    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-background relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-background z-0">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[100px] animate-pulse" />
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-secondary/20 rounded-full blur-[100px] animate-pulse delay-1000" />
            </div>

            <div className="relative z-10 w-full max-w-md p-6">
                <div className="bg-card border border-white/10 rounded-2xl shadow-2xl backdrop-blur-xl p-8">
                    <div className="text-center mb-8">
                        <h1 className="text-3xl font-black text-white mb-2 tracking-tight">{title}</h1>
                        {subtitle && <p className="text-muted text-sm">{subtitle}</p>}
                    </div>
                    {children}
                </div>
            </div>
        </div>
    );
};
