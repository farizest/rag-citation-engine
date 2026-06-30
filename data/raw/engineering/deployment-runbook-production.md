# Deployment Runbook (Production)

**Owner:** Platform Engineering
**Last updated:** 2026-02-10
**Status:** Living document

## Pre-deployment checklist

1. Confirm the change has passed CI, including the RAG-style evaluation
   gates if touching any ML-adjacent service — see CI/CD Pipeline
   Overview for what's gated.
2. Confirm there is no active SEV-1/SEV-2 incident — check `#incidents`.
3. Confirm deployment window: production deploys are restricted to
   Tuesday-Thursday, 9am-3pm local time for the deploying engineer's
   region, to ensure adequate team coverage if something goes wrong.
   Exceptions require an SRE lead approval.
4. For any change touching the Fleet Controller, Path Planner, or
   Perception Pipeline (safety-adjacent services), a second engineer must
   review and approve the deployment plan, not just the code — this is in
   addition to standard code review under Code Review Guidelines.

## Deployment steps

1. Deploy to staging first using the same artifact that will go to
   production — see Deployment Runbook (Staging).
2. Run the smoke test suite against staging.
3. Deploy to production using a canary rollout: 5% of traffic for 15
   minutes, then 25%, 50%, 100%, with automated rollback if error rates
   or latency exceed thresholds at any stage.
4. Monitor the relevant service dashboard for at least 30 minutes after
   reaching 100%.

## Rollback

Any engineer can trigger an immediate rollback via the deployment tool
without needing approval — speed matters more than process here. A
rollback should be followed by a `#incidents` post if it was triggered by
a real production issue (not just an abundance of caution), so the
on-call rotation has visibility per Incident Response Process.

## Robot firmware deployments

Firmware deployments to physical robots follow a separate, slower process
described in Robot Firmware Update Process — they are not covered by
this runbook, since rolling firmware back in the field is significantly
harder than rolling back a cloud service.

## Related documents

- Deployment Runbook (Staging)
- CI/CD Pipeline Overview
- Incident Response Process
- Code Review Guidelines
- Robot Firmware Update Process
