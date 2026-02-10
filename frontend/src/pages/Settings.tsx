import React, { useState, useEffect } from "react";
import { Settings as SettingsIcon, Save, Check } from "lucide-react";

const DEFAULTS = {
    oddsFormat: "american",
    theme: "dark",
    refreshInterval: "5",
};

export const Settings: React.FC = () => {
    const [oddsFormat, setOddsFormat] = useState(DEFAULTS.oddsFormat);
    const [theme, setTheme] = useState(DEFAULTS.theme);
    const [refreshInterval, setRefreshInterval] = useState(DEFAULTS.refreshInterval);
    const [saved, setSaved] = useState(false);

    // Load saved preferences on mount
    useEffect(() => {
        const stored = localStorage.getItem("karchain_settings");
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                if (parsed.oddsFormat) setOddsFormat(parsed.oddsFormat);
                if (parsed.theme) setTheme(parsed.theme);
                if (parsed.refreshInterval) setRefreshInterval(parsed.refreshInterval);
            } catch (e) {
                console.error("Failed to parse settings", e);
            }
        }
    }, []);

    const handleSave = () => {
        const settings = { oddsFormat, theme, refreshInterval };
        localStorage.setItem("karchain_settings", JSON.stringify(settings));
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <div className="max-w-2xl space-y-8">
            <div className="flex items-center gap-3 mb-8">
                <div className="p-2 bg-primary/10 rounded-lg text-primary">
                    <SettingsIcon size={24} />
                </div>
                <h1 className="text-2xl font-bold text-white">Preferences</h1>
            </div>

            <div className="space-y-6">
                {/* Display Settings */}
                <div className="bg-card border border-white/5 rounded-2xl p-6 space-y-4">
                    <h3 className="text-lg font-bold text-white mb-4">Display Settings</h3>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm text-muted">Odds Format</label>
                        <select
                            value={oddsFormat}
                            onChange={(e) => setOddsFormat(e.target.value)}
                            className="bg-white/5 border border-white/10 rounded-lg p-2 text-white outline-none focus:border-primary"
                        >
                            <option value="american" className="bg-card">American (e.g. -110)</option>
                            <option value="decimal" className="bg-card">Decimal (e.g. 1.91)</option>
                        </select>
                    </div>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm text-muted">Theme</label>
                        <select
                            value={theme}
                            onChange={(e) => setTheme(e.target.value)}
                            className="bg-white/5 border border-white/10 rounded-lg p-2 text-white outline-none focus:border-primary"
                        >
                            <option value="dark" className="bg-card">Dark (Default)</option>
                            <option value="midnight" className="bg-card">Midnight</option>
                        </select>
                    </div>
                </div>

                {/* Scraper Settings */}
                <div className="bg-card border border-white/5 rounded-2xl p-6 space-y-4">
                    <h3 className="text-lg font-bold text-white mb-4">Scraper Settings</h3>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm text-muted">Auto-Refresh Interval</label>
                        <select
                            value={refreshInterval}
                            onChange={(e) => setRefreshInterval(e.target.value)}
                            className="bg-white/5 border border-white/10 rounded-lg p-2 text-white outline-none focus:border-primary"
                        >
                            <option value="5" className="bg-card">Every 5 minutes</option>
                            <option value="15" className="bg-card">Every 15 minutes</option>
                            <option value="60" className="bg-card">Every hour</option>
                            <option value="manual" className="bg-card">Manual Only</option>
                        </select>
                    </div>
                </div>

                <button
                    onClick={handleSave}
                    className="flex items-center gap-2 bg-primary text-black font-bold px-6 py-3 rounded-xl hover:bg-emerald-400 transition-colors"
                >
                    {saved ? <Check size={18} /> : <Save size={18} />}
                    {saved ? "Saved!" : "Save Changes"}
                </button>
            </div>
        </div>
    );
};
