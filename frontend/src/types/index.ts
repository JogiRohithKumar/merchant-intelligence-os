export interface User {
  id: string;
  email: string;
  role: string;
}

export interface Metric {
  value: number;
  label: string;
  change: number;
}
