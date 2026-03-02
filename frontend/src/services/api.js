import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

// Auto-logout on 401
api.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err.response?.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
        return Promise.reject(err);
    }
);

// ── Auth ──
export const authAPI = {
    register: (data) => api.post('/auth/register', data),
    login: (data) => api.post('/auth/login', data),
    logout: () => api.post('/auth/logout'),
    me: () => api.get('/auth/me'),
};

// ── Stocks ──
export const stockAPI = {
    getInfo: (symbol) => api.get(`/stocks/${symbol}`),
    getHistory: (symbol, period = '1y', interval = '1d') =>
        api.get(`/stocks/${symbol}/history`, { params: { period, interval } }),
    getFinancials: (symbol) => api.get(`/stocks/${symbol}/financials`),
    compare: (symbols) => api.get('/stocks/compare', { params: { symbols: symbols.join(',') } }),
    getNseTop: (limit = 20) => api.get('/stocks/nse/top', { params: { limit } }),
    getThesis: (symbol) => api.get(`/stocks/${symbol}/thesis`),
    getRisk: (symbol) => api.get(`/stocks/${symbol}/risk`),
    getSummary: (symbol) => api.get(`/stocks/${symbol}/summary`),
    ask: (question, symbol, context) => api.post('/stocks/ask', { question, symbol, additional_context: context }),
};

// ── Watchlist ──
export const watchlistAPI = {
    get: () => api.get('/watchlist'),
    add: (symbol) => api.post('/watchlist', { symbol }),
    remove: (symbol) => api.delete(`/watchlist/${symbol}`),
};

// ── Documents ──
export const docAPI = {
    upload: (formData) => api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        baseURL: 'http://localhost:8000/api/v1',
    }),
    list: () => api.get('/documents', { baseURL: 'http://localhost:8000/api/v1' }),
    status: (docId) => api.get(`/documents/${docId}/status`, { baseURL: 'http://localhost:8000/api/v1' }),
};

export default api;
