
import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
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
    const initializedRef = useRef(false);

    // Fetch the real user profile from the backend
    const fetchUserProfile = async () => {
        try {
            const userData = await api.fetchMe();
            setUser(userData);
            localStorage.setItem("user", JSON.stringify(userData));
        } catch (e) {
            // Token invalid or expired - clean up
            localStorage.removeItem("access_token");
            localStorage.removeItem("user");
            setUser(null);
        }
    };

    useEffect(() => {
        if (initializedRef.current) return;
        initializedRef.current = true;

        const token = localStorage.getItem("access_token");
        if (token) {
            // Validate token by fetching real user data from backend
            fetchUserProfile().finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    const signIn = async (email: string, password: string) => {
        try {
            const data = await api.login(email, password);
            localStorage.setItem("access_token", data.access_token);
            // Fetch real user profile from /auth/me
            await fetchUserProfile();
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
