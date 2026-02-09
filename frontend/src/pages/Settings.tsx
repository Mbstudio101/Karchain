import React from "react";
import { Settings as SettingsIcon, Save } from "lucide-react";

export const Settings: React.FC = () => {
    return (
        <div className="max-w-2xl space-y-8">
            <div className="flex items-center gap-3 mb-8">
                <div className="p-2 bg-primary/10 rounded-lg text-primary">
                    <SettingsIcon size={24} />
                </div>
                <h1 className="text-2xl font-bold text-white">Preferences</h1>
            </div>

            <div className="space-y-6">
                {/* Section */}
                <div className="bg-card border border-white/5 rounded-2xl p-6 space-y-4">
                    <h3 className="text-lg font-bold text-white mb-4">Display Settings</h3>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm text-muted">Odds Format</label>
                        <select className="bg-white/5 border border-white/10 rounded-lg p-2 text-white outline-none focus:border-primary">
                            <option>American (e.g. -110)</option>
                            <option>Decimal (e.g. 1.91)</option>
                        </select>
                    </div>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm text-muted">Theme</label>
                        <select className="bg-white/5 border border-white/10 rounded-lg p-2 text-white outline-none focus:border-primary">
                            <option>Dark (Default)</option>
                            <option>Midnight</option>
                        </select>
                    </div>
                </div>

                {/* Section */}
                <div className="bg-card border border-white/5 rounded-2xl p-6 space-y-4">
                    <h3 className="text-lg font-bold text-white mb-4">Scraper Settings</h3>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm text-muted">Auto-Refresh Interval</label>
                        <select className="bg-white/5 border border-white/10 rounded-lg p-2 text-white outline-none focus:border-primary">
                            <option>Every 5 minutes</option>
                            <option>Every 15 minutes</option>
                            <option>Every hour</option>
                            <option>Manual Only</option>
                        </select>
                    </div>
                </div>

                <button className="flex items-center gap-2 bg-primary text-black font-bold px-6 py-3 rounded-xl hover:bg-emerald-400 transition-colors">
                    <Save size={18} />
                    Save Changes
                </button>
            </div>
        </div>
    );
};
