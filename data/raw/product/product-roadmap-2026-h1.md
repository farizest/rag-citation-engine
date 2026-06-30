# Product Roadmap 2026 H1

**Owner:** Product Management
**Last updated:** 2026-01-08
**Status:** Living document, updated monthly

## Themes for H1 2026

1. **Multi-warehouse intelligence** — features that let customers operate
   and reason about their robot fleet across multiple warehouse sites as
   a single system, rather than warehouse-by-warehouse.
2. **Predictive operations** — shifting from reactive maintenance and
   monitoring to predictive, using the telemetry data we've now collected
   over multiple years of fleet operation.
3. **Dashboard modernization** — a full rebuild of the customer-facing
   Fleet Dashboard, our most-used and most design-debt-laden surface.

## Major initiatives

### Fleet Dashboard v2
A ground-up rebuild of the customer dashboard, prioritizing real-time
fleet visibility and reducing the click-depth for common operator tasks.
See Feature Spec: Fleet Dashboard v2 for detailed requirements. Targeted
for release in the v3.5 release train.

### Predictive Maintenance
Uses telemetry history to flag robots likely to need maintenance before
a failure occurs, rather than relying purely on fixed maintenance
intervals. See Feature Spec: Predictive Maintenance. This is our most
technically ambitious H1 initiative and depends heavily on telemetry data
quality — see Telemetry Data Pipeline for the underlying data
infrastructure this builds on. Targeted for the v3.6 release train.

### Multi-Warehouse Routing
Allows task assignment and path planning to consider robot availability
across nearby warehouses, not just within a single site — relevant for
customers with multiple facilities in close proximity. See Feature Spec:
Multi-Warehouse Routing. This is a longer-term initiative; H1 scope is
limited to a pilot with two design partner customers.

## Explicitly out of scope for H1

- Outdoor/yard robot operation (currently indoor-only) — under
  exploration for H2 2026 at the earliest, no committed timeline yet.
- Customer-built custom integrations marketplace — discussed but not
  prioritized for 2026.

## Related documents

- Feature Spec: Fleet Dashboard v2
- Feature Spec: Predictive Maintenance
- Feature Spec: Multi-Warehouse Routing
- Release Notes (v3.4, v3.5, v3.6)
