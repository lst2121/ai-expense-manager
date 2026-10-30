import React from 'react';
import { RechartsCard } from '../Charts/RechartsCard';
import type { KpiData, ChartSpec } from '../../services/api';

interface AnalyticsOverviewProps {
  kpis: KpiData | null;
}

export const AnalyticsOverview: React.FC<AnalyticsOverviewProps> = ({ kpis }) => {
  if (!kpis) return null;

  const trendChartSpec: ChartSpec = {
    __chart__: true,
    chart_type: 'area',
    title: 'Monthly Spending Trajectory (2025)',
    description: 'Monthly family expenditure trend over the past 6 months',
    x_key: 'month',
    y_keys: ['spend'],
    data: kpis.monthly_trend,
  };

  const categoryChartSpec: ChartSpec = {
    __chart__: true,
    chart_type: 'bar',
    title: 'Expense Distribution by Category',
    description: 'Total spend volume organized by primary operational category',
    x_key: 'category',
    y_keys: ['amount'],
    data: kpis.category_distribution,
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <RechartsCard spec={trendChartSpec} />
      <RechartsCard spec={categoryChartSpec} />
    </div>
  );
};

