import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Brain, Shield, RefreshCw, Layers, TrendingUp, FileSearch, X } from 'lucide-react';

interface CommandPaletteModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CommandPaletteModal({ isOpen, onClose }: CommandPaletteModalProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  if (!isOpen) return null;

  const actions = [
    { label: 'Run Flagship Investigation', path: '/command', icon: Brain, desc: 'Analyze 20% revenue drop & recover' },
    { label: 'View ML Risk Model & Metrics', path: '/risk', icon: Shield, desc: 'Held-out test set, ROC-AUC 0.99' },
    { label: 'Explore Recovery Funnel', path: '/recovery', icon: RefreshCw, desc: 'P(recovery) candidates & retries' },
    { label: 'Inspect Reconciliation & Settlements', path: '/finance', icon: Layers, desc: '4-level matching & exceptions' },
    { label: 'Simulate Growth Campaigns', path: '/growth', icon: TrendingUp, desc: 'A/B simulation & lift curves' },
    { label: 'Examine Forensic Audit Log', path: '/audit', icon: FileSearch, desc: 'Immutable agent action history' },
  ];

  const filtered = actions.filter(a => 
    a.label.toLowerCase().includes(searchTerm.toLowerCase()) || 
    a.desc.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelect = (path: string) => {
    navigate(path);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-start justify-center pt-24">
      <div className="w-full max-w-xl bg-command-surface border border-command-border rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Search Header */}
        <div className="flex items-center px-4 py-3 border-b border-command-border gap-3">
          <Search className="w-4 h-4 text-terminal-cyan" />
          <input 
            type="text"
            autoFocus
            placeholder="Type a command or search mission control..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full bg-transparent text-sm text-gray-200 placeholder-gray-500 font-sans focus:outline-none"
          />
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-200 rounded cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results list */}
        <div className="p-2 max-h-80 overflow-y-auto space-y-1">
          {filtered.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div 
                key={idx}
                onClick={() => handleSelect(item.path)}
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-command-subtle/70 cursor-pointer text-xs font-mono text-gray-300 transition-colors"
              >
                <div className="p-2 rounded-lg bg-command-bg border border-command-border text-terminal-cyan">
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1">
                  <div className="font-bold text-gray-200">{item.label}</div>
                  <div className="text-[11px] text-gray-400 font-sans">{item.desc}</div>
                </div>
                <span className="text-[10px] text-gray-500 font-mono">EXECUTE</span>
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div className="p-6 text-center text-xs font-mono text-gray-500">
              No matching actions found.
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="px-4 py-2 bg-command-bg border-t border-command-border flex items-center justify-between text-[10px] font-mono text-gray-500">
          <span>NAVIGATION SHORTCUTS</span>
          <span>ESC TO CLOSE</span>
        </div>
      </div>
    </div>
  );
}
