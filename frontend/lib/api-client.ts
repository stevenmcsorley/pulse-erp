import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

const ORDERS_API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011'; // Orders
const INVENTORY_API_URL = process.env.NEXT_PUBLIC_INVENTORY_API_URL || 'http://localhost:8012';
const BILLING_API_URL = process.env.NEXT_PUBLIC_BILLING_API_URL || 'http://localhost:8013';
const OLAP_API_URL = process.env.NEXT_PUBLIC_OLAP_API_URL || 'http://localhost:8014';
console.log('INVENTORY_API_URL:', INVENTORY_API_URL);
console.log('INVENTORY_API_URL:', INVENTORY_API_URL);
console.log('INVENTORY_API_URL:', INVENTORY_API_URL);

export const ordersClient: AxiosInstance = axios.create({
  baseURL: ORDERS_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const inventoryClient: AxiosInstance = axios.create({
  baseURL: INVENTORY_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const billingClient: AxiosInstance = axios.create({
  baseURL: BILLING_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const olapClient: AxiosInstance = axios.create({
  baseURL: OLAP_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication (when implemented)
ordersClient.interceptors.request.use(
  (config) => {
    // Add auth token when available
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
ordersClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized (redirect to login when auth is implemented)
      console.error('Unauthorized access');
    }
    return Promise.reject(error);
  }
);

// Same interceptors for other clients (if needed, or apply to each individually)
inventoryClient.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);
inventoryClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
);

billingClient.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);
billingClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
);

olapClient.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);

olapClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
);

// Type-safe API methods
export const api = {
  // Orders
  orders: {
    list: () => ordersClient.get('/orders'),
    get: (id: string) => ordersClient.get(`/orders/${id}`),
    create: (data: any) => ordersClient.post('/orders', data),
    update: (id: string, data: any) => ordersClient.patch(`/orders/${id}`, data),
  },

  // Products (using inventory API)
  products: {
    list: () => inventoryClient.get('/inventory'),
    get: (sku: string) => inventoryClient.get(`/inventory/${sku}`),
    create: (data: any) => inventoryClient.post('/inventory', data),
    update: (sku: string, data: any) => inventoryClient.put(`/inventory/${sku}`, data),
  },

  // Inventory
  inventory: {
    list: () => inventoryClient.get('/inventory'),
    listProducts: () => inventoryClient.get('/inventory'),
    get: (sku: string) => inventoryClient.get(`/inventory/${sku}`),
    getProduct: (sku: string) => inventoryClient.get(`/inventory/${sku}`),
    createProduct: (data: any) => inventoryClient.post('/inventory', data),
    update: (sku: string, data: any) => inventoryClient.put(`/inventory/${sku}`, data),
    updateProduct: (sku: string, data: any) => inventoryClient.put(`/inventory/${sku}`, data),
    adjustStock: (sku: string, adjustment: number) => inventoryClient.patch(`/inventory/${sku}/adjust-stock`, { adjustment }),
    reserve: (sku: string, data: any) => inventoryClient.post(`/inventory/${sku}/reserve`, data),
  },

  // Billing/Invoices
  billing: {
    listInvoices: () => billingClient.get('/billing/invoices'),
    getInvoice: (id: string) => billingClient.get(`/billing/invoices/${id}`),
    createInvoice: (data: any) => billingClient.post('/billing/invoices', data),
    payInvoice: (id: string) => billingClient.post(`/billing/invoices/${id}/pay`),
    markAsPaid: (id: string) => billingClient.post(`/billing/invoices/${id}/pay`),
  },
};

// OLAP API methods
export const olapApi = {
  // Sales
  sales: {
    hourly: (hours: number = 24) =>
      olapClient.get(`/sales/hourly?hours=${hours}`),
  },

  // Inventory
  inventory: {
    lowStock: () => olapClient.get('/inventory/low-stock'),
    movement: (limit: number = 50) =>
      olapClient.get(`/inventory/movement?limit=${limit}`),
  },

  // AR
  ar: {
    overdue: () => olapClient.get('/ar/overdue'),
  },

  // Orders
  orders: {
    daily: (days: number = 30) =>
      olapClient.get(`/orders/daily?days=${days}`),
  },
};

export default ordersClient;
