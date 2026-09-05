export function formatINR(amount: number): string {
  if (amount >= 10_000_000) return `₹${(amount/10_000_000).toFixed(1)}Cr`;
  if (amount >= 100_000) return `₹${(amount/100_000).toFixed(1)}L`;
  if (amount >= 1_000) return `₹${amount.toLocaleString('en-IN')}`;
  return `₹${amount.toFixed(0)}`;
}

export function formatPct(value: number, decimals = 1): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
}

export function formatDateTime(iso: string): string {
  if (!iso) return '';
  return new Date(iso).toLocaleString('en-IN', {
    day: '2-digit', 
    month: 'short', 
    hour: '2-digit', 
    minute: '2-digit'
  });
}
