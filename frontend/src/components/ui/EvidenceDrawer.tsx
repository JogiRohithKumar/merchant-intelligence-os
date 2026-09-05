import React from 'react';
import { X } from 'lucide-react';

interface EvidenceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export default function EvidenceDrawer({ isOpen, onClose, title, children }: EvidenceDrawerProps) {
  if (!isOpen) return null;
  return (
    <>
      <div className="fixed inset-0 bg-black/20 z-40 transition-opacity" onClick={onClose} />
      <div className={`fixed top-0 right-0 h-full w-[500px] bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : 'translate-x-full'} flex flex-col`}>
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          {children}
        </div>
      </div>
    </>
  );
}
