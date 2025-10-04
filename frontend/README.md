# Pulse ERP Frontend

Modern ERP frontend built with Next.js 14, TypeScript, and Tailwind CSS.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **State Management:** React hooks (future: Zustand/Redux)

## Getting Started

### Prerequisites

- Node.js 20+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env with your API endpoints
```

### Development

```bash
# Start development server
npm run dev

# Open http://localhost:3001
```

### Build

```bash
# Type check
npm run type-check

# Build for production
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── app/                 # Next.js App Router pages
│   ├── layout.tsx      # Root layout
│   ├── page.tsx        # Home page
│   └── globals.css     # Global styles
├── components/          # React components
├── lib/                 # Utilities and API clients
│   ├── api-client.ts   # Axios API client
│   └── utils.ts        # Helper functions
├── types/              # TypeScript type definitions
│   └── index.ts        # Shared types
├── public/             # Static assets
└── package.json        # Dependencies

```

## API Integration

### OLTP APIs (Orders, Inventory, Billing)

```typescript
import { api } from '@/lib/api-client';

// Get orders
const orders = await api.orders.list();

// Create order
const order = await api.orders.create({
  customer_id: '123',
  items: [{ sku: 'WIDGET-001', qty: 2, price: 99.99 }]
});
```

### OLAP APIs (Analytics)

```typescript
import { olapApi } from '@/lib/api-client';

// Get sales data
const sales = await olapApi.sales.hourly(24);

// Get low stock items
const lowStock = await olapApi.inventory.lowStock();
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | OLTP API base URL | `http://localhost:8001` |
| `OLAP_API_URL` | OLAP API base URL | `http://localhost:8004` |
| `GRAFANA_URL` | Grafana dashboard URL | `http://localhost:3000` |

## Features

- ✅ TypeScript strict mode
- ✅ Tailwind CSS styling
- ✅ API client with interceptors
- ✅ Type-safe API methods
- ✅ Responsive layout
- ✅ Dark mode support
- ⏳ Authentication (coming in Sprint 2)
- ⏳ State management (coming in Sprint 2)

## Development Guidelines

### Code Style

- Use TypeScript strict mode
- Follow Next.js best practices
- Use functional components with hooks
- Prefer server components when possible

### Naming Conventions

- Components: PascalCase (e.g., `OrderList.tsx`)
- Files: kebab-case (e.g., `api-client.ts`)
- Folders: kebab-case (e.g., `lib/`)

### Component Structure

```typescript
// components/OrderCard.tsx
interface OrderCardProps {
  order: Order;
  onUpdate?: (id: string) => void;
}

export function OrderCard({ order, onUpdate }: OrderCardProps) {
  // Component logic
}
```

## Testing

```bash
# Coming in Sprint 2
# npm test
# npm run test:e2e
```

## Deployment

See `/docs/DEPLOYMENT.md` for Docker deployment instructions.

## License

MIT
