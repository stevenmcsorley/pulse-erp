import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011';
const OLAP_API_URL = process.env.NEXT_PUBLIC_OLAP_API_URL || 'http://localhost:8014';

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

  // Products (using inventory API)
  products: {
    list: () => apiClient.get('/inventory'),
    get: (sku: string) => apiClient.get(`/inventory/${sku}`),
    create: (data: any) => apiClient.post('/inventory', data),
    update: (sku: string, data: any) => apiClient.put(`/inventory/${sku}`, data),
  },

  // Inventory
  inventory: {
    list: () => apiClient.get('/inventory'),
    listProducts: () => apiClient.get('/inventory'),
    get: (sku: string) => apiClient.get(`/inventory/${sku}`),
    getProduct: (sku: string) => apiClient.get(`/inventory/${sku}`),
    createProduct: (data: any) => apiClient.post('/inventory', data),
    update: (sku: string, data: any) => apiClient.put(`/inventory/${sku}`, data),
    updateProduct: (sku: string, data: any) => apiClient.put(`/inventory/${sku}`, data),
    reserve: (sku: string, data: any) => apiClient.post(`/inventory/${sku}/reserve`, data),
  },

  // Billing/Invoices
  billing: {
    listInvoices: () => apiClient.get('/billing/invoices'),
    getInvoice: (id: string) => apiClient.get(`/billing/invoices/${id}`),
    createInvoice: (data: any) => apiClient.post('/billing/invoices', data),
    payInvoice: (id: string) => apiClient.post(`/billing/invoices/${id}/pay`),
    markAsPaid: (id: string) => apiClient.post(`/billing/invoices/${id}/pay`),
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

export default apiClient;
