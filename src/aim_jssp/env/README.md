# Environment Plan

This module will define abstract scheduling environments and simulator adapters.

Planned responsibilities:

- Generate synthetic JSSP/AIM instances from `I = (Z, T)`.
- Step the partial schedule after each selected operation.
- Compute delay reward and schedule feasibility.
- Provide a SUMO/TraCI adapter for active vehicle state extraction.
- Trigger replanning events from arrivals, departures, tracking violations, or smoother infeasibility.

The first implementation should start with a simulator-free abstract environment before SUMO integration.
