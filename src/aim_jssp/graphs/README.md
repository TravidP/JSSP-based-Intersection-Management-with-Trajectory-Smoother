# Graph Construction Plan

This module will convert active vehicle states and route templates into operation graphs.

Planned responsibilities:

- Build operation nodes `v_{i,k}` for vehicle-zone traversals.
- Add conjunctive route-precedence edges.
- Add disjunctive same-conflict-zone edges.
- Compute node features and relation-specific neighborhoods.
- Produce fixed-operation and schedulability masks.

Initial tests should validate graph size, edge direction, edge relation labels, and mask correctness.
