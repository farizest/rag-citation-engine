# Postmortem: 2025 Warehouse Collision (Denver DC3)

**Severity:** SEV-1
**Date of incident:** 2025-11-08
**Author:** Incident Commander, Safety Engineering
**Status:** Closed, action items complete

## Summary

On 2025-11-08 at approximately 14:32 local time, robot unit DC3-R047
made contact with a warehouse employee in aisle 12 of the Denver DC3
facility. The employee sustained a minor bruise and did not require
medical treatment beyond first aid on site. No equipment damage occurred.
This document describes the timeline, root cause, and corrective actions.

## Timeline

- **14:31:58** — Employee enters aisle 12 from a cross-aisle not covered
  by the robot's planned route, walking parallel to the robot's direction
  of travel.
- **14:32:01** — Perception pipeline detects the employee but classifies
  them with 0.61 confidence as "person," which at the time was below the
  0.75 confidence threshold required to trigger the safety zone stop logic
  for ambiguous detections. The object was logged internally as
  "ambiguous — low confidence."
- **14:32:03** — Robot continues on planned path. Distance to employee
  closes to approximately 1.4 meters.
- **14:32:04** — Confidence score updates to 0.79 as the employee turns
  to face the robot, crossing the threshold. Safety stop is triggered.
- **14:32:04.3** — Robot begins emergency braking. Given the robot's
  speed (0.9 m/s) and braking distance, contact is not fully avoided.
- **14:32:04.6** — Light contact occurs between the robot's front bumper
  guard and the employee's leg.

## Root cause

The root cause was the 0.75 confidence threshold for treating a detection
as a person for safety-zone purposes. This threshold was originally tuned
to minimize false-positive stops (which were a customer complaint in
early deployments, as overly cautious stopping was hurting throughput).
That tuning did not adequately weight the asymmetry between the cost of a
false positive (minor throughput loss) and a false negative (potential
injury).

A contributing factor was the cross-aisle entry point in question not
being included in the robot's "high alert" zones, which would have
applied a stricter, lower confidence threshold regardless of the global
default.

## Corrective actions

1. **[Completed]** Lowered the global default confidence threshold for
   person classification from 0.75 to 0.55. See Perception Pipeline doc
   for current value.
2. **[Completed]** Reduced default robot speed in any aisle with
   uncontrolled cross-aisle entry points from 0.9 m/s to 0.5 m/s.
3. **[Completed]** Added all cross-aisle entry points across all
   facilities to the "high alert" zone configuration, which applies a
   0.40 confidence threshold and a wider safety buffer.
4. **[Completed]** Updated Robot Sensor Calibration Guide with a new
   section on cross-aisle zone tagging during facility onboarding.
5. **[In progress, owner: Perception team]** Evaluate whether a
   secondary, independent presence-sensing modality (e.g. low-cost
   passive infrared sensors at cross-aisle junctions) could provide a
   non-ML safety signal independent of the camera/LiDAR classifier.

## Lessons learned

This incident is the primary reference case any time someone proposes
raising a safety-related confidence threshold for throughput reasons.
The framing the Safety Engineering team now uses: any change to a safety
threshold requires an explicit, documented analysis of false-negative
cost, not just false-positive rate.

## Related documents

- Perception Pipeline
- Robot Sensor Calibration Guide
- Incident Response Process
