'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api-client';
import { Invoice, Order } from '@/types';
import { formatCurrency, formatDate, formatDateTime } from '@/lib/utils';

export default function InvoiceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const invoiceId = params.id as string;

  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (invoiceId) {
      loadInvoice();
    }
  }, [invoiceId]);

  const loadInvoice = async () => {
    try {
      const invoiceRes = await api.billing.getInvoice(invoiceId);
      const invoiceData = invoiceRes.data;
      setInvoice(invoiceData);

      // Load associated order
      try {
        const orderRes = await api.orders.get(invoiceData.order_id);
        setOrder(orderRes.data);
      } catch (err) {
        console.error('Failed to load order:', err);
      }
    } catch (error) {
      console.error('Failed to load invoice:', error);
      setError('Failed to load invoice');
    } finally {
      setLoading(false);
    }
  };

  const isOverdue = (inv: Invoice) => {
    if (inv.status === 'paid' || inv.status === 'cancelled') {
      return false;
    }
    return new Date(inv.due_date) < new Date();
  };

  const getStatusColor = (inv: Invoice) => {
    if (isOverdue(inv)) {
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
    }

    const colors = {
      issued: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      paid: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
      cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    };
    return colors[inv.status as keyof typeof colors] || colors.issued;
  };

  const getStatusLabel = (inv: Invoice) => {
    if (isOverdue(inv)) {
      return 'Overdue';
    }
    return inv.status.charAt(0).toUpperCase() + inv.status.slice(1);
  };

  const handleMarkAsPaid = async () => {
    if (!invoice) return;

    setProcessing(true);
    try {
      await api.billing.markAsPaid(invoice.id);
      setShowPaymentModal(false);
      await loadInvoice();
    } catch (error: any) {
      console.error('Failed to mark invoice as paid:', error);
      alert(error.response?.data?.detail || 'Failed to mark invoice as paid');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-5xl mx-auto px-4">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-8"></div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 mb-6">
              <div className="space-y-4">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !invoice) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-5xl mx-auto px-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
            <p className="text-red-800 dark:text-red-200 mb-4">{error || 'Invoice not found'}</p>
            <Link
              href="/invoices"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              ← Back to Invoices
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-5xl mx-auto px-4">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/invoices"
            className="text-blue-600 dark:text-blue-400 hover:underline mb-4 inline-block"
          >
            ← Back to Invoices
          </Link>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Invoice Details
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Invoice ID: {invoice.id}
              </p>
            </div>
            <span className={`px-4 py-2 text-sm font-semibold rounded-full ${getStatusColor(invoice)}`}>
              {getStatusLabel(invoice)}
            </span>
          </div>
        </div>

        {/* Invoice Info */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Invoice Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Amount</p>
              <p className="text-gray-900 dark:text-white font-medium text-2xl">
                {formatCurrency(invoice.amount)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Order ID</p>
              <Link
                href={`/orders/${invoice.order_id}`}
                className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
              >
                {invoice.order_id}
              </Link>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Issued Date</p>
              <p className="text-gray-900 dark:text-white font-medium">
                {formatDateTime(invoice.issued_at)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Due Date</p>
              <p className={`font-medium ${
                isOverdue(invoice)
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-gray-900 dark:text-white'
              }`}>
                {formatDateTime(invoice.due_date)}
                {isOverdue(invoice) && (
                  <span className="ml-2 text-xs">
                    (Overdue)
                  </span>
                )}
              </p>
            </div>
            {invoice.paid_at && (
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Paid Date</p>
                <p className="text-gray-900 dark:text-white font-medium">
                  {formatDateTime(invoice.paid_at)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Order Details (if available) */}
        {order && order.items && order.items.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Order Items
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      SKU
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Quantity
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Price
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Subtotal
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {order.items.map((item) => (
                    <tr key={item.id}>
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-white font-medium">
                        {item.sku}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-white text-right">
                        {item.qty}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-white text-right">
                        {formatCurrency(item.price)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-white text-right font-medium">
                        {formatCurrency(item.qty * item.price)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Actions */}
        {invoice.status === 'issued' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Actions
            </h2>
            <button
              onClick={() => setShowPaymentModal(true)}
              className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              Mark as Paid
            </button>
          </div>
        )}

        {/* Payment Confirmation Modal */}
        {showPaymentModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Confirm Payment
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Are you sure you want to mark this invoice as paid?
              </p>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-md p-4 mb-6">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Invoice ID:</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {invoice.id.substring(0, 16)}...
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Amount:</span>
                  <span className="text-lg font-bold text-gray-900 dark:text-white">
                    {formatCurrency(invoice.amount)}
                  </span>
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowPaymentModal(false)}
                  disabled={processing}
                  className="flex-1 px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  onClick={handleMarkAsPaid}
                  disabled={processing}
                  className="flex-1 px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {processing ? 'Processing...' : 'Confirm Payment'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
