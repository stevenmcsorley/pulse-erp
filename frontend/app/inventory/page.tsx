'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api-client';
import { Product, InventoryItem } from '@/types';
import { formatCurrency, formatNumber } from '@/lib/utils';

interface InventoryItemWithProduct extends InventoryItem {
  product?: Product;
}

export default function InventoryPage() {
  const [inventory, setInventory] = useState<InventoryItemWithProduct[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [productsRes] = await Promise.all([
        api.inventory.list(), // This returns List<ProductResponse>
      ]);

      const productsWithInventory = productsRes.data; // This is List<ProductResponse>

      const inventoryItems: InventoryItemWithProduct[] = [];
      productsWithInventory.forEach((product: Product) => {
        if (product.inventory) {
          inventoryItems.push({
            ...product.inventory,
            product: product, // Attach the full product object
          });
        }
      });

      setProducts(productsWithInventory); // Set products as well
      setInventory(inventoryItems); // Set the correctly structured inventory
    } catch (error) {
      console.error('Failed to load inventory:', error);
      setError('Failed to load inventory');
    } finally {
      setLoading(false);
    }
  };

  const getAvailableQty = (item: InventoryItem) => {
    const onHand = item.qty_on_hand ?? 0;
    const reserved = item.reserved_qty ?? 0;
    return onHand - reserved;
  };

  const isLowStock = (item: InventoryItem) => {
    const available = getAvailableQty(item);
    const reorderPoint = 10; // Could be configurable per product
    return available <= reorderPoint;
  };

  const filteredInventory = inventory.filter((item) => {
    const matchesSearch =
      item.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.product?.name.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter = !showLowStockOnly || isLowStock(item);

    return matchesSearch && matchesFilter;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-8"></div>
            <div className="space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Inventory</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              Manage products and stock levels
            </p>
          </div>
          <Link
            href="/inventory/products/new"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            + Add Product
          </Link>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search by SKU or product name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
            </div>
            <label className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
              <input
                type="checkbox"
                checked={showLowStockOnly}
                onChange={(e) => setShowLowStockOnly(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <span>Show low stock only</span>
            </label>
          </div>
        </div>

        {/* Inventory Table */}
        {filteredInventory.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-12 text-center">
            <div className="text-gray-400 dark:text-gray-500 mb-4">
              <svg className="mx-auto h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {searchTerm || showLowStockOnly ? 'No items found' : 'No inventory items'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {searchTerm || showLowStockOnly
                ? 'Try adjusting your filters'
                : 'Get started by adding your first product'}
            </p>
            {!searchTerm && !showLowStockOnly && (
              <Link
                href="/inventory/products/new"
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Add Product
              </Link>
            )}
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      SKU
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Product Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      On Hand
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Reserved
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Available
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredInventory.map((item) => {
                    const available = getAvailableQty(item);
                    const lowStock = isLowStock(item);

                    return (
                      <tr
                        key={item.sku}
                        className={`hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors ${
                          lowStock ? 'bg-yellow-50 dark:bg-yellow-900/10' : ''
                        }`}
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                          {item.sku}
                          {lowStock && (
                            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
                              Low Stock
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {item.product?.name || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {item.product ? formatCurrency(item.product.price) : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100 text-right">
                          {formatNumber(item.qty_on_hand ?? 0)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right">
                          {formatNumber(item.reserved_qty ?? 0)}
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${
                          lowStock
                            ? 'text-yellow-600 dark:text-yellow-400'
                            : 'text-green-600 dark:text-green-400'
                        }`}>
                          {formatNumber(available)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm space-x-2">
                          <Link
                            href={`/inventory/products/${item.sku}/edit`}
                            className="text-blue-600 dark:text-blue-400 hover:underline"
                          >
                            Edit
                          </Link>
                          <Link
                            href={`/inventory/stock/${item.sku}`}
                            className="text-green-600 dark:text-green-400 hover:underline"
                          >
                            Adjust Stock
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Stats */}
        {filteredInventory.length > 0 && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Products</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatNumber(filteredInventory.length)}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">Low Stock Items</p>
              <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                {formatNumber(filteredInventory.filter(isLowStock).length)}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Units</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatNumber(filteredInventory.reduce((sum, item) => sum + (item.qty_on_hand ?? 0), 0))}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
