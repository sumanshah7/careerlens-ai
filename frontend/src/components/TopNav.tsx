import { Link, useLocation, useNavigate } from 'react-router-dom';
import { cn } from '../lib/utils';
import { useAuth } from '../contexts/AuthContext';
import { useAppStore } from '../store/useAppStore';
import { Button } from './ui/button';
import { Logo } from './Logo';
import { Home, BarChart3, Briefcase, LayoutDashboard, Settings, BookOpen, LogOut, TrendingUp, Moon, Sun, ChevronDown } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

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
  const { darkMode, toggleDarkMode } = useAppStore();
  const [scrolled, setScrolled] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleSignOut = async (e?: React.MouseEvent) => {
    e?.preventDefault();
    e?.stopPropagation();
    try {
      setProfileOpen(false);
      await signOut();
      navigate('/');
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (profileOpen && !target.closest('.profile-dropdown')) {
        setProfileOpen(false);
      }
    };

    if (profileOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [profileOpen]);

  // Don't show nav on landing or login pages
  if (location.pathname === '/' || location.pathname === '/login') {
    return null;
  }

  return (
    <motion.nav 
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className={cn(
        "sticky top-0 z-50 glass-nav transition-shadow duration-300",
        scrolled && "shadow-sm"
      )}
    >
      <div className="max-w-[1100px] mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Logo />
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
                        'relative flex items-center space-x-2 px-3 py-2 text-sm font-medium transition-colors',
                        isActive
                          ? 'text-[#2563eb]'
                          : 'text-[#6b7280] hover:text-[#111827]'
                      )}
                    >
                      {isActive && (
                        <motion.div
                          layoutId="activeTab"
                          className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#2563eb]"
                          initial={false}
                          transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        />
                      )}
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
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleDarkMode}
                className="text-[#6b7280] hover:text-[#111827] hover:bg-transparent"
                aria-label="Toggle dark mode"
              >
                {darkMode ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
              </Button>
              <div className="relative profile-dropdown">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setProfileOpen(!profileOpen);
                  }}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-[#111827] hover:bg-[#f9fafb] transition-colors"
                >
                  <span className="text-[#6b7280]">{currentUser.email}</span>
                  <ChevronDown className="h-4 w-4 text-[#6b7280]" />
                </button>
                {profileOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-md border border-[#e5e7eb] py-1 z-50"
                  >
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleSignOut(e);
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-[#111827] hover:bg-[#f9fafb] flex items-center gap-2 transition-colors"
                    >
                      <LogOut className="h-4 w-4" />
                      Sign Out
                    </button>
                  </motion.div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.nav>
  );
};

