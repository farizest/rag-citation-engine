# VPN Setup Guide

**Owner:** IT Operations
**Last updated:** 2026-02-20
**Applies to:** All employees accessing internal systems remotely

## Overview

Northwind uses a WireGuard-based VPN (internally called "NorthLink") for
all remote access to internal systems, including the Fleet Management
database, internal wiki edit access, and any customer data. You must be
connected to NorthLink any time you're working from outside a Northwind
office, per the Remote Work Policy and Device Security Requirements.

## Initial setup

1. Install the NorthLink client from the internal software portal (see
   Software License Request if it's not already available to you — it
   should be pre-installed on all IT-provisioned laptops, see Laptop
   Provisioning Process).
2. Authenticate with your Northwind SSO credentials. You'll be prompted
   for multi-factor authentication — see Password and MFA Policy if you
   haven't set this up yet.
3. Once authenticated, the client automatically pulls your device
   certificate, valid for 180 days. You'll be prompted to renew before
   expiration; renewal is automatic if you're connected to the internet
   at the time.

## Connecting

NorthLink auto-connects on device boot if you're on a trusted home or
public network and have previously authenticated. On a fully new network,
you may need to manually approve the connection the first time, as a
security measure against connecting through unrecognized networks
without awareness.

## Split tunneling

NorthLink uses split tunneling: only traffic destined for internal
Northwind systems (`*.internal.northwindrobotics.com`, the VPN-gated
admin tools, and the fleet telemetry endpoints) is routed through the
VPN. General internet browsing is not routed through NorthLink, which
keeps performance impact minimal for day-to-day work.

## Troubleshooting

- **Can't connect**: most common cause is an expired device certificate;
  try signing out and back in to force a refresh.
- **Connected but can't reach internal tools**: check whether the
  specific tool requires an additional access grant beyond base VPN
  connectivity — many internal tools have their own RBAC layer on top of
  network access. See Access Request Process.
- **Slow performance**: if you're on a particularly congested public
  WiFi, try switching to your phone's hotspot temporarily; this is the
  most common fix reported to the helpdesk.

If none of the above resolves your issue, file a ticket — see IT
Helpdesk SLA for expected response times.

## Related documents

- Remote Work Policy
- Device Security Requirements
- Password and MFA Policy
- Access Request Process
