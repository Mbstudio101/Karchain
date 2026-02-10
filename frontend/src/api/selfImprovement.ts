import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/self-improvement';

export const selfImprovementAPI = {
  // Performance tracking
  getModelPerformance: async (modelName?: string, daysBack: number = 30) => {
    const params = new URLSearchParams();
    if (modelName) params.append('model_name', modelName);
    params.append('days_back', daysBack.toString());
    
    const response = await axios.get(`${API_BASE_URL}/performance?${params}`);
    return response.data;
  },

  // Analysis and improvement
  runAnalysis: async () => {
    const response = await axios.post(`${API_BASE_URL}/run-analysis`);
    return response.data;
  },

  retrainModel: async (modelName: string) => {
    const response = await axios.post(`${API_BASE_URL}/retrain-model/${modelName}`);
    return response.data;
  },

  getImprovementRecommendations: async () => {
    const response = await axios.get(`${API_BASE_URL}/recommendations`);
    return response.data;
  },

  // Genius picks and parlays
  getGeniusPicks: async (daysBack: number = 30, minConfidence: number = 0.8) => {
    const params = new URLSearchParams();
    params.append('days_back', daysBack.toString());
    params.append('min_confidence', minConfidence.toString());
    
    const response = await axios.get(`${API_BASE_URL}/genius-picks?${params}`);
    return response.data;
  },

  getAIParlays: async (daysBack: number = 30, minConfidence: number = 0.7) => {
    const params = new URLSearchParams();
    params.append('days_back', daysBack.toString());
    params.append('min_confidence', minConfidence.toString());
    
    const response = await axios.get(`${API_BASE_URL}/ai-parlays?${params}`);
    return response.data;
  },

  // Dashboard stats
  getDashboardStats: async () => {
    const response = await axios.get(`${API_BASE_URL}/dashboard-stats`);
    return response.data;
  }
};