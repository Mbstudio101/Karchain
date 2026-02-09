
import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { ArrowRight, Loader2 } from 'lucide-react';

export const SignUp: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const { signUp } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        setLoading(true);

        try {
            const { error } = await signUp(email, password);
            if (error) throw error;
            // Depending on Supabase settings, might need to confirm email.
            // For now, assume auto-login or redirect to login.
            navigate('/');
        } catch (err: any) {
            setError(typeof err === 'string' ? err : err.message || "An unexpected error occurred");
        } finally {
            setLoading(false);
        }
    };

    return (
        <AuthLayout title="Create Account" subtitle="Join Karchain today">
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                {error && (
                    <div className="bg-red-500/10 border border-red-500/20 text-red-500 text-sm p-3 rounded-lg">
                        {error}
                    </div>
                )}

                <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-muted">Email</label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-primary/50 transition-colors"
                        placeholder="name@example.com"
                    />
                </div>

                <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-muted">Password</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        className="bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-primary/50 transition-colors"
                        placeholder="••••••••"
                        minLength={6}
                    />
                </div>

                <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-muted">Confirm Password</label>
                    <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        className="bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-primary/50 transition-colors"
                        placeholder="••••••••"
                        minLength={6}
                    />
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="mt-4 bg-primary text-background font-bold py-3 rounded-xl hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                    {loading ? <Loader2 className="animate-spin" size={20} /> : 'Sign Up'}
                    {!loading && <ArrowRight size={20} />}
                </button>

                <div className="mt-4 text-center text-sm text-muted">
                    Already have an account?{' '}
                    <Link to="/login" className="text-primary hover:underline font-bold">
                        Sign In
                    </Link>
                </div>
            </form>
        </AuthLayout>
    );
};
