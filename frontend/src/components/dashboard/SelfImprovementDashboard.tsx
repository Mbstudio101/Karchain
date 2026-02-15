import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, TrendingDown, Award, Target, Zap, BarChart3, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../../api';

interface ModelPerformance {
  win_rate: number;
  total_bets: number;
  wins: number;
  losses: number;
  pushes: number;
  profit: number;
  roi: number;
}

interface PerformanceData {
  xgboost: ModelPerformance;
  pythagorean: ModelPerformance;
  heuristic: ModelPerformance;
}

interface GeniusPick {
  id: number;
  game_id: number;
  predicted_pick: string;
  confidence: number;
  model_used: string;
  created_at: string;
}

interface ImprovementRecommendation {
  immediate_actions: Array<{
    action: string;
    reason: string;
    priority: 'high' | 'medium' | 'low';
  }>;
  medium_term: Array<{
    action: string;
    reason: string;
    priority: 'high' | 'medium' | 'low';
  }>;
  long_term: Array<{
    action: string;
    reason: string;
    priority: 'high' | 'medium' | 'low';
  }>;
}

interface DashboardStats {
  performance: {
    '30_days': PerformanceData;
    '7_days': PerformanceData;
  };
  genius_picks: {
    last_30_days: number;
    hit_rate: number;
  };
  improvement_recommendations: ImprovementRecommendation;
  last_analysis: string;
}

export const SelfImprovementDashboard: React.FC = () => {
  const RETRAINABLE_MODELS = new Set(["xgboost"]);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState<string>('xgboost');
  const [geniusPicks, setGeniusPicks] = useState<GeniusPick[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [retrainStatus, setRetrainStatus] = useState<string>("");

  useEffect(() => {
    fetchDashboardStats();
    fetchGeniusPicks();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const { data } = await api.get('/self-improvement/dashboard-stats');
      setDashboardStats(data);
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchGeniusPicks = async () => {
    try {
      const { data } = await api.get('/self-improvement/genius-picks?days_back=30&min_confidence=0.8');
      setGeniusPicks(data.picks || []);
    } catch (error) {
      console.error('Failed to fetch genius picks:', error);
    }
  };

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      await api.post('/self-improvement/run-analysis');
      // Refresh data after analysis
      setTimeout(() => {
        fetchDashboardStats();
        fetchGeniusPicks();
        setIsAnalyzing(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to run analysis:', error);
      setIsAnalyzing(false);
    }
  };

  const retrainModel = async (modelName: string) => {
    if (!RETRAINABLE_MODELS.has(modelName)) {
      setRetrainStatus(`Retraining is currently available only for xgboost.`);
      return;
    }
    try {
      await api.post(`/self-improvement/retrain-model/${modelName}`);
      setRetrainStatus(`Retraining started for ${modelName}.`);
    } catch (error) {
      console.error('Failed to retrain model:', error);
      setRetrainStatus(`Failed to retrain ${modelName}.`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!dashboardStats) {
    return <div className="text-red-400">Failed to load dashboard data</div>;
  }

  const { performance, genius_picks, improvement_recommendations } = dashboardStats;
  const selectedPerformance = performance['30_days'][selectedModel as keyof PerformanceData];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Brain className="h-8 w-8 text-primary" />
          <h2 className="text-2xl font-bold text-white">AI Self-Improvement Dashboard</h2>
        </div>
        <button
          onClick={runAnalysis}
          disabled={isAnalyzing}
          className="flex items-center space-x-2 px-4 py-2 bg-primary text-black font-medium rounded-lg hover:bg-emerald-400 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
          <span>{isAnalyzing ? 'Analyzing...' : 'Run Analysis'}</span>
        </button>
      </div>

      {/* Model Performance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Object.entries(performance['30_days']).map(([model, stats]) => (
          <motion.div
            key={model}
            whileHover={{ scale: 1.02 }}
            className={`p-6 rounded-xl border cursor-pointer transition-all ${
              selectedModel === model 
                ? 'border-primary bg-primary/10' 
                : 'border-white/10 bg-card/50 hover:border-white/20'
            }`}
            onClick={() => setSelectedModel(model)}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold capitalize text-white">{model}</h3>
              <div className={`px-2 py-1 rounded text-xs font-medium ${
                stats.win_rate >= 0.55 ? 'bg-emerald-500/20 text-emerald-400' :
                stats.win_rate >= 0.45 ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                {(stats.win_rate * 100).toFixed(1)}% Win Rate
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-muted">Total Bets</span>
                <span className="font-medium text-white">{stats.total_bets}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Wins/Losses</span>
                <span className="font-medium text-white">{stats.wins}/{stats.losses}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Profit</span>
                <span className={`font-medium ${
                  stats.profit >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}>
                  ${stats.profit.toFixed(0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">ROI</span>
                <span className={`font-medium ${
                  stats.roi >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}>
                  {stats.roi.toFixed(1)}%
                </span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Detailed Model Analysis */}
      <div className="bg-card/50 backdrop-blur-sm rounded-xl border border-white/10 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-white">
            {selectedModel.charAt(0).toUpperCase() + selectedModel.slice(1)} Model Analysis
          </h3>
          <button
            onClick={() => retrainModel(selectedModel)}
            disabled={!RETRAINABLE_MODELS.has(selectedModel)}
            className="px-4 py-2 bg-blue-600/20 text-blue-400 border border-blue-500/30 rounded-lg hover:bg-blue-600/30 text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Retrain Model
          </button>
        </div>
        {retrainStatus && (
          <div className="mb-4 text-sm text-blue-300">{retrainStatus}</div>
        )}
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-white">
              {(selectedPerformance.win_rate * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-muted">Win Rate</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-white">
              {selectedPerformance.total_bets}
            </div>
            <div className="text-sm text-muted">Total Bets</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-white">
              ${selectedPerformance.profit.toFixed(0)}
            </div>
            <div className="text-sm text-muted">Profit</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-white">
              {selectedPerformance.roi.toFixed(1)}%
            </div>
            <div className="text-sm text-muted">ROI</div>
          </div>
        </div>

        {/* 7-day vs 30-day comparison */}
        <div className="mt-6 pt-6 border-t border-white/10">
          <h4 className="text-lg font-medium text-white mb-4">Performance Trend</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-white/5 rounded-lg border border-white/5">
              <div className="text-lg font-semibold text-white">
                {(performance['7_days'][selectedModel as keyof PerformanceData].win_rate * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-muted">7-Day Win Rate</div>
            </div>
            <div className="text-center p-4 bg-white/5 rounded-lg border border-white/5">
              <div className="text-lg font-semibold text-white">
                {(performance['30_days'][selectedModel as keyof PerformanceData].win_rate * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-muted">30-Day Win Rate</div>
            </div>
          </div>
        </div>
      </div>

      {/* Genius Picks */}
      <div className="bg-card/50 backdrop-blur-sm rounded-xl border border-white/10 p-6">
        <div className="flex items-center space-x-3 mb-6">
          <Award className="h-6 w-6 text-yellow-500" />
          <h3 className="text-xl font-semibold text-white">Genius Picks (Last 30 Days)</h3>
          <div className="ml-auto text-sm text-muted">
            {geniusPicks.length} picks • {(genius_picks.hit_rate * 100).toFixed(1)}% hit rate
          </div>
        </div>
        
        <div className="space-y-3">
          <AnimatePresence>
            {geniusPicks.slice(0, 5).map((pick, index) => (
              <motion.div
                key={pick.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/5"
              >
                <div className="flex items-center space-x-3">
                  <Target className="h-5 w-5 text-emerald-500" />
                  <div>
                    <div className="font-medium text-white">{pick.predicted_pick}</div>
                    <div className="text-sm text-muted">Model: {pick.model_used}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium text-emerald-400">
                    {(pick.confidence * 100).toFixed(1)}%
                  </div>
                  <div className="text-sm text-muted">
                    {new Date(pick.created_at).toLocaleDateString()}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Improvement Recommendations */}
      <div className="bg-card/50 backdrop-blur-sm rounded-xl border border-white/10 p-6">
        <div className="flex items-center space-x-3 mb-6">
          <BarChart3 className="h-6 w-6 text-blue-500" />
          <h3 className="text-xl font-semibold text-white">Improvement Recommendations</h3>
        </div>
        
        <div className="space-y-6">
          {/* Immediate Actions */}
          {improvement_recommendations.immediate_actions.length > 0 && (
            <div>
              <h4 className="text-lg font-medium text-white mb-3 flex items-center space-x-2">
                <Zap className="h-5 w-5 text-red-500" />
                <span>Immediate Actions</span>
              </h4>
              <div className="space-y-2">
                {improvement_recommendations.immediate_actions.map((action, index) => (
                  <div key={index} className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <div className="font-medium text-red-400">{action.action}</div>
                    <div className="text-sm text-red-400/80 mt-1">{action.reason}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Medium Term */}
          {improvement_recommendations.medium_term.length > 0 && (
            <div>
              <h4 className="text-lg font-medium text-white mb-3 flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-yellow-500" />
                <span>Medium Term</span>
              </h4>
              <div className="space-y-2">
                {improvement_recommendations.medium_term.map((action, index) => (
                  <div key={index} className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <div className="font-medium text-yellow-400">{action.action}</div>
                    <div className="text-sm text-yellow-400/80 mt-1">{action.reason}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Long Term */}
          {improvement_recommendations.long_term.length > 0 && (
            <div>
              <h4 className="text-lg font-medium text-white mb-3 flex items-center space-x-2">
                <TrendingDown className="h-5 w-5 text-blue-500" />
                <span>Long Term</span>
              </h4>
              <div className="space-y-2">
                {improvement_recommendations.long_term.map((action, index) => (
                  <div key={index} className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <div className="font-medium text-blue-400">{action.action}</div>
                    <div className="text-sm text-blue-400/80 mt-1">{action.reason}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
