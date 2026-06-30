# System Architecture Overview

**Owner:** Platform Engineering
**Last updated:** 2026-02-14
**Status:** Living document

## Purpose

This document describes the high-level architecture of the Northwind Robotics fleet
management platform. It is the starting point for any new engineer trying to
understand how our services fit together. If you're onboarding onto the
Platform or Fleet teams, read this before anything else.

## High-level diagram (described)

The system is organized into four logical layers:

1. **Edge layer** — runs on each robot. Includes the perception pipeline, the
   path planning module, and a lightweight local controller that can operate
   autonomously for up to 90 seconds if connectivity to the cloud is lost.
2. **Cloud control layer** — the Fleet Controller Service, which is the
   brain of the operation. It tracks the state of every robot in every
   warehouse, assigns tasks, and resolves conflicts (e.g. two robots
   approaching the same aisle).
3. **Data layer** — the Telemetry Data Pipeline ingests sensor and state data
   from robots at roughly 4Hz per robot and writes it into our time-series
   store. The Fleet Management database (Postgres) holds the canonical state:
   robot inventory, warehouse maps, task history.
4. **API / integration layer** — the API Gateway is the single entry point
   for all external traffic, including the customer-facing Fleet Dashboard
   and third-party warehouse management system (WMS) integrations.

## Core services

| Service | Language | Owns |
|---|---|---|
| fleet-controller | Go | Robot state machine, task assignment |
| perception-pipeline | Python/C++ | Object detection, obstacle avoidance |
| path-planner | C++ | Route computation, collision avoidance |
| telemetry-pipeline | Go | Sensor data ingestion, time-series storage |
| api-gateway | Go | AuthN/Z, rate limiting, request routing |
| auth-service | Go | Identity, tokens, RBAC |

Each service has its own runbook — see the deployment runbook pages for
production and staging environments.

## Data flow for a typical task

1. A warehouse operator (or the WMS, via the API Gateway) creates a task,
   e.g. "move pallet from dock 3 to shelf B12."
2. The Fleet Controller Service receives the task, checks which robots are
   idle and nearby, and assigns it to one.
3. The assigned robot's local controller receives the task over our
   internal MQTT-based message bus (see Message Queue Architecture).
4. The path planner computes a route using the latest warehouse map and
   current positions of other robots.
5. As the robot executes the task, the perception pipeline continuously
   feeds obstacle data back to the local controller for real-time
   adjustments, while telemetry is streamed to the cloud for monitoring.
6. On completion, the Fleet Controller marks the task done and updates the
   Fleet Management database.

## Why we built it this way

Early versions of the platform (pre-2024) had robots talking directly to a
monolithic backend. This caused two recurring problems: a single noisy robot
could degrade API latency for the entire fleet, and any backend deployment
required careful coordination with robot firmware versions. The current
layered architecture decouples these concerns — see
`postmortem-2025-fleet-controller-outage` for the incident that finally
forced this decision.

## Related documents

- Fleet Controller Service (deep dive)
- Message Queue Architecture
- Telemetry Data Pipeline
- Deployment Runbook (Production)
- Database Schema: Fleet Management
