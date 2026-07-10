import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import LogAnalysis from "./pages/Logs/LogAnalysis";
import ThreatIntel from "./pages/ThreatIntel/ThreatIntel";
import AIAssistant from "./pages/AI/AIAssistant";
import Cases from "./pages/Cases/Cases";
import Detection from "./pages/Detection/Detection";
import Reports from "./pages/Reports";
import MfaSettings from "./pages/MfaSettings";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/logs" element={<LogAnalysis />} />
            <Route path="/threat-intel" element={<ThreatIntel />} />
            <Route path="/ai" element={<AIAssistant />} />
            <Route path="/cases" element={<Cases />} />
            <Route path="/detection" element={<Detection />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/mfa" element={<MfaSettings />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
