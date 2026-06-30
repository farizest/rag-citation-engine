# API Gateway Design

**Owner:** Platform Engineering
**Last updated:** 2026-01-18
**Status:** Living document

## Purpose

The API Gateway is the single entry point for all external traffic into
Northwind's systems: the customer-facing Fleet Dashboard, third-party WMS
integrations, and partner API consumers. It does not contain business
logic itself — it routes, authenticates, and rate-limits, then delegates
to backend services like the Fleet Controller.

## Responsibilities

- **AuthN/Z**: validates tokens issued by the Auth Service on every
  request, before routing. See Auth Service Spec for token format and
  validation details.
- **Rate limiting**: enforces per-customer rate limits — see API Rate
  Limiting Policy for current tiers and limits.
- **Routing**: maps external API paths to internal service endpoints,
  including version routing (e.g. `/v2/tasks` routes differently than
  `/v1/tasks` for backward compatibility with older WMS integrations).
- **Request/response logging**: all requests are logged for debugging
  and billing purposes, with sensitive fields redacted per Data
  Classification Policy.

## Why a separate gateway layer

Before the gateway existed (pre-2024), each backend service implemented
its own auth and rate limiting independently, which led to inconsistent
behavior between services and made it hard to reason about what a given
API key could actually access. Centralizing this in the gateway means
backend services like the Fleet Controller can trust that any request
reaching them has already been authenticated and rate-limited correctly.

## Versioning policy

We support the current major API version plus one prior version
(currently v2 and v1) for external integrations. Deprecating v1 requires
6 months advance notice to integration partners — see Feature
Deprecation Policy for the general deprecation process this follows.

## Related documents

- Auth Service Spec
- API Rate Limiting Policy
- System Architecture Overview
- Feature Deprecation Policy
