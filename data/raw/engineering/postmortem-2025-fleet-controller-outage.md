# Postmortem: 2025 Fleet Controller Outage

**Severity:** SEV-1
**Date of incident:** 2025-08-19
**Author:** Incident Commander, Platform Engineering
**Status:** Closed, action items complete

## Summary

On 2025-08-19 between 09:14 and 10:02 local time, the Fleet Controller
instance serving three Phoenix-area warehouses experienced severe task
assignment latency degradation, peaking at 14.2 seconds p99 (against an
SLO of 500ms). This caused visible slowdowns in robot task pickup across
all three sites during the morning shift change, the highest-traffic
period of the day. No safety incidents occurred; the impact was purely
operational throughput.

## Timeline

- **09:14** — Shift change begins across all three Phoenix warehouses
  simultaneously. Task creation rate spikes roughly 6x above baseline as
  overnight backlogs are released into the system.
- **09:17** — `fleet_controller_assignment_latency_p99` dashboard crosses
  the 2s warning threshold. No page is fired yet (the alert threshold was
  set at 5s).
- **09:21** — Latency crosses 5s, on-call engineer paged.
- **09:26** — On-call engineer begins investigation, initially suspects a
  Postgres issue based on elevated query times.
- **09:38** — Postgres is ruled out as primary cause; query times are
  elevated but not enough to explain the full latency.
- **09:51** — Root cause identified: a single Fleet Controller instance
  was handling task assignment for all three warehouses, and the
  assignment algorithm's conflict-resolution step has roughly O(n²)
  behavior in the number of concurrently pending tasks. With three
  warehouses' shift-change backlogs combined into one instance, pending
  task count was over 4x what any single warehouse normally produces.
- **09:55** — Mitigation applied: task creation rate is temporarily
  throttled at the API Gateway to bring pending count back under control.
- **10:02** — Latency returns to baseline. Incident resolved.

## Root cause

The Fleet Controller was architected as a single shared instance handling
multiple warehouses, with a task assignment algorithm whose
conflict-resolution step scales poorly with pending task count. This had
not surfaced in testing because load tests were conducted per-warehouse,
never simulating multiple warehouses' shift-change spikes hitting the
same instance concurrently.

## Corrective actions

1. **[Completed]** Sharded the Fleet Controller by warehouse ID — each
   warehouse now gets a dedicated instance. See Fleet Controller Service
   doc for current architecture.
2. **[Completed]** Rewrote the conflict-resolution step to use a spatial
   index, bringing complexity down from roughly O(n²) to O(n log n).
3. **[Completed]** Updated Load Testing Guidelines to require multi-site
   concurrent shift-change simulation as a standard test scenario.
4. **[Completed]** Lowered the assignment latency alert threshold from 5s
   to 2s, with the warning threshold lowered from 2s to 800ms, to catch
   degradation earlier.
5. **[Completed]** Added a per-instance pending task count circuit
   breaker that automatically throttles new task creation if pending
   count exceeds a safe threshold, rather than relying on manual
   throttling as was done during this incident.

## Lessons learned

Single-instance services that are expected to scale should be load
tested against realistic worst-case concurrent demand, not just steady
state or single-tenant peak. This incident directly motivated the
sharding decision now described as the default architecture in the
System Architecture Overview.

## Related documents

- Fleet Controller Service
- System Architecture Overview
- Incident Response Process
- Load Testing Guidelines
