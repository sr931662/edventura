import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import Home from './pages/public/Home';
import Login from './pages/auth/Login';
import RegisterInstitute from './pages/enrollment/RegisterInstitute';
import InstituteStatus from './pages/enrollment/InstituteStatus';
import VerifyInstitute from './pages/enrollment/VerifyInstitute';
import Dashboard from './pages/dashboard/Dashboard';
import ProtectedRoute from './components/auth/ProtectedRoute';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/enroll" element={<RegisterInstitute />} />
            <Route path="/institute/status" element={<ProtectedRoute><InstituteStatus /></ProtectedRoute>} />
            <Route path="/institute/verify/:type" element={<ProtectedRoute><VerifyInstitute /></ProtectedRoute>} />
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}