# Perception Pipeline

**Owner:** Robotics Software (Perception team)
**Last updated:** 2026-01-20
**Status:** Living document

## Overview

The perception pipeline runs on-robot and is responsible for turning raw
sensor data (LiDAR, stereo cameras, ultrasonic proximity sensors) into a
structured understanding of the robot's surroundings: where obstacles are,
what they are (person, pallet, another robot, shelving), and how they're
moving.

This output feeds directly into the path planner, so latency here is
safety-critical. Our hard requirement is end-to-end perception latency
under 80ms at the 99th percentile.

## Pipeline stages

1. **Sensor fusion** — combines LiDAR point clouds with stereo camera
   depth maps into a unified 3D occupancy grid, refreshed at 20Hz.
2. **Object detection** — a quantized YOLO-family model (custom-trained on
   our warehouse dataset) runs on the occupancy grid plus raw camera frames
   to classify detected objects.
3. **Tracking** — a Kalman-filter-based tracker maintains object identity
   across frames, which is what lets us distinguish "person walking toward
   the robot" from "person walking away."
4. **Human safety zone check** — a dedicated, intentionally simple
   rule-based system (not ML) checks whether any tracked person has
   entered the robot's defined safety zone. If so, it issues an immediate
   stop signal that bypasses the rest of the pipeline. This is deliberately
   kept separate from the ML stack for auditability and certification
   reasons — see Robot Sensor Calibration Guide for the safety zone
   calibration procedure.

## Hardware notes

Each robot has:
- 1x mechanical LiDAR (360°, 15m range)
- 4x stereo camera pairs (front, back, left, right)
- 8x ultrasonic proximity sensors as a low-level redundant backup

The perception model runs on an onboard Jetson-class edge compute module.
See Edge Compute Deployment for provisioning and update details.

## Known limitations

- Performance degrades in low-light conditions below approximately 50 lux;
  warehouses operating night shifts need supplemental lighting in robot
  travel lanes.
- Highly reflective surfaces (plastic wrap on pallets, in particular) can
  produce false LiDAR returns. The fusion stage has a reflectivity filter,
  but it is not perfect.
- The object classifier has not been trained on every possible warehouse
  obstacle type; unrecognized objects are conservatively treated as
  static obstacles, which can cause robots to take unnecessarily cautious
  routes around novel objects.

## Incident history

The perception pipeline's classification confidence threshold was a
contributing factor in the incident covered in
`postmortem-2025-warehouse-collision`. Following that incident, the
default confidence threshold for treating a detection as "person" (rather
than "ambiguous object") was lowered from 0.75 to 0.55, trading some false
positives (robot slows for non-people) for a meaningful reduction in false
negatives.

## Related documents

- Robot Sensor Calibration Guide
- Path Planning Module
- Postmortem: 2025 Warehouse Collision
- Edge Compute Deployment
