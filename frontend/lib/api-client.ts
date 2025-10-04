import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8001';
const OLAP_API_URL = process.env.OLAP_API_URL || 'http://localhost:8004';

// OLTP API Client (Orders, Inventory, Billing)
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// OLAP API Client (Analytics, Reports)
export const olapClient: AxiosInstance = axios.create({
  baseURL: OLAP_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication (when implemented)
apiClient.interceptors.request.use(
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
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized (redirect to login when auth is implemented)
      console.error('Unauthorized access');
    }
    return Promise.reject(error);
  }
);

// Same interceptors for OLAP client
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
    list: () => apiClient.get('/orders'),
    get: (id: string) => apiClient.get(`/orders/${id}`),
    create: (data: any) => apiClient.post('/orders', data),
    update: (id: string, data: any) => apiClient.patch(`/orders/${id}`, data),
  },

  // Inventory
  inventory: {
    list: () => apiClient.get('/inventory'),
    create: (data: any) => apiClient.post('/inventory', data),
    reserve: (sku: string, data: any) =>
      apiClient.post(`/inventory/${sku}/reserve`, data),
  },

  // Billing
  billing: {
    listInvoices: () => apiClient.get('/billing/invoices'),
    getInvoice: (id: string) => apiClient.get(`/billing/invoices/${id}`),
    createInvoice: (data: any) => apiClient.post('/billing/invoices', data),
  },
};

// OLAP API methods
export const olapApi = {
  // Sales
  sales: {
    hourly: (hours: number = 24) =>
      olapClient.get(`/query/sales/hourly?hours=${hours}`),
  },

  // Inventory
  inventory: {
    lowStock: () => olapClient.get('/query/inventory/low-stock'),
    movement: (limit: number = 50) =>
      olapClient.get(`/query/inventory/movement?limit=${limit}`),
  },

  // AR
  ar: {
    overdue: () => olapClient.get('/query/ar/overdue'),
  },

  // Orders
  orders: {
    daily: (days: number = 30) =>
      olapClient.get(`/query/orders/daily?days=${days}`),
  },
};

export default apiClient;
