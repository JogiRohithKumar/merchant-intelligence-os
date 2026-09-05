import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { formatINR } from '../../utils/format';

interface FunnelData {
  detected: { count: number, amount: number };
  eligible: { count: number, amount: number };
  approved: { count: number, amount: number };
  attempted: { count: number, amount: number };
  recovered: { count: number, amount: number };
}

export default function RecoveryFunnel({ data }: { data: FunnelData }) {
  const chartData = [
    { name: 'Detected', count: data.detected.count, amount: data.detected.amount, color: '#94A3B8' },
    { name: 'Risk Filtered', count: data.eligible.count, amount: data.eligible.amount, color: '#F59E0B' },
    { name: 'Policy Approved', count: data.approved.count, amount: data.approved.amount, color: '#0284C7' },
    { name: 'Attempted', count: data.attempted.count, amount: data.attempted.amount, color: '#6366F1' },
    { name: 'Recovered', count: data.recovered.count, amount: data.recovered.amount, color: '#10B981' }
  ];

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart layout="vertical" data={chartData} margin={{ top: 20, right: 30, left: 40, bottom: 5 }}>
          <XAxis type="number" hide />
          <YAxis 
            dataKey="name" 
            type="category" 
            axisLine={false} 
            tickLine={false} 
            width={120} 
            tick={{ fontSize: 12, fill: '#475569', fontWeight: 500 }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#FFFFFF', 
              borderColor: '#E2E8F0', 
              borderRadius: '8px', 
              fontSize: '12px', 
              color: '#0F172A', 
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' 
            }}
            formatter={(value: number, name: string, props: any) => {
              if (name === 'count') return [value, 'Count'];
              return [formatINR(value), 'Amount'];
            }}
          />
          <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={28}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
