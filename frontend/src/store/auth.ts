import { create } from 'zustand';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  name?: string;
  role: string;
  merchant_id: string | null;
  merchant_name?: string | null;
  account_status?: string;
  onboarding_required?: boolean;
  last_login?: string | null;
}

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  setToken: (token: string | null) => void;
  setUser: (user: UserProfile | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  // Secure: Only load real token from localStorage, NEVER default to a mock token
  token: localStorage.getItem('token'),
  user: null,
  setToken: (token) => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
    set({ token });
  },
  setUser: (user) => set({ user }),
  logout: () => {
    localStorage.removeItem('token');
    set({ token: null, user: null });
  }
}));
