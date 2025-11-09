import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from './contexts/AuthContext';
import { TopNav } from './components/TopNav';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Home } from './pages/Home';
import { Analysis } from './pages/Analysis';
import { Jobs } from './pages/Jobs';
import { Dashboard } from './pages/Dashboard';
import { Settings } from './pages/Settings';
import { CoachingPlan } from './pages/CoachingPlan';
import { Progress } from './pages/Progress';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <div className="min-h-screen h-full bg-[#f9fafb] transition-colors">
          <TopNav />
          <main className="min-h-[calc(100vh-4rem)] page-fade">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route
                path="/home"
                element={
                  <ProtectedRoute>
                    <Home />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/analysis"
                element={
                  <ProtectedRoute>
                    <Analysis />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/jobs"
                element={
                  <ProtectedRoute>
                    <Jobs />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/settings"
                element={
                  <ProtectedRoute>
                    <Settings />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/coaching-plan"
                element={
                  <ProtectedRoute>
                    <CoachingPlan />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/progress"
                element={
                  <ProtectedRoute>
                    <Progress />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </main>
          <Toaster />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App

