'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api-client';
import { Product, InventoryItem } from '@/types';
import { formatNumber } from '@/lib/utils';

export default function StockAdjustmentPage() {
  const params = useParams();
  const router = useRouter();
  const sku = params.sku as string;

  const [product, setProduct] = useState<Product | null>(null);
  const [inventory, setInventory] = useState<InventoryItem | null>(null);
  const [adjustment, setAdjustment] = useState('');
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (sku) {
      loadData();
    }
  }, [sku]);

  const loadData = async () => {
    try {
      const productRes = await api.inventory.getProduct(sku); // This returns ProductResponse

      setProduct(productRes.data);
      // Extract inventory item from the product response
      if (productRes.data.inventory) {
        setInventory(productRes.data.inventory);
      } else {
        // Handle case where product has no inventory item (e.g., set default 0s)
        setInventory({ sku: sku, qty_on_hand: 0, reserved_qty: 0 });
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      setError('Failed to load product information');
    } finally {
      setLoading(false);
    }
  };

  const handleAdjustment = async (delta: number) => {
    if (!inventory) return;

    setUpdating(true);
    setError('');

    try {
      const newQty = (inventory.qty_on_hand ?? 0) + delta;

      if (newQty < 0) {
        setError('Adjustment would result in negative stock');
        setUpdating(false);
        return;
      }

      await api.inventory.adjustStock(sku, delta);
      await loadData();
      setAdjustment('');
    } catch (error: any) {
      console.error('Failed to update stock:', error);
      setError(
        error.response?.data?.detail ||
        'Failed to update stock. Please try again.'
      );
    } finally {
      setUpdating(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const delta = parseInt(adjustment);

    if (isNaN(delta) || delta === 0) {
      setError('Please enter a valid adjustment amount');
      return;
    }

    handleAdjustment(delta);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-3xl mx-auto px-4">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-8"></div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
              <div className="space-y-4">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!product || !inventory) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-3xl mx-auto px-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
            <p className="text-red-800 dark:text-red-200 mb-4">Product not found</p>
            <Link
              href="/inventory"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              ← Back to Inventory
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const available = (inventory.qty_on_hand ?? 0) - (inventory.reserved_qty ?? 0);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <div className="mb-6">
          <Link
            href="/inventory"
            className="text-blue-600 dark:text-blue-400 hover:underline mb-4 inline-block"
          >
            ← Back to Inventory
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Stock Adjustment</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {product.name} ({product.sku})
          </p>
        </div>

        {/* Current Stock Levels */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Current Stock Levels
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">On Hand</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">
                {formatNumber(inventory.qty_on_hand ?? 0)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Reserved</p>
              <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                {formatNumber(inventory.reserved_qty ?? 0)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Available</p>
              <p className={`text-3xl font-bold ${
                available <= 10
                  ? 'text-yellow-600 dark:text-yellow-400'
                  : 'text-green-600 dark:text-green-400'
              }`}>
                {formatNumber(available)}
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Adjustment Form */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Adjust Stock
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="adjustment" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Adjustment Amount
              </label>
              <input
                type="number"
                id="adjustment"
                value={adjustment}
                onChange={(e) => setAdjustment(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                placeholder="Enter positive or negative number"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Positive numbers increase stock, negative numbers decrease stock
              </p>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={updating || !adjustment}
                className="flex-1 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {updating ? 'Updating...' : 'Apply Adjustment'}
              </button>
            </div>
          </form>

          {/* Quick Actions */}
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Quick Actions
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <button
                onClick={() => handleAdjustment(10)}
                disabled={updating}
                className="px-4 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-md hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                +10
              </button>
              <button
                onClick={() => handleAdjustment(50)}
                disabled={updating}
                className="px-4 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-md hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                +50
              </button>
              <button
                onClick={() => handleAdjustment(-10)}
                disabled={updating}
                className="px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-md hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                -10
              </button>
              <button
                onClick={() => handleAdjustment(-50)}
                disabled={updating}
                className="px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-md hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                -50
              </button>
            </div>
          </div>
        </div>

        {/* Warning */}
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Important Note
              </p>
              <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                Stock adjustments do not affect reserved quantities. Reserved stock is managed automatically through the order fulfillment process.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
