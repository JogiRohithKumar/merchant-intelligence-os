import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../../store/auth';
import { Search, Menu, LogOut, User, Shield } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import CommandPaletteModal from '../ui/CommandPaletteModal';
import SystemStatusIndicator, { SystemOperatingState } from '../ui/ConfirmModal';
import api from '../../services/api';

interface TopNavProps {
  pageTitle: string;
  systemState?: SystemOperatingState;
  onOpenMobileNav?: () => void;
}

export default function TopNav({ pageTitle, systemState = 'STANDBY', onOpenMobileNav }: TopNavProps) {
  const user = useAuthStore(state => state.user);
  const setUser = useAuthStore(state => state.setUser);
  const logout = useAuthStore(state => state.logout);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const navigate = useNavigate();

  // Load verified user identity from backend /api/v1/auth/me if token exists
  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token');
      if (token && !user) {
        try {
          const res = await api.get('/v1/auth/me');
          if (res.data) {
            setUser(res.data);
          }
        } catch {
          // Token invalid: logout handles redirect
          logout();
          navigate('/login');
        }
      }
    };
    fetchUser();
  }, [user, setUser, logout, navigate]);

  // Keyboard shortcut Ctrl+K / Cmd+K listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setPaletteOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <>
      <header className="h-16 bg-white/90 border-b border-slate-200/80 px-4 sm:px-6 flex items-center justify-between z-20 backdrop-blur-md sticky top-0">
        {/* Left: Mobile Hamburger & Page Title */}
        <div className="flex items-center gap-3">
          {onOpenMobileNav && (
            <button
              onClick={onOpenMobileNav}
              className="md:hidden p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
              title="Open Navigation"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}
          <div>
            <h1 className="text-sm font-bold tracking-tight text-slate-900 font-sans">
              {pageTitle}
            </h1>
            <div className="hidden sm:block text-[11px] text-slate-400 font-medium">
              Merchant Financial Operations Console
            </div>
          </div>
        </div>

        {/* Center: Command Palette Trigger */}
        <button
          onClick={() => setPaletteOpen(true)}
          className="hidden md:flex items-center gap-3 px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-xs text-slate-500 hover:text-slate-800 hover:border-slate-300 transition-all w-64 justify-between cursor-pointer shadow-2xs"
        >
          <div className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-sans text-[11px]">Command Palette / Search...</span>
          </div>
          <kbd className="px-1.5 py-0.5 rounded bg-white border border-slate-200 text-[10px] font-mono text-slate-500 shadow-2xs">
            ⌘K
          </kbd>
        </button>

        {/* Right: Live System Status & User Profile Menu */}
        <div className="flex items-center gap-3">
          <SystemStatusIndicator systemState={systemState} />

          {/* User Profile Capsule */}
          <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-slate-200">
            <div className="w-7 h-7 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 font-bold text-xs">
              {user?.full_name ? user.full_name[0].toUpperCase() : <User className="w-3.5 h-3.5" />}
            </div>
            <div className="flex flex-col text-left">
              <span className="text-xs font-semibold text-slate-800 leading-tight max-w-[120px] truncate">
                {user?.full_name || 'Authenticated User'}
              </span>
              <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
                <Shield className="w-2.5 h-2.5 text-indigo-500" />
                {user?.role || 'operator'}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors ml-1 cursor-pointer"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Global Command Palette Modal */}
      <CommandPaletteModal isOpen={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </>
  );
}
