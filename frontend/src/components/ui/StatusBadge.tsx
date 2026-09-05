import React from 'react';

interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error' | 'critical' | 'info' | string;
  label: string;
}

const StatusBadge = ({ status, label }: StatusBadgeProps) => {
  const s = (status || '').toLowerCase();
  let colorStyle = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
  
  if (s === 'success' || s === 'approved') {
    colorStyle = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  } else if (s === 'warning' || s === 'pending_approval' || s === 'pending' || s === 'disputed') {
    colorStyle = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  } else if (s === 'error' || s === 'critical' || s === 'failed' || s === 'rejected') {
    colorStyle = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider border ${colorStyle}`}>
      {label}
    </span>
  );
};

export default StatusBadge;
