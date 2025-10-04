import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011';
const INVENTORY_API_URL = process.env.NEXT_PUBLIC_INVENTORY_API_URL || 'http://localhost:8012';
const BILLING_API_URL = process.env.NEXT_PUBLIC_BILLING_API_URL || 'http://localhost:8013';
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
    list: () => apiClient.get(`${INVENTORY_API_URL}/inventory`),
    get: (sku: string) => apiClient.get(`${INVENTORY_API_URL}/inventory/${sku}`),
    create: (data: any) => apiClient.post(`${INVENTORY_API_URL}/inventory`, data),
    update: (sku: string, data: any) => apiClient.put(`${INVENTORY_API_URL}/inventory/${sku}`, data),
  },

  // Inventory
  inventory: {
    list: () => apiClient.get(`${INVENTORY_API_URL}/inventory`),
    listProducts: () => apiClient.get(`${INVENTORY_API_URL}/inventory`),
    get: (sku: string) => apiClient.get(`${INVENTORY_API_URL}/inventory/${sku}`),
    getProduct: (sku: string) => apiClient.get(`${INVENTORY_API_URL}/inventory/${sku}`),
    createProduct: (data: any) => apiClient.post(`${INVENTORY_API_URL}/inventory`, data),
    update: (sku: string, data: any) => apiClient.put(`${INVENTORY_API_URL}/inventory/${sku}`, data),
    updateProduct: (sku: string, data: any) => apiClient.put(`${INVENTORY_API_URL}/inventory/${sku}`, data),
    reserve: (sku: string, data: any) => apiClient.post(`${INVENTORY_API_URL}/inventory/${sku}/reserve`, data),
  },

  // Billing/Invoices
  billing: {
    listInvoices: () => apiClient.get(`${BILLING_API_URL}/invoices`),
    getInvoice: (id: string) => apiClient.get(`${BILLING_API_URL}/invoices/${id}`),
    createInvoice: (data: any) => apiClient.post(`${BILLING_API_URL}/invoices`, data),
    payInvoice: (id: string) => apiClient.post(`${BILLING_API_URL}/invoices/${id}/pay`),
    markAsPaid: (id: string) => apiClient.post(`${BILLING_API_URL}/invoices/${id}/pay`),
  },
};

// OLAP API methods
export const olapApi = {
  // Sales
  sales: {
    hourly: (hours: number = 24) =>
      olapClient.get(`${OLAP_API_URL}/sales/hourly?hours=${hours}`),
  },

  // Inventory
  inventory: {
    lowStock: () => olapClient.get(`${OLAP_API_URL}/inventory/low-stock`),
    movement: (limit: number = 50) =>
      olapClient.get(`${OLAP_API_URL}/inventory/movement?limit=${limit}`),
  },

  // AR
  ar: {
    overdue: () => olapClient.get(`${OLAP_API_URL}/ar/overdue`),
  },

  // Orders
  orders: {
    daily: (days: number = 30) =>
      olapClient.get(`${OLAP_API_URL}/orders/daily?days=${days}`),
  },
};

export default apiClient;
