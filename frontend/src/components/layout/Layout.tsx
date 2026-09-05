import React, { useState } from 'react';
import Sidebar from './Sidebar';

const Layout = ({ children }: { children: React.ReactNode }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen bg-slate-50 text-slate-800 overflow-hidden font-sans">
      <Sidebar 
        collapsed={collapsed} 
        onToggleCollapse={() => setCollapsed(!collapsed)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto bg-gradient-to-br from-slate-50 via-white to-sky-50/30">
        {React.isValidElement(children) 
          ? React.cloneElement(children as React.ReactElement<any>, { 
              onOpenMobileNav: () => setMobileOpen(true) 
            }) 
          : children}
      </div>
    </div>
  );
};

export default Layout;
