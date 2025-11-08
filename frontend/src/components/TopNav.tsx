import { Link, useLocation, useNavigate } from 'react-router-dom';
import { cn } from '../lib/utils';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Home, BarChart3, Briefcase, LayoutDashboard, Settings, BookOpen, LogOut, TrendingUp } from 'lucide-react';

const navItems = [
  { path: '/home', label: 'Home', icon: Home },
  { path: '/analysis', label: 'Analysis', icon: BarChart3 },
  { path: '/jobs', label: 'Jobs', icon: Briefcase },
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/progress', label: 'Progress', icon: TrendingUp },
  { path: '/coaching-plan', label: 'Coaching Plan', icon: BookOpen },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const TopNav = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentUser, signOut } = useAuth();

  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/');
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  // Don't show nav on landing or login pages
  if (location.pathname === '/' || location.pathname === '/login') {
    return null;
  }

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link to="/home" className="text-xl font-bold">
              CareerLens AI
            </Link>
            {currentUser && (
              <div className="flex space-x-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={cn(
                        'flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
          {currentUser && (
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">{currentUser.email}</span>
              <Button variant="outline" size="sm" onClick={handleSignOut}>
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </Button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

