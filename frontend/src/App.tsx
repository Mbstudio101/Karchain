
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppLayout } from "./components/layout/AppLayout";
import { Dashboard } from "./pages/Dashboard";
import { Players } from "./pages/Players";
import { Teams } from "./pages/Teams";
import { PropsFinder } from "./pages/PropsFinder";
import { Analysis } from "./pages/Analysis";
import { History } from "./pages/History";
import { GameDetails } from "./pages/GameDetails";
import { Settings } from "./pages/Settings";
import { MixedParlay } from "./pages/MixedParlay";
import { GeniusPicksPage } from "./pages/GeniusPicks";
import { SelfImprovement } from "./pages/SelfImprovement";
import { Login } from "./pages/auth/Login";
import { SignUp } from "./pages/auth/SignUp";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { WebSocketProvider } from "./context/WebSocketContext";
import { DesktopTitlebar } from "./components/layout/DesktopTitlebar";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});
const isDesktop =
  typeof window !== "undefined" &&
  (((window as any).__TAURI_INTERNALS__ !== undefined) || navigator.userAgent.includes("Tauri"));

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="h-screen w-full overflow-hidden">
        <DesktopTitlebar />
        <div className={isDesktop ? "h-[calc(100vh-2.5rem)]" : "h-full"}>
          <Router>
            <AuthProvider>
              <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<SignUp />} />

                {/* Protected Routes */}
                <Route
                  element={
                    <WebSocketProvider>
                      <ProtectedRoute />
                    </WebSocketProvider>
                  }
                >
                  <Route path="/" element={<AppLayout />}>
                    <Route index element={<Dashboard />} />
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="players" element={<Players />} />
                    <Route path="teams" element={<Teams />} />
                    <Route path="props-finder" element={<PropsFinder />} />
                    <Route path="analysis" element={<Analysis />} />
                    <Route path="self-improvement" element={<SelfImprovement />} />
                    <Route path="history" element={<History />} />
                    <Route path="games/:id" element={<GameDetails />} />
                    <Route path="settings" element={<Settings />} />
                    <Route path="mixed-parlay" element={<MixedParlay />} />
                    <Route path="genius-picks" element={<GeniusPicksPage />} />
                  </Route>
                </Route>

                {/* Catch-all for unmatched routes */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </AuthProvider>
          </Router>
        </div>
      </div>
    </QueryClientProvider>
  );
}

export default App;
