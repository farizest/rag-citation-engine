# Incident Response Process

**Owner:** Platform Engineering
**Last updated:** 2026-01-05
**Status:** Living document

## Severity levels

- **SEV-1**: Customer-facing outage, safety incident, or data loss.
  Requires immediate response, incident commander assigned within 5
  minutes of detection.
- **SEV-2**: Significant degradation affecting a subset of customers or
  warehouses, no safety impact. Response within 30 minutes.
- **SEV-3**: Minor degradation, workaround available. Response within
  business hours.

## Roles

- **Incident Commander (IC)**: coordinates the response, makes the final
  call on mitigation actions, and owns communication. The IC does not
  necessarily do the hands-on debugging.
- **On-call engineer**: the first responder, typically becomes IC for
  SEV-2/3 incidents unless escalated. See On-Call Rotation Policy for
  scheduling.
- **Scribe**: maintains the incident timeline in real time. For SEV-1
  incidents, the IC should assign a scribe rather than doing this
  themselves.

## Process

1. **Detection** — via paging alert, customer report, or internal report.
2. **Triage** — on-call engineer assesses severity within the SLAs above.
3. **Declare** — for SEV-1/2, post in `#incidents` with severity, impact
   summary, and IC assignment. This starts the official incident clock.
4. **Mitigate** — focus on stopping customer/safety impact first;
   root-causing can come after mitigation. It is acceptable and often
   correct to apply a blunt mitigation (e.g. rollback, traffic throttle)
   before fully understanding the root cause.
5. **Resolve** — once impact has stopped, declare the incident resolved
   in `#incidents`.
6. **Postmortem** — required for all SEV-1 and SEV-2 incidents within 5
   business days. SEV-3 postmortems are optional but encouraged for
   recurring issues. Postmortems are blameless: the goal is process and
   system improvement, not individual accountability. See the postmortem
   template linked in `#incidents` channel topic.

## Safety incidents — special handling

Any incident involving physical contact between a robot and a person,
regardless of injury severity, is automatically classified SEV-1 and
additionally triggers the Safety Engineering escalation path. This is
separate from and in addition to the standard severity assessment above.
Safety incidents require a postmortem within 2 business days, not 5, and
require sign-off from the Safety Engineering lead before the postmortem
is considered closed. See `postmortem-2025-warehouse-collision` for an
example of this process.

## Related documents

- On-Call Rotation Policy
- Postmortem: 2025 Fleet Controller Outage
- Postmortem: 2025 Warehouse Collision
- Deployment Runbook (Production)
