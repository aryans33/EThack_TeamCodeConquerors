import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { StockProvider } from './context/StockContext';

import Layout from './components/layout/Layout';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import Dashboard from './pages/Dashboard/Dashboard';
import StockDetail from './pages/Stock/StockDetail';
import Watchlist from './pages/Watchlist/Watchlist';
import Documents from './pages/Documents/Documents';
import Ask from './pages/Ask/Ask';

// Protected route wrapper
function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="loading-container"><div className="spinner spinner-lg" /></div>;
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

// Public route (redirects to dashboard if logged in)
function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="loading-container"><div className="spinner spinner-lg" /></div>;
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : children;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

      {/* Protected routes — wrapped in app Layout */}
      <Route path="/dashboard" element={<PrivateRoute><Layout><Dashboard /></Layout></PrivateRoute>} />
      <Route path="/stock/:symbol" element={<PrivateRoute><Layout><StockDetail /></Layout></PrivateRoute>} />
      <Route path="/watchlist" element={<PrivateRoute><Layout><Watchlist /></Layout></PrivateRoute>} />
      <Route path="/documents" element={<PrivateRoute><Layout><Documents /></Layout></PrivateRoute>} />
      <Route path="/ask" element={<PrivateRoute><Layout><Ask /></Layout></PrivateRoute>} />
      <Route path="/stocks" element={<PrivateRoute><Layout><Dashboard /></Layout></PrivateRoute>} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <StockProvider>
          <AppRoutes />
        </StockProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
