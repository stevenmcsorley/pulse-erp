'use client';

import { useState } from 'react';

type DashboardType = 'sales' | 'inventory' | 'cashflow';

interface Dashboard {
  id: DashboardType;
  name: string;
  description: string;
  path: string;
}

const dashboards: Dashboard[] = [
  {
    id: 'sales',
    name: 'Sales Analytics',
    description: 'Real-time sales metrics, order volume, and revenue trends',
    path: '/d/sales-analytics/sales-analytics',
  },
  {
    id: 'inventory',
    name: 'Inventory Status',
    description: 'Stock levels, low inventory alerts, and movement tracking',
    path: '/d/inventory-status/inventory-status',
  },
  {
    id: 'cashflow',
    name: 'Cashflow & AR',
    description: 'Accounts receivable, payment trends, and aging reports',
    path: '/d/cashflow-ar/cashflow-ar',
  },
];

export default function DashboardsPage() {
  const [selectedDashboard, setSelectedDashboard] = useState<DashboardType>('sales');
  const [loading, setLoading] = useState(true);

  const grafanaUrl = process.env.NEXT_PUBLIC_GRAFANA_URL || process.env.GRAFANA_URL || 'http://localhost:3000';
  const currentDashboard = dashboards.find(d => d.id === selectedDashboard);

  const getIframeUrl = (dashboard: Dashboard) => {
    const params = new URLSearchParams({
      orgId: '1',
      refresh: '10s',
      kiosk: 'tv',
    });
    return `${grafanaUrl}${dashboard.path}?${params.toString()}`;
  };

  const handleIframeLoad = () => {
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Analytics Dashboards</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Real-time business intelligence and metrics
          </p>
        </div>

        {/* Dashboard Selector */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {dashboards.map((dashboard) => (
              <button
                key={dashboard.id}
                onClick={() => {
                  setSelectedDashboard(dashboard.id);
                  setLoading(true);
                }}
                className={`p-4 rounded-lg text-left transition-all ${
                  selectedDashboard === dashboard.id
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600'
                }`}
              >
                <h3 className={`font-semibold mb-1 ${
                  selectedDashboard === dashboard.id
                    ? 'text-white'
                    : 'text-gray-900 dark:text-white'
                }`}>
                  {dashboard.name}
                </h3>
                <p className={`text-sm ${
                  selectedDashboard === dashboard.id
                    ? 'text-blue-100'
                    : 'text-gray-600 dark:text-gray-400'
                }`}>
                  {dashboard.description}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Dashboard Embed */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
          <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {currentDashboard?.name}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Auto-refreshing every 10 seconds
            </p>
          </div>

          <div className="relative bg-gray-100 dark:bg-gray-900" style={{ paddingBottom: '56.25%' }}>
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600 dark:text-gray-400">Loading dashboard...</p>
                </div>
              </div>
            )}

            {currentDashboard && (
              <iframe
                src={getIframeUrl(currentDashboard)}
                className="absolute inset-0 w-full h-full"
                frameBorder="0"
                onLoad={handleIframeLoad}
                title={currentDashboard.name}
              />
            )}
          </div>

          {/* Info Banner */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border-t border-blue-200 dark:border-blue-800 px-6 py-3">
            <div className="flex items-center text-sm text-blue-800 dark:text-blue-200">
              <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>
                Dashboards are powered by Grafana and display real-time data from the OLAP database
              </span>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-8 w-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">Sales Analytics</p>
                <p className="text-xs text-gray-500 dark:text-gray-500">Revenue & orders</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-8 w-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">Inventory Status</p>
                <p className="text-xs text-gray-500 dark:text-gray-500">Stock levels & alerts</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-8 w-8 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">Cashflow & AR</p>
                <p className="text-xs text-gray-500 dark:text-gray-500">Receivables & payments</p>
              </div>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Dashboard Configuration
              </h3>
              <div className="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
                <p className="mb-2">
                  Dashboards are embedded from Grafana running at <code className="bg-yellow-100 dark:bg-yellow-900/50 px-1 rounded">{grafanaUrl}</code>
                </p>
                <p>
                  If dashboards are not loading, ensure:
                </p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>Grafana is running and accessible</li>
                  <li>Anonymous access is enabled in Grafana</li>
                  <li>Dashboard UIDs match the configured paths</li>
                  <li>GRAFANA_URL environment variable is set correctly</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
