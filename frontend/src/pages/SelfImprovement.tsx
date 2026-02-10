import React from "react";
import { SelfImprovementDashboard } from "../components/dashboard/SelfImprovementDashboard";

export const SelfImprovement: React.FC = () => {
    return (
        <div className="flex flex-col gap-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">AI Self-Improvement</h1>
                    <p className="text-muted text-sm">Track AI performance and model learning progress</p>
                </div>
            </div>
            
            <div className="bg-card/50 backdrop-blur-sm rounded-xl border border-white/10 p-6">
                <SelfImprovementDashboard />
            </div>
        </div>
    );
};