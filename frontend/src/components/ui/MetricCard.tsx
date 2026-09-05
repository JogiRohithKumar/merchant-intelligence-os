interface MetricCardProps {
  label: string;
  value: string;
  change: number;
}

const MetricCard = ({ label, value, change }: MetricCardProps) => {
  return (
    <div className="p-4 bg-white rounded shadow">
      <div className="text-gray-500 text-sm">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
      <div className={`text-sm ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
        {change >= 0 ? '+' : ''}{change}%
      </div>
    </div>
  );
};

export default MetricCard;
