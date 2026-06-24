# RL JSSP Scheduler Demo

This folder contains a static concept demo for the reinforcement-learning-based JSSP scheduler.

Open `rl_jssp_scheduler_demo.html` directly in a browser. It has no backend, package install, build step, or external JavaScript dependency.

The demo illustrates:

- Operation nodes for vehicle-zone traversals.
- Same-vehicle precedence edges.
- Same-zone disjunctive conflict edges.
- Current schedulability mask.
- Sequential operation rollout.
- Generated reservation times.

The demo does not train a policy, run SUMO, solve vehicle dynamics, or replace the future Python implementation. It is a small visual reference for the planned scheduler data flow.

Related planning documents:

- [RL scheduler training plan](../docs/rl_jssp_scheduler_training_plan.md)
- [Project build roadmap](../docs/project_build_roadmap.md)
