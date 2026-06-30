# Fleet Controller Service

**Owner:** Platform Engineering (Fleet team)
**Last updated:** 2026-03-02
**Status:** Living document

## Overview

The Fleet Controller is the central state machine for every robot in the
Northwind fleet. If you only read one engineering doc this week after the
System Architecture Overview, read this one — it's the most-paged service
in the on-call rotation.

It is responsible for:

- Tracking the real-time state of every robot (idle, en route, charging,
  faulted, offline)
- Assigning tasks to robots based on proximity, battery level, and current
  load
- Detecting and resolving task conflicts (two robots assigned overlapping
  paths)
- Publishing state changes to the Telemetry Data Pipeline and the Fleet
  Dashboard

## Tech stack

Written in Go, using a custom in-memory state machine library
(`internal/fsm`) backed by Postgres for durability. It communicates with
robots over the internal MQTT message bus described in Message Queue
Architecture, and exposes a gRPC API consumed by the API Gateway.

## Scaling characteristics

As of Q1 2026, a single Fleet Controller instance handles up to 250 robots
comfortably. Above that, task assignment latency (the time between a task
being created and a robot being assigned) starts to climb past our 500ms
SLO. For warehouses with more than 250 robots, we shard by warehouse ID —
each warehouse gets its own Fleet Controller instance. This sharding
decision was made after the outage described in
`postmortem-2025-fleet-controller-outage`, where a single instance handling
three large warehouses simultaneously fell behind on task assignment during
a peak shift change.

## State machine

A robot can be in one of six states:

1. `IDLE` — available for task assignment
2. `ASSIGNED` — has received a task but not yet started moving
3. `EN_ROUTE` — actively executing a task
4. `CHARGING` — docked and charging, not available
5. `FAULTED` — reported an error condition, requires either auto-recovery
   or human intervention
6. `OFFLINE` — no heartbeat received in the last 15 seconds

Transitions are logged and form the basis of most incident investigations.
If you're debugging a "robot stuck" report, the first thing to check is the
state transition history for that robot, queryable via the internal
`fleetctl history <robot-id>` CLI tool.

## Common failure modes

- **Heartbeat flapping**: robots near the edge of warehouse WiFi coverage
  can oscillate between `EN_ROUTE` and `OFFLINE`. We added a 3-second grace
  period in v2.3 to reduce false offline transitions, configurable via the
  `HEARTBEAT_GRACE_MS` environment variable.
- **Task assignment thrashing**: under high load, the assignment algorithm
  can reassign a task multiple times before a robot actually starts moving.
  Mitigated by a 2-second assignment lock per task.
- **Stale map data**: if the warehouse map hasn't been refreshed after a
  layout change, the controller may assign physically impossible routes.
  Map refresh is currently a manual trigger — see the open ticket in the
  product roadmap for automating this.

## On-call notes

This service pages frequently. See On-Call Rotation Policy for scheduling
and Incident Response Process for what to do when paged. The most common
page is "task assignment latency high," which is almost always either a
sharding imbalance or a downstream Postgres slowdown — check the
`fleet_controller_assignment_latency_p99` dashboard first.

## Related documents

- System Architecture Overview
- Message Queue Architecture
- Postmortem: 2025 Fleet Controller Outage
- On-Call Rotation Policy
- Database Schema: Fleet Management
