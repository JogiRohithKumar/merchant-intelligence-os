import React, { useState } from 'react';
import { X, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { formatINR } from '../../utils/format';

interface ApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children?: React.ReactNode;
  onConfirm?: () => void | Promise<void>;
  onApprove?: () => void;
  onReject?: (reason: string) => void;
  action?: any;
}

export default function ApprovalModal({
  isOpen,
  onClose,
  title = 'AUTHORIZE POLICY ACTION',
  children,
  onConfirm,
  onApprove,
  onReject,
  action,
}: ApprovalModalProps) {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    setLoading(true);
    try {
      if (onConfirm) await onConfirm();
      else if (onApprove) onApprove();
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const handleReject = () => {
    if (onReject) {
      onReject(reason || 'Operator rejected');
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm font-mono">
      <div className="relative bg-white border border-slate-200 rounded-2xl shadow-2xl w-full max-w-xl p-6 text-slate-800 animate-fade-in">
        {/* Modal Header */}
        <div className="flex justify-between items-center pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-amber-50 text-amber-600 border border-amber-200">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold tracking-wider text-slate-900 uppercase">{title}</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="py-4 space-y-4 text-xs">
          {children ? (
            children
          ) : action ? (
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-slate-500">Action Type:</span>
                <span className="font-bold text-slate-900">{action.type || action.action_type}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-slate-500">Amount at Risk:</span>
                <span className="font-bold text-amber-700 text-sm">{formatINR(action.amount_at_risk || 0)}</span>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                <span className="text-[10px] text-slate-500 uppercase font-semibold">Expected Outcome:</span>
                <p className="text-slate-700 font-sans text-xs">{action.expected_outcome || action.description}</p>
              </div>

              {onReject && (
                <div className="mt-2">
                  <label className="block text-[10px] uppercase font-semibold text-slate-500 mb-1">
                    Rejection Reason (Optional)
                  </label>
                  <textarea
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg text-xs p-2.5 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                    rows={2}
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Provide operator context for audit log..."
                  />
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
          {onReject && (
            <button
              onClick={handleReject}
              className="px-4 py-2 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-xl transition-colors"
            >
              Reject Action
            </button>
          )}
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading}
            className="px-5 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-all flex items-center gap-1.5 shadow-sm shadow-indigo-200 disabled:opacity-50 cursor-pointer"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>{loading ? 'Authorizing...' : 'Authorize Execution'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
