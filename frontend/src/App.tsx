import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Login from './pages/Login';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import AICommandCenter from './pages/AICommandCenter';
import Growth from './pages/Growth';
import Risk from './pages/Risk';
import Recovery from './pages/Recovery';
import Finance from './pages/Finance';
import Transactions from './pages/Transactions';
import Actions from './pages/Actions';
import Audit from './pages/Audit';
import Evaluation from './pages/Evaluation';
import Settings from './pages/Settings';

const AuthGuard = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" />;
  return <>{children}</>;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/onboarding" element={<AuthGuard><Onboarding /></AuthGuard>} />
        <Route path="/" element={<AuthGuard><Layout><Dashboard /></Layout></AuthGuard>} />
        <Route path="/command" element={<AuthGuard><Layout><AICommandCenter /></Layout></AuthGuard>} />
        <Route path="/growth" element={<AuthGuard><Layout><Growth /></Layout></AuthGuard>} />
        <Route path="/risk" element={<AuthGuard><Layout><Risk /></Layout></AuthGuard>} />
        <Route path="/recovery" element={<AuthGuard><Layout><Recovery /></Layout></AuthGuard>} />
        <Route path="/finance" element={<AuthGuard><Layout><Finance /></Layout></AuthGuard>} />
        <Route path="/transactions" element={<AuthGuard><Layout><Transactions /></Layout></AuthGuard>} />
        <Route path="/actions" element={<AuthGuard><Layout><Actions /></Layout></AuthGuard>} />
        <Route path="/audit" element={<AuthGuard><Layout><Audit /></Layout></AuthGuard>} />
        <Route path="/evaluation" element={<AuthGuard><Layout><Evaluation /></Layout></AuthGuard>} />
        <Route path="/settings" element={<AuthGuard><Layout><Settings /></Layout></AuthGuard>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
