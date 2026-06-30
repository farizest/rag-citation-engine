# On-Call Rotation Policy

**Owner:** Platform Engineering
**Last updated:** 2025-12-10
**Status:** Living document

## Who is on-call

Engineering on-call is split into two rotations:

- **Platform rotation**: covers Fleet Controller, API Gateway, Auth
  Service, Telemetry Pipeline. Pulled from Platform Engineering, 6
  engineers, one week shifts.
- **Robotics rotation**: covers Perception Pipeline, Path Planner, and
  on-robot firmware issues. Pulled from Robotics Software, 5 engineers,
  one week shifts.

Both rotations are primary/secondary: the secondary is paged automatically
if the primary doesn't acknowledge within 5 minutes.

## Expectations

- Primary on-call must be reachable and able to begin investigating within
  5 minutes of a page, for both rotations.
- On-call engineers are expected to have a working VPN connection and
  laptop access at all times during their shift — see VPN Setup Guide.
- Shift handoff happens every Monday at 10:00 local time via a short
  written handoff note in `#platform-oncall` or `#robotics-oncall`
  summarizing any ongoing issues, recent changes, and anything the
  incoming on-call should watch.

## Compensation

On-call engineers receive on-call pay per the Compensation Bands Overview
document, plus the ability to take a half-day off in the week following a
shift that included a SEV-1 page outside business hours.

## Escalation

If an incident requires expertise outside the on-call engineer's area
(e.g. a Platform on-call needs Perception team input), use the
`@robotics-escalation` Slack group, which pages the Robotics secondary
on-call regardless of whether it's technically their rotation's issue.

## Related documents

- Incident Response Process
- Fleet Controller Service
- Compensation Bands Overview
