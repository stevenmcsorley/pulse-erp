# Grafana Dashboards Documentation

## Overview

Pulse ERP includes 3 pre-configured Grafana dashboards for real-time business intelligence:

1. **Sales & Revenue** - Sales trends, order volume, revenue tracking
2. **Inventory & Stock** - Stock levels, low stock alerts, reservation tracking
3. **Cashflow & AR** - Accounts receivable aging, overdue invoices, collections

All dashboards auto-refresh every 5 seconds and are mobile-responsive.

---

## Accessing Dashboards

**Grafana URL:** `http://localhost:3000`

**Default Credentials:**
- Username: `admin`
- Password: `admin` (change on first login)

**Dashboard Location:**
- Navigate to **Dashboards** → **Browse** → **ERP Analytics** folder

---

## Dashboard 1: Sales & Revenue

**UID:** `sales-revenue-001`

### Panels

#### Summary Stats (Top Row)
- **Total Revenue (24h)** - Sum of revenue in last 24 hours
- **Total Orders (24h)** - Count of orders in last 24 hours
- **Avg Order Value (24h)** - Average order value in last 24 hours

#### Charts
- **Revenue by Hour (7 days)** - Time series line chart showing hourly revenue trends
- **Orders by Hour (7 days)** - Time series line chart showing order volume trends
- **Daily Revenue (30 days)** - Bar chart showing daily revenue aggregates

### Data Source

- **OLAP Analytics** (JSON API)
- Endpoints:
  - `/query/sales/hourly?hours=24`
  - `/query/sales/hourly?hours=168`
  - `/query/orders/daily?days=30`

### Refresh Rate

5 seconds

### Use Cases

- Monitor daily sales performance
- Identify peak sales hours
- Track revenue trends
- Compare order volumes over time

---

## Dashboard 2: Inventory & Stock

**UID:** `inventory-stock-001`

### Panels

#### Summary Stats
- **Low Stock Alerts** - Count of SKUs needing reorder

#### Tables & Charts
- **Low Stock Items - Reorder Needed** - Table showing items below reorder point
  - Columns: SKU, Product, On Hand, Reserved, Available, Reorder Point
  - Color-coded Available column (red < 10, yellow 10-20, green > 20)
- **Top 20 Reserved SKUs** - Bar chart of most reserved products
- **Stock Movement Summary** - Table showing reservation history by SKU

### Data Source

- **OLAP Analytics** (JSON API)
- Endpoints:
  - `/query/inventory/low-stock`
  - `/query/inventory/movement?limit=20`
  - `/query/inventory/movement?limit=50`

### Refresh Rate

5 seconds

### Use Cases

- Identify items needing reorder
- Monitor stock levels in real-time
- Track which products are most in-demand
- Prevent stockouts

---

## Dashboard 3: Cashflow & AR

**UID:** `cashflow-ar-001`

### Panels

#### Summary Stats (Top Row)
- **Total AR Outstanding** - Sum of all overdue amounts
  - Thresholds: Green < $10k, Yellow $10k-$50k, Red > $50k
- **Overdue Customers** - Count of customers with overdue invoices
- **Oldest Overdue (days)** - Maximum days overdue

#### Visualizations
- **AR Aging Buckets** - Donut chart showing distribution
  - 30 days
  - 60 days
  - 90+ days
- **Overdue Accounts Receivable** - Table with color-coded days overdue
  - Columns: Customer, Total Outstanding, 30/60/90+ Days, Days Overdue
  - Gradient gauge for Days Overdue column

### Data Source

- **OLAP Analytics** (JSON API)
- Endpoints:
  - `/query/ar/overdue`

### Refresh Rate

5 seconds

### Use Cases

- Monitor collections targets
- Identify customers requiring follow-up
- Track AR aging trends
- Prioritize collection efforts

---

## Setup & Configuration

### Auto-Provisioning

Dashboards are automatically provisioned on Grafana startup via:

```yaml
# grafana/provisioning/dashboards.yml
providers:
  - name: 'Pulse ERP Dashboards'
    folder: 'ERP Analytics'
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
```

### Data Source Configuration

```yaml
# grafana/provisioning/datasources.yml
datasources:
  - name: OLAP Analytics
    type: marcusolsson-json-datasource
    url: http://olap-worker:8004
    isDefault: true
```

**Note:** Requires `marcusolsson-json-datasource` plugin. Install via:

```bash
docker exec -it pulse-grafana grafana-cli plugins install marcusolsson-json-datasource
docker restart pulse-grafana
```

---

## Customization

### Editing Dashboards

1. Open dashboard in Grafana
2. Click **Dashboard settings** (gear icon)
3. Make changes
4. Click **Save dashboard**
5. Export JSON via **Share** → **Export** → **Save to file**
6. Replace JSON file in `grafana/dashboards/`

### Adding New Panels

1. Click **Add panel** in dashboard edit mode
2. Select **OLAP Analytics** datasource
3. Configure query:
   - Method: GET
   - URL Path: `/query/sales/hourly`
   - Query Params: `hours=24`
4. Map JSON fields:
   - `$.data[*].hour` → time
   - `$.data[*].total_revenue` → Revenue
5. Choose visualization type
6. Save panel

### Custom Queries

Use predefined queries from OLAP API:
- `sales_24h`, `sales_7d`
- `low_stock`, `stock_movement`
- `overdue_ar`, `top_customers`
- `daily_orders`, `revenue_by_day`

See `/query/available` endpoint for full list.

---

## Performance

### Expected Load Times

- Panel data load: <500ms
- Full dashboard load: <2s
- Auto-refresh: Every 5s (configurable)

### Optimization Tips

1. **Limit data points** - Use query params (`limit`, `hours`, `days`)
2. **Increase refresh interval** - Change from 5s to 10s/30s for less active dashboards
3. **Cache datasource** - Enable caching in datasource settings

---

## Troubleshooting

### Dashboard Not Loading

**Problem:** Panels show "No data"

**Solutions:**
1. Check OLAP Worker is running: `docker ps | grep olap-worker`
2. Verify datasource: Settings → Data sources → OLAP Analytics → Test
3. Check API endpoint: `curl http://localhost:8004/query/sales/hourly?hours=24`

### Plugin Not Found

**Problem:** "Plugin not found: marcusolsson-json-datasource"

**Solution:**
```bash
docker exec -it pulse-grafana grafana-cli plugins install marcusolsson-json-datasource
docker restart pulse-grafana
```

### Slow Performance

**Problem:** Dashboards load slowly

**Solutions:**
1. Reduce refresh interval
2. Limit query results
3. Check DuckDB query performance: See `execution_time_ms` in API responses
4. Check Prometheus metrics for OLAP Worker

---

## Mobile Access

All dashboards are mobile-responsive:
- Panels stack vertically on small screens
- Tables scroll horizontally
- Touch-friendly controls

**Mobile URL:** Same as desktop (`http://localhost:3000`)

---

## Alerting (Future)

Planned for Sprint 2:
- [ ] Low stock alerts
- [ ] AR aging threshold alerts
- [ ] Daily revenue targets
- [ ] Email/Slack notifications

---

## Embedding in Frontend

Dashboards can be embedded in Next.js frontend:

```typescript
<iframe
  src="http://localhost:3000/d/sales-revenue-001?orgId=1&kiosk"
  width="100%"
  height="600"
  frameBorder="0"
/>
```

**Kiosk Mode Parameters:**
- `?kiosk` - Full kiosk (no UI)
- `?kiosk=tv` - TV mode (no controls, cycles dashboards)

---

## Backup & Export

### Export All Dashboards

```bash
# Via Grafana UI
Settings → Dashboards → Browse → Select dashboard → Share → Export → Save to file

# Via API
curl -u admin:admin http://localhost:3000/api/dashboards/uid/sales-revenue-001 | \
  jq '.dashboard' > sales-revenue-backup.json
```

### Import Dashboards

1. Dashboards → Import
2. Upload JSON file or paste JSON
3. Select data source: **OLAP Analytics**
4. Click **Import**

---

## Dashboard Tags

For easy filtering:
- `erp` - All ERP dashboards
- `sales`, `revenue` - Sales & Revenue dashboard
- `inventory`, `stock` - Inventory dashboard
- `cashflow`, `ar`, `finance` - Cashflow dashboard

---

## Variables & Templating

Currently not implemented. Future enhancements:
- Customer selector
- Date range picker
- Product category filter
- Warehouse filter

---

## Permissions

Default: All dashboards visible to all users

To restrict access:
1. Settings → Users & Teams
2. Create team (e.g., "Finance Team")
3. Dashboard settings → Permissions
4. Add team with View/Edit permissions

---

## Changelog

### Version 1.0 (2025-10-04)
- Initial dashboard creation
- 3 dashboards (Sales, Inventory, Cashflow)
- Auto-provisioning configured
- OLAP Analytics datasource integration

---

## Support

For issues or questions:
- Check API documentation: `/services/olap-worker/API.md`
- Check OLAP schema: `/services/olap-worker/migrations/README.md`
- Test queries directly: `http://localhost:8004/docs`
