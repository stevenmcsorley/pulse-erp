export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <main className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-4">
            Pulse ERP
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Modular ERP with Real-time Business Intelligence
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          <Card
            title="Orders"
            description="Manage customer orders and track fulfillment"
            href="/orders"
            icon="📦"
          />
          <Card
            title="Inventory"
            description="Track stock levels and manage reservations"
            href="/inventory"
            icon="📊"
          />
          <Card
            title="Billing"
            description="Create invoices and manage accounts receivable"
            href="/billing"
            icon="💰"
          />
          <Card
            title="Dashboards"
            description="Real-time analytics and business intelligence"
            href="/dashboards"
            icon="📈"
          />
          <Card
            title="Reports"
            description="Generate reports and export data"
            href="/reports"
            icon="📋"
          />
          <Card
            title="Settings"
            description="Configure system settings and preferences"
            href="/settings"
            icon="⚙️"
          />
        </div>

        <div className="mt-16 text-center">
          <div className="inline-flex items-center gap-2 bg-white dark:bg-gray-800 rounded-lg px-6 py-3 shadow-md">
            <span className="inline-block w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
            <span className="text-sm text-gray-600 dark:text-gray-300">
              System Status: Operational
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}

function Card({
  title,
  description,
  href,
  icon,
}: {
  title: string;
  description: string;
  href: string;
  icon: string;
}) {
  return (
    <a
      href={href}
      className="block p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200"
    >
      <div className="text-4xl mb-4">{icon}</div>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        {title}
      </h2>
      <p className="text-gray-600 dark:text-gray-300">{description}</p>
    </a>
  );
}
