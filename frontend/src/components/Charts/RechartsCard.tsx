import React from 'react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { ChartSpec } from '../../services/api';

const PALETTE = [
  '#4f46e5', // Indigo Slate
  '#0284c7', // Sky
  '#059669', // Emerald
  '#d97706', // Amber
  '#7c3aed', // Purple
  '#0d9488', // Teal
  '#e11d48', // Rose
];

interface RechartsCardProps {
  spec: ChartSpec;
}

export const RechartsCard: React.FC<RechartsCardProps> = ({ spec }) => {
  const { chart_type, title, description, x_key, y_keys, data } = spec;

  const formatTooltipName = (name: any) => {
    if (typeof name === 'string') {
      return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase());
    }
    return name;
  };

  const formatTooltipValue = (value: any, name: any) => {
    const formattedVal =
      typeof value === 'number'
        ? `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
        : value;
    const formattedName = formatTooltipName(name);
    return [formattedVal, formattedName];
  };

  const renderChart = () => {
    if (!data || data.length === 0) {
      return (
        <div className="flex h-56 items-center justify-center text-slate-500 text-sm">
          No chart data available
        </div>
      );
    }

    if (chart_type === 'pie') {
      const metricKey = y_keys[0] || 'amount';
      return (
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Tooltip
              formatter={formatTooltipValue}
              cursor={{ fill: 'rgba(255, 255, 255, 0.05)', radius: 6 }}
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)' }}
            />
            <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
            <Pie
              data={data}
              dataKey={metricKey}
              nameKey={x_key}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={3}
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={PALETTE[index % PALETTE.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      );
    }

    if (chart_type === 'bar') {
      return (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
            <defs>
              <linearGradient id="barGradientPrimary" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366f1" stopOpacity={0.9} />
                <stop offset="100%" stopColor="#4338ca" stopOpacity={0.65} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey={x_key}
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              interval={0}
              angle={-20}
              textAnchor="end"
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => `₹${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`}
            />
            <Tooltip
              formatter={formatTooltipValue}
              cursor={{ fill: 'rgba(255, 255, 255, 0.03)' }}
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                color: '#f8fafc',
                boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)',
              }}
            />
            {y_keys.map((key, i) => (
              <Bar
                key={key}
                dataKey={key}
                fill={i === 0 ? 'url(#barGradientPrimary)' : PALETTE[i % PALETTE.length]}
                radius={[6, 6, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      );
    }

    // Default: area chart
    return (
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.6} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey={x_key} stroke="#64748b" fontSize={11} tickLine={false} />
          <YAxis
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            tickFormatter={(v) => `₹${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`}
          />
          <Tooltip
            formatter={formatTooltipValue}
            cursor={{ stroke: 'rgba(99, 102, 241, 0.4)', strokeWidth: 1.5, strokeDasharray: '3 3' }}
            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)' }}
          />
          {y_keys.map((key) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stroke="#6366f1"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#areaGradient)"
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl">
      <div className="mb-3">
        <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
          {title}
        </h4>
        {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
      </div>
      <div className="w-full">{renderChart()}</div>
    </div>
  );
};

