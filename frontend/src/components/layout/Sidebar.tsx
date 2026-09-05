import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Terminal, 
  Brain, 
  TrendingUp, 
  Shield, 
  RefreshCw, 
  Layers, 
  ListOrdered, 
  CheckSquare, 
  FileSearch, 
  Cpu, 
  Sliders, 
  LogOut,
  ChevronLeft,
  ChevronRight,
  Menu,
  X
} from 'lucide-react';
import { useAuthStore } from '../../store/auth';

interface SidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export default function Sidebar({
  collapsed = false,
  onToggleCollapse,
  mobileOpen = false,
  onCloseMobile
}: SidebarProps) {
  const logout = useAuthStore(state => state.logout);
  const user = useAuthStore(state => state.user);

  const navSections = [
    {
      title: "INTELLIGENCE",
      items: [
        { to: '/', label: 'Overview', icon: Terminal, badge: null },
        { to: '/command', label: 'AI Assistant', icon: Brain, badge: 'CORE' },
      ]
    },
    {
      title: "SPECIALISTS",
      items: [
        { to: '/growth', label: 'Growth', icon: TrendingUp, badge: null },
        { to: '/risk', label: 'Risk & ML', icon: Shield, badge: 'AUC 0.99' },
        { to: '/recovery', label: 'Recovery', icon: RefreshCw, badge: null },
        { to: '/finance', label: 'Finance & Recon', icon: Layers, badge: null },
      ]
    },
    {
      title: "OPERATIONS",
      items: [
        { to: '/transactions', label: 'Transactions', icon: ListOrdered, badge: null },
        { to: '/actions', label: 'Action Center', icon: CheckSquare, badge: 'SAFE' },
        { to: '/audit', label: 'Forensic Audit', icon: FileSearch, badge: 'VERIFIED' },
      ]
    },
    {
      title: "SYSTEM",
      items: [
        { to: '/evaluation', label: 'Model Benchmarks', icon: Cpu, badge: null },
        { to: '/settings', label: 'Settings', icon: Sliders, badge: null },
      ]
    }
  ];

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white border-r border-slate-200/90 text-slate-700 select-none shadow-sm">
      {/* Brand Header */}
      <div className={`p-4 border-b border-slate-200/80 flex items-center ${collapsed ? 'justify-center' : 'justify-between'}`}>
        {!collapsed ? (
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-sky-500/20">
              <Brain className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold tracking-tight text-slate-900 font-sans">
                <span>MERCHANT INTELLIGENCE OS</span>
              </div>
              <div className="text-[10px] text-slate-400 font-medium">
                Financial Operating System
              </div>
            </div>
          </div>
        ) : (
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
            <Brain className="w-4 h-4" />
          </div>
        )}

        {/* Desktop Collapse Toggle */}
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className="hidden md:flex p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        )}

        {/* Mobile Close Button */}
        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="md:hidden p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-2.5 py-3 space-y-5">
        {navSections.map((section, idx) => (
          <div key={idx} className="space-y-1">
            {!collapsed && (
              <div className="px-2.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                {section.title}
              </div>
            )}
            {section.items.map(item => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  onClick={onCloseMobile}
                  title={collapsed ? item.label : undefined}
                  className={({ isActive }) =>
                    `flex items-center ${collapsed ? 'justify-center px-2 py-2.5' : 'justify-between px-2.5 py-2'} rounded-xl text-xs font-medium transition-all duration-150 ${
                      isActive
                        ? 'bg-gradient-to-r from-sky-50 to-indigo-50/80 text-sky-700 font-semibold shadow-xs border border-sky-200/60'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                    }`
                  }
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 shrink-0 transition-colors ${collapsed ? '' : 'text-slate-500'}`} />
                    {!collapsed && <span>{item.label}</span>}
                  </div>
                  {!collapsed && item.badge && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 font-medium">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </div>
        ))}
      </div>

      {/* User Info & Sign Out */}
      <div className="p-3 border-t border-slate-200/80 bg-slate-50/70">
        <div className={`p-2 rounded-xl border border-slate-200/90 bg-white flex items-center ${collapsed ? 'justify-center' : 'justify-between'} shadow-xs`}>
          {!collapsed && (
            <div className="truncate pr-2">
              <div className="text-slate-800 text-xs font-semibold truncate font-sans">
                {user?.merchant_name || user?.full_name || 'Merchant Workspace'}
              </div>
              <div className="text-[10px] text-slate-400 truncate">
                {user?.email || 'Active Operator'}
              </div>
            </div>
          )}
          <button 
            onClick={logout} 
            title="Sign Out"
            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className={`hidden md:flex flex-col h-screen shrink-0 transition-all duration-200 z-30 ${collapsed ? 'w-16' : 'w-64'}`}>
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Backdrop */}
      {mobileOpen && (
        <div 
          onClick={onCloseMobile}
          className="fixed inset-0 bg-slate-900/30 backdrop-blur-xs z-40 md:hidden transition-opacity"
        />
      )}

      {/* Mobile Slide-Out Drawer */}
      <div className={`fixed inset-y-0 left-0 w-72 z-50 transform transition-transform duration-200 ease-in-out md:hidden ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        {sidebarContent}
      </div>
    </>
  );
}
