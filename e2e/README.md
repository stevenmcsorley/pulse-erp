# Pulse ERP - E2E Tests

End-to-end tests for Pulse ERP using Playwright.

## Overview

This test suite validates the complete demo flow:

1. ✅ **Create Product** - Add new product via UI
2. ✅ **Set Initial Stock** - Adjust inventory levels
3. ✅ **Create Order** - Create order with line items
4. ✅ **Place Order** - Change status from draft to placed
5. ✅ **Verify Stock Reservation** - Check inventory API for reserved qty
6. ✅ **Verify Invoice Auto-Creation** - Confirm billing service created invoice
7. ✅ **Mark Invoice as Paid** - Process payment via UI
8. ✅ **Verify OLAP Data** - Check analytics APIs and dashboards

## Prerequisites

**Services must be running:**

```bash
# Start full stack
docker-compose \
  -f docker-compose.base.yml \
  -f docker-compose.services.yml \
  -f docker-compose.bi.yml \
  -f docker-compose.erp.yml \
  up -d

# Or just frontend if backend already running
cd frontend && npm run dev
```

**Install dependencies:**

```bash
cd e2e
npm install
npx playwright install --with-deps chromium
```

## Running Tests

### Headless (CI mode)

```bash
npm test
```

### Headed (see browser)

```bash
npm run test:headed
```

### Debug mode

```bash
npm run test:debug
```

### UI mode (interactive)

```bash
npm run test:ui
```

### View test report

```bash
npm run report
```

## Environment Variables

Configure API endpoints if running on non-default ports:

```bash
export BASE_URL=http://localhost:3001
export API_BASE_URL=http://localhost:8001
export INVENTORY_API_URL=http://localhost:8002
export OLAP_API_URL=http://localhost:8004

npm test
```

## Test Structure

```
e2e/
├── tests/
│   └── demo-flow.spec.ts       # Main E2E test
├── playwright.config.ts        # Playwright configuration
├── package.json                # Dependencies
└── README.md                   # This file
```

## Test Breakdown

### demo-flow.spec.ts

**Duration:** ~2-3 minutes

**Steps:**

1. **Create Product** (15s)
   - Navigate to `/inventory/products/new`
   - Fill form (SKU, name, price)
   - Submit and verify redirect

2. **Set Initial Stock** (10s)
   - Navigate to stock adjustment page
   - Use quick actions (+50 twice)
   - Verify via API call

3. **Create Order** (20s)
   - Navigate to `/orders/new`
   - Fill customer ID
   - Select product from dropdown
   - Set quantity
   - Verify total calculation
   - Submit and verify redirect

4. **Place Order** (15s)
   - Click "Place Order" button
   - Verify status badge changes
   - Verify stock reservation via API

5. **Verify Invoice** (20s)
   - Navigate to invoices list
   - Wait for async invoice creation
   - Find invoice by order ID
   - Navigate to invoice detail
   - Verify amount and status

6. **Mark as Paid** (15s)
   - Click "Mark as Paid"
   - Confirm in modal
   - Verify status changes to "Paid"

7. **Verify OLAP Data** (15s)
   - Query OLAP API endpoints
   - Navigate to dashboards
   - Verify dashboard cards visible

8. **Summary Verification** (10s)
   - Check orders list
   - Check inventory list
   - Check invoices list

## CI Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Start services
        run: |
          docker-compose -f docker-compose.base.yml up -d
          docker-compose -f docker-compose.services.yml up -d

      - name: Install dependencies
        working-directory: e2e
        run: |
          npm ci
          npx playwright install --with-deps chromium

      - name: Run E2E tests
        working-directory: e2e
        run: npm test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: e2e/playwright-report/
```

## Troubleshooting

### Tests fail with timeout

**Issue:** Services not ready

**Solution:**
```bash
# Check service health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:3001/

# Restart services
docker-compose restart
```

### Product creation fails

**Issue:** Database constraints

**Solution:**
```bash
# Check if product already exists
curl http://localhost:8002/products

# Run migrations
./scripts/migrate.sh
```

### Invoice not found

**Issue:** Async processing delay

**Solution:** Test includes 3-second wait and reload. If still failing, increase timeout in test.

### Screenshots/videos not captured

**Issue:** Playwright reporter config

**Solution:** Check `playwright.config.ts`:
```typescript
use: {
  screenshot: 'only-on-failure',
  video: 'retain-on-failure',
}
```

## Best Practices

1. **Unique test data** - Use timestamps to avoid conflicts
2. **Explicit waits** - Wait for elements, not timeouts
3. **API verification** - Don't rely solely on UI
4. **Cleanup** - Tests should be idempotent
5. **Screenshots** - Auto-captured on failure
6. **Sequential execution** - One worker for demo flow

## Future Enhancements

- [ ] Add API-only tests for faster execution
- [ ] Add visual regression tests
- [ ] Add load testing with k6
- [ ] Add mobile viewport tests
- [ ] Add accessibility tests
- [ ] Add performance budgets
