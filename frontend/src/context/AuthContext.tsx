
import React, { createContext, useContext, useEffect, useState } from 'react';
import * as api from '../api';

interface User {
    id: number;
    email: string;
    full_name?: string;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    signIn: (email: string, password: string) => Promise<{ error: any }>;
    signUp: (email: string, password: string, fullName?: string) => Promise<{ error: any }>;
    signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Simple session check: check if token and user info exist
        const token = localStorage.getItem("access_token");
        const storedUser = localStorage.getItem("user");

        if (token && storedUser) {
            try {
                setUser(JSON.parse(storedUser));
            } catch (e) {
                console.error("Failed to parse stored user", e);
                localStorage.removeItem("access_token");
                localStorage.removeItem("user");
            }
        }
        setLoading(false);
    }, []);

    const signIn = async (email: string, password: string) => {
        try {
            const data = await api.login(email, password);
            localStorage.setItem("access_token", data.access_token);
            // In a real app, you'd fetch the user info after login
            // For now, let's just set a dummy user or wait for a fetchUser endpoint
            const dummyUser = { id: 1, email };
            setUser(dummyUser);
            localStorage.setItem("user", JSON.stringify(dummyUser));
            return { error: null };
        } catch (error: any) {
            return { error: error.response?.data?.detail || "Login failed" };
        }
    };

    const signUp = async (email: string, password: string, fullName?: string) => {
        try {
            await api.signup(email, password, fullName);
            // After signup, automatically log in
            return await signIn(email, password);
        } catch (error: any) {
            return { error: error.response?.data?.detail || "Signup failed" };
        }
    };

    const signOut = async () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        setUser(null);
    };

    const value = {
        user,
        loading,
        signIn,
        signUp,
        signOut,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
