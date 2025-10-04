import { test, expect } from '@playwright/test';

/**
 * Pulse ERP - E2E Smoke Test
 *
 * Validates the complete demo flow:
 * 1. Create product
 * 2. Verify inventory
 * 3. Create order
 * 4. Verify stock reservation
 * 5. Verify invoice auto-creation
 * 6. Mark invoice as paid
 * 7. Verify dashboards updated
 */

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8001';
const INVENTORY_API_URL = process.env.INVENTORY_API_URL || 'http://localhost:8002';
const OLAP_API_URL = process.env.OLAP_API_URL || 'http://localhost:8004';

// Generate unique test data
const timestamp = Date.now();
const TEST_SKU = `TEST-${timestamp}`;
const TEST_CUSTOMER = `TEST-CUSTOMER-${timestamp}`;

test.describe('Pulse ERP Demo Flow', () => {
  test('complete end-to-end demo flow', async ({ page, request }) => {
    // ========================================
    // Step 1: Create Product
    // ========================================
    test.step('Create product via UI', async () => {
      await page.goto('/inventory/products/new');
      await expect(page.locator('h1')).toContainText('Add New Product');

      // Fill product form
      await page.fill('input#sku', TEST_SKU);
      await page.fill('input#name', 'E2E Test Widget');
      await page.fill('input#price', '99.99');

      // Submit form
      await page.click('button[type="submit"]');

      // Should redirect to inventory list
      await expect(page).toHaveURL('/inventory', { timeout: 10000 });

      // Verify product appears in list
      await expect(page.locator('text=' + TEST_SKU)).toBeVisible();
    });

    // ========================================
    // Step 2: Set Initial Inventory
    // ========================================
    test.step('Set initial stock level', async () => {
      // Navigate to stock adjustment page
      await page.goto(`/inventory/stock/${TEST_SKU}`);
      await expect(page.locator('h1')).toContainText('Stock Adjustment');

      // Use quick action to add 100 units
      await page.click('button:has-text("+50")');
      await page.waitForTimeout(1000);
      await page.click('button:has-text("+50")');
      await page.waitForTimeout(1000);

      // Verify stock level via API
      const inventoryResponse = await request.get(`${INVENTORY_API_URL}/inventory/${TEST_SKU}`);
      expect(inventoryResponse.ok()).toBeTruthy();
      const inventory = await inventoryResponse.json();
      expect(inventory.qty_on_hand).toBeGreaterThanOrEqual(100);
    });

    // ========================================
    // Step 3: Create Order
    // ========================================
    let orderId: string;

    test.step('Create order via UI', async () => {
      await page.goto('/orders/new');
      await expect(page.locator('h1')).toContainText('Create New Order');

      // Fill customer ID
      await page.fill('input#customerId', TEST_CUSTOMER);

      // Select product from dropdown
      await page.selectOption('select', TEST_SKU);

      // Set quantity
      await page.fill('input[type="number"][min="1"]', '10');

      // Verify total calculation
      await expect(page.locator('text=999.90')).toBeVisible(); // 10 * 99.99

      // Submit order
      await page.click('button:has-text("Create Order")');

      // Should redirect to order detail
      await page.waitForURL(/\/orders\/[a-f0-9-]+/, { timeout: 10000 });

      // Extract order ID from URL
      const url = page.url();
      orderId = url.split('/orders/')[1];
      expect(orderId).toBeTruthy();

      // Verify order details
      await expect(page.locator('h1')).toContainText('Order Details');
      await expect(page.locator(`text=${TEST_CUSTOMER}`)).toBeVisible();
      await expect(page.locator('text=999.90')).toBeVisible();
    });

    // ========================================
    // Step 4: Place Order & Verify Stock Reservation
    // ========================================
    test.step('Place order and verify stock reservation', async () => {
      // Place order using action button
      await page.click('button:has-text("Place Order")');
      await page.waitForTimeout(2000); // Wait for status update

      // Verify status badge changed
      await expect(page.locator('text=placed')).toBeVisible();

      // Verify stock was reserved via API
      const inventoryResponse = await request.get(`${INVENTORY_API_URL}/inventory/${TEST_SKU}`);
      expect(inventoryResponse.ok()).toBeTruthy();
      const inventory = await inventoryResponse.json();
      expect(inventory.reserved_qty).toBeGreaterThanOrEqual(10);
    });

    // ========================================
    // Step 5: Verify Invoice Auto-Creation
    // ========================================
    let invoiceId: string;

    test.step('Verify invoice was auto-created', async () => {
      // Navigate to invoices list
      await page.goto('/invoices');
      await expect(page.locator('h1')).toContainText('Invoices');

      // Wait for invoice to appear (billing service processes async)
      await page.waitForTimeout(3000);
      await page.reload();

      // Find invoice with matching order ID
      const invoiceRow = page.locator(`a[href*="/orders/${orderId}"]`).first();
      await expect(invoiceRow).toBeVisible({ timeout: 10000 });

      // Get invoice ID
      const invoiceLink = await invoiceRow.locator('xpath=../..').locator('a[href*="/invoices/"]').first();
      const invoiceUrl = await invoiceLink.getAttribute('href');
      invoiceId = invoiceUrl!.split('/invoices/')[1];
      expect(invoiceId).toBeTruthy();

      // Navigate to invoice detail
      await invoiceLink.click();
      await expect(page).toHaveURL(`/invoices/${invoiceId}`);

      // Verify invoice details
      await expect(page.locator('text=999.90')).toBeVisible();
      await expect(page.locator('text=issued')).toBeVisible();
    });

    // ========================================
    // Step 6: Mark Invoice as Paid
    // ========================================
    test.step('Mark invoice as paid', async () => {
      // Click Mark as Paid button
      await page.click('button:has-text("Mark as Paid")');

      // Confirm in modal
      await expect(page.locator('text=Confirm Payment')).toBeVisible();
      await page.click('button:has-text("Confirm Payment")');

      // Wait for status update
      await page.waitForTimeout(2000);

      // Verify status changed to paid
      await expect(page.locator('text=Paid')).toBeVisible();
      await expect(page.locator('text=Paid Date')).toBeVisible();
    });

    // ========================================
    // Step 7: Verify Dashboards (OLAP Data)
    // ========================================
    test.step('Verify OLAP data updated', async () => {
      // Check sales data via OLAP API
      const salesResponse = await request.get(`${OLAP_API_URL}/sales/hourly?hours=1`);
      expect(salesResponse.ok()).toBeTruthy();
      const salesData = await salesResponse.json();
      expect(Array.isArray(salesData)).toBeTruthy();

      // Should have at least one entry
      expect(salesData.length).toBeGreaterThan(0);

      // Check inventory status
      const lowStockResponse = await request.get(`${OLAP_API_URL}/inventory/low-stock`);
      expect(lowStockResponse.ok()).toBeTruthy();
      const lowStock = await lowStockResponse.json();
      expect(Array.isArray(lowStock)).toBeTruthy();

      // Navigate to dashboards page
      await page.goto('/dashboards');
      await expect(page.locator('h1')).toContainText('Analytics Dashboards');

      // Verify dashboard cards are present
      await expect(page.locator('text=Sales Analytics')).toBeVisible();
      await expect(page.locator('text=Inventory Status')).toBeVisible();
      await expect(page.locator('text=Cashflow & AR')).toBeVisible();
    });

    // ========================================
    // Step 8: Summary Verification
    // ========================================
    test.step('Verify complete flow summary', async () => {
      // Check orders list
      await page.goto('/orders');
      await expect(page.locator(`text=${TEST_CUSTOMER}`)).toBeVisible();
      await expect(page.locator('text=placed')).toBeVisible();

      // Check inventory list
      await page.goto('/inventory');
      await expect(page.locator(`text=${TEST_SKU}`)).toBeVisible();

      // Check invoices list
      await page.goto('/invoices');
      await expect(page.locator('text=Paid')).toBeVisible();
    });
  });
});
