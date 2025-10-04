'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';
import { Product } from '@/types';
import { formatCurrency } from '@/lib/utils';

interface OrderItem {
  sku: string;
  qty: number;
  price: number;
}

interface FormErrors {
  customer_id?: string;
  items?: string;
  [key: string]: string | undefined;
}

export default function NewOrderPage() {
  const router = useRouter();
  const [customerId, setCustomerId] = useState('');
  const [items, setItems] = useState<OrderItem[]>([{ sku: '', qty: 1, price: 0 }]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitError, setSubmitError] = useState('');

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      const response = await api.inventory.listProducts();
      setProducts(response.data);
    } catch (error) {
      console.error('Failed to load products:', error);
    } finally {
      setLoadingProducts(false);
    }
  };

  const handleAddItem = () => {
    setItems([...items, { sku: '', qty: 1, price: 0 }]);
  };

  const handleRemoveItem = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  const handleItemChange = (index: number, field: keyof OrderItem, value: string | number) => {
    const newItems = [...items];
    if (field === 'sku') {
      const product = products.find(p => p.sku === value);
      newItems[index] = {
        sku: value as string,
        qty: newItems[index].qty,
        price: product?.price || 0,
      };
    } else {
      newItems[index] = { ...newItems[index], [field]: value };
    }
    setItems(newItems);
  };

  const calculateTotal = () => {
    return items.reduce((sum, item) => sum + (item.qty * item.price), 0);
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!customerId.trim()) {
      newErrors.customer_id = 'Customer ID is required';
    } else if (!/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(customerId)) {
      newErrors.customer_id = 'Customer ID must be a valid UUID format';
    }

    if (items.length === 0 || items.every(item => !item.sku)) {
      newErrors.items = 'At least one item is required';
    }

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.sku && item.qty <= 0) {
        newErrors[`item_${i}_qty`] = 'Quantity must be greater than 0';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const validItems = items.filter(item => item.sku);
      const response = await api.orders.create({
        customer_id: customerId,
        items: validItems,
      });

      router.push(`/orders/${response.data.id}`);
    } catch (error: any) {
      console.error('Failed to create order:', error);
      setSubmitError(
        error.response?.data?.detail ||
        'Failed to create order. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Create New Order</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Fill in the order details below
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          {submitError && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
              <p className="text-red-800 dark:text-red-200">{submitError}</p>
            </div>
          )}

          {/* Customer ID */}
          <div className="mb-6">
            <label htmlFor="customerId" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Customer ID *
            </label>
            <input
              type="text"
              id="customerId"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              className={`w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white ${
                errors.customer_id ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
              }`}
              placeholder="e.g., a1b2c3d4-e5f6-7890-1234-567890abcdef"
            />
            {errors.customer_id && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.customer_id}</p>
            )}
          </div>

          {/* Order Items */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Order Items *
              </label>
              <button
                type="button"
                onClick={handleAddItem}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                + Add Item
              </button>
            </div>

            {errors.items && (
              <p className="mb-3 text-sm text-red-600 dark:text-red-400">{errors.items}</p>
            )}

            <div className="space-y-4">
              {items.map((item, index) => (
                <div key={index} className="flex gap-3 items-start p-4 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                  <div className="flex-1">
                    <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                      Product SKU
                    </label>
                    <select
                      value={item.sku}
                      onChange={(e) => handleItemChange(index, 'sku', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                      disabled={loadingProducts}
                    >
                      <option value="">Select product...</option>
                      {products.map((product) => (
                        <option key={product.sku} value={product.sku}>
                          {product.sku} - {product.name} ({formatCurrency(product.price)})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="w-24">
                    <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                      Quantity
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={item.qty}
                      onChange={(e) => handleItemChange(index, 'qty', parseInt(e.target.value) || 1)}
                      className={`w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:text-white ${
                        errors[`item_${index}_qty`] ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                      }`}
                    />
                  </div>

                  <div className="w-32">
                    <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                      Price
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={item.price}
                      onChange={(e) => handleItemChange(index, 'price', parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                    />
                  </div>

                  <div className="w-32">
                    <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                      Subtotal
                    </label>
                    <div className="px-3 py-2 bg-gray-100 dark:bg-gray-600 rounded-md text-gray-900 dark:text-white">
                      {formatCurrency(item.qty * item.price)}
                    </div>
                  </div>

                  {items.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveItem(index)}
                      className="mt-6 px-3 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Total */}
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-md">
            <div className="flex justify-between items-center">
              <span className="text-lg font-semibold text-gray-900 dark:text-white">Total Amount:</span>
              <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {formatCurrency(calculateTotal())}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={() => router.push('/orders')}
              className="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Order'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
