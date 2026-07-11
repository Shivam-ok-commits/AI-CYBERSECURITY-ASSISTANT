import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { Layout } from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import LogAnalysis from "./pages/Logs/LogAnalysis";
import ThreatIntel from "./pages/ThreatIntel/ThreatIntel";
import AIAssistant from "./pages/AI/AIAssistant";
import Cases from "./pages/Cases/Cases";
import Detection from "./pages/Detection/Detection";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import Plugins from "./pages/Plugins";

function App() {
  return (
    <HashRouter>
      <AuthProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/logs" element={<LogAnalysis />} />
            <Route path="/threat-intel" element={<ThreatIntel />} />
            <Route path="/ai" element={<AIAssistant />} />
            <Route path="/cases" element={<Cases />} />
            <Route path="/detection" element={<Detection />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/plugins" element={<Plugins />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/mfa" element={<Settings />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </HashRouter>
  );
}

export default App;
