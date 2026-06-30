# Device Security Requirements

**Owner:** IT Operations / Security
**Last updated:** 2026-02-05
**Applies to:** All company-issued devices

## Baseline requirements

Every Northwind-issued laptop (see Laptop Provisioning Process) must
have, at all times:

- Full-disk encryption enabled (FileVault on macOS, BitLocker on
  Windows) — this is configured automatically at provisioning and
  cannot be disabled by the user.
- Endpoint detection and monitoring agent installed and reporting.
- Auto-lock after 5 minutes of inactivity.
- OS security patches applied within 14 days of release; devices that
  fall out of compliance lose VPN access (see VPN Setup Guide) until
  patched.

## Multi-factor authentication

MFA is required for VPN access, the HR portal, and any Confidential or
Restricted classified system per Data Classification Policy. See
Password and MFA Policy for setup details.

## Personal devices (BYOD)

Personal devices may only access email and calendar, never the VPN,
customer data, or fleet management systems. See BYOD Policy for the
specific mobile device management enrollment required even for this
limited access.

## Working from public networks

Public WiFi (cafes, airports, etc.) is permitted, but NorthLink VPN must
be connected before accessing any internal system — see VPN Setup Guide.
The laptop's local firewall additionally blocks several classes of
inbound connection automatically on untrusted networks, no user action
required.

## Loss or compromise

If you suspect your device has been lost, stolen, or compromised, report
immediately per the process in Laptop Provisioning Process — the
remediation speed is the most important factor in limiting exposure.

## Related documents

- VPN Setup Guide
- Password and MFA Policy
- BYOD Policy
- Laptop Provisioning Process
- Data Classification Policy
