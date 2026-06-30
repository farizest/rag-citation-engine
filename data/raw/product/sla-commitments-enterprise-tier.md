# SLA Commitments: Enterprise Tier

**Owner:** Product Management / Customer Success
**Last updated:** 2025-12-15
**Applies to:** Customers on the Enterprise pricing tier only

## Uptime commitment

Northwind commits to 99.9% uptime for the Fleet Dashboard and core task
assignment API for Enterprise tier customers, measured monthly. This
excludes scheduled maintenance windows (announced at least 72 hours in
advance) and does not cover on-robot/edge system availability, which is
governed by a separate hardware warranty agreement, not this SLA.

## Response time commitments

| Severity | Definition | Response time |
|---|---|---|
| Critical | Fleet-wide outage or safety-related issue | 15 minutes, 24/7 |
| High | Significant degradation, single warehouse | 1 hour, 24/7 |
| Medium | Limited functionality impact | 4 business hours |
| Low | Cosmetic or minor issue | 2 business days |

These response time commitments mirror our internal Incident Response
Process severity framework, though the external SLA tiers and internal
SEV levels are not a strict one-to-one mapping — Customer Success
maintains the translation table.

## Credits for missed SLA

If monthly uptime falls below 99.9%, the customer is eligible for a
service credit on a sliding scale, detailed in the master service
agreement (legal document, not duplicated here). Customer Success is
responsible for proactively identifying and applying credits — customers
should not have to request them, though they can also raise a claim if
they believe a credit was missed.

## What's not covered

- Customer-side network issues (the SLA covers Northwind systems only)
- Issues caused by unsupported third-party WMS integrations
- Force majeure events

## Related documents

- Customer Onboarding Playbook
- Incident Response Process
- Pricing and Packaging Overview
