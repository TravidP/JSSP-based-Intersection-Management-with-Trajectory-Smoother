# Project Build Roadmap

This roadmap explains how to grow the current paper-first repository into a small, testable PyTorch Geometric implementation of the RL-based JSSP scheduler.

The key rule is to build from deterministic scheduling primitives outward. The project should prove graph construction, masks, schedule generation, and heuristic baselines before training a neural policy.

## Current Repository State

The repository currently contains:

- IEEE-style paper sources in `Hierarchical JSSP-Based Scheduling.tex` and `sections/`.
- Figures and reference material in `assets/`.
- Planning-only package folders in `src/aim_jssp/`.
- Planning-only `configs/` and `tests/` folders.

There is no Python package metadata, no runnable scheduler, no PyTorch Geometric model, and no executable training loop yet.

## Target Folder Organization

The future implementation should keep the current high-level layout and fill it in gradually:

```text
src/aim_jssp/
  graphs/
    schema.py              # OperationNode and OperationGraph data structures
    builder.py             # Active vehicle state to operation graph
    features.py            # Scalar normalization and categorical ids
    masks.py               # Fixed and schedulability masks
  env/
    synthetic.py           # Simulator-free JSSP/AIM environment
    schedule.py            # Operation order to target times
    reward.py              # Delay and later ablation rewards
    sumo_adapter.py        # Later TraCI/SUMO state extraction
  models/
    relation_gat.py        # PyG relation-aware GAT policy
    actor.py               # Masked operation actor head
    critic.py              # Optional graph-level value head
  training/
    rollout.py             # Complete schedule rollout
    trainer.py             # REINFORCE/PPO-style offline trainer
    evaluate.py            # Baselines and held-out evaluation
    logging.py             # Run summaries and metrics
configs/
  synthetic_small.yaml
  model_relation_gat.yaml
  train_reinforce_small.yaml
  eval_synthetic.yaml
tests/
  test_graph_builder.py
  test_masks.py
  test_schedule_generator.py
  test_reward.py
  test_rollout.py
  test_sumo_adapter.py
demos/
  rl_jssp_scheduler_demo.html
docs/
  rl_jssp_scheduler_training_plan.md
  project_build_roadmap.md
```

The files above are a target structure, not a requirement to create all code at once. Add code only when the related tests can be written at the same time.

## Implementation Milestones

### Milestone 0: Documentation And Static Demo

Status: this is the current docs-only deliverable.

Add:

- Training plan in `docs/rl_jssp_scheduler_training_plan.md`.
- Project roadmap in `docs/project_build_roadmap.md`.
- Static browser demo in `demos/rl_jssp_scheduler_demo.html`.
- Demo README in `demos/README.md`.
- README links to the new planning documents.

No Python package changes are needed for this milestone.

### Milestone 1: Python Package Foundation

Add the minimum package setup before scheduler code:

- `pyproject.toml` with Python, pytest, torch, torch-geometric, numpy, pandas, and optional SUMO extras.
- `src/aim_jssp/__init__.py` and package `__init__.py` files.
- A short developer setup section in `README.md`.
- A smoke test that imports `aim_jssp`.

Keep generated logs, checkpoints, and simulation outputs ignored by git.

### Milestone 2: Graph Schema And Builder

Implement `OperationNode` and `OperationGraph`, then build graphs from synthetic active-vehicle descriptions.

Acceptance criteria:

- One node exists for each vehicle-zone traversal.
- Same-vehicle precedence edges are complete.
- Reverse successor context is available to the model.
- Same-zone disjunctive edges connect all conflicting operations.
- Node features include scalar, binary, and categorical groups.
- Tests cover at least one hand-written intersection instance.

### Milestone 3: Masks And Schedule Generator

Implement fixed-operation masks, schedulability masks, and deterministic schedule generation.

Acceptance criteria:

- The mask exposes first unscheduled operations for each route.
- A successor becomes schedulable only after its predecessor is selected or fixed.
- Fixed commitments are never reordered.
- Generated schedules preserve route precedence.
- Generated schedules have no same-zone overlap.
- Delay is zero for a simple no-wait free-flow case.

### Milestone 4: Synthetic Environment

Implement `SyntheticAIMEnv` around the graph builder, masks, schedule generator, and reward.

Acceptance criteria:

- `reset()` returns a valid initial graph.
- `step()` accepts only schedulable operations.
- Rollout terminates after all remaining operations are selected.
- Invalid actions raise clear debug errors.
- Reward can be computed per step and per episode.

### Milestone 5: Heuristic Baselines

Add deterministic non-neural dispatch policies before adding RL.

Recommended baselines:

- FCFS by nominal first-zone arrival.
- Earliest nominal entry time.
- Shortest occupancy time.
- Random feasible operation with fixed seed.

Acceptance criteria:

- All baselines use the same environment and schedule generator.
- Evaluation reports delay, makespan, rollout length, and violation counts.
- Baseline results are reproducible by seed.

### Milestone 6: PyTorch Geometric Policy

Implement the first `RelationAwareGATPolicy`.

Acceptance criteria:

- The model consumes the graph representation from `OperationGraph`.
- Scalar, binary, and categorical features are encoded separately.
- Relation-aware message passing handles `pre`, `succ`, and `disj`.
- The actor returns one masked logit per operation node.
- Invalid operations cannot be sampled.
- A forward-pass test runs on a tiny graph.

### Milestone 7: Offline RL Training

Implement Stage 1 offline training.

Start with REINFORCE plus a moving-average or rollout baseline. Add a critic or PPO only after the simple trainer is correct.

Acceptance criteria:

- Training runs on generated synthetic instances.
- Evaluation runs on held-out seeds.
- Logs include reward, delay, policy entropy, mask size, and violation counts.
- The learned policy is compared against every heuristic baseline.

### Milestone 8: SUMO Adapter

Add TraCI/SUMO integration only after the abstract scheduler is stable.

Acceptance criteria:

- Active vehicles are converted into the same `OperationGraph` interface.
- Vehicle ids, routes, positions, speeds, and vehicle classes are preserved.
- Scheduling events are triggered by arrival, departure, tracking violation, or fallback request.
- The frozen Stage 1 policy can run in closed-loop validation.

### Milestone 9: Smoother Interface

Connect scheduler reservations to the low-level trajectory smoother.

Acceptance criteria:

- Scheduler outputs `(vehicle_id, zone_id, operation_rank, target_entry_time, occupancy_time)`.
- Smoother feedback includes predicted arrival, tracking error, feasibility, and fallback status.
- Infeasible smoothing can trigger replanning without reordering fixed commitments.
- Evaluation separates scheduler-only and smoother-integrated metrics.

## Configuration Plan

Add YAML configs only when the matching code exists. The first config set should include:

- `synthetic_small.yaml`: conflict zones, route templates, vehicle count range, speed range, occupancy range, random seeds.
- `model_relation_gat.yaml`: hidden size, layer count, attention heads, embedding dimensions, dropout.
- `train_reinforce_small.yaml`: batch size, learning rate, entropy weight, baseline type, training steps, evaluation interval.
- `eval_synthetic.yaml`: held-out seeds, instance sizes, baselines, metrics.

Configs should define experiment choices, not hide business logic. Route construction, mask rules, and reward formulas belong in code with tests.

## Testing Strategy

Tests should be added before or alongside each subsystem:

- Graph tests: node count, edge relations, relation labels.
- Mask tests: predecessor blocking, fixed commitments, terminal mask.
- Schedule tests: same-zone non-overlap, route precedence, fixed windows.
- Reward tests: no-delay case, delayed case, weighted priority case.
- Rollout tests: complete termination, invalid-action rejection.
- Model tests: forward pass, mask application, finite valid logits.
- Adapter tests: SUMO state preservation with mocked TraCI data.

No SUMO dependency should be required for Stage 1 tests.

## Development Defaults

Use these defaults unless experiments show a reason to change:

- Start with simulator-free synthetic instances.
- Keep online deployment frozen: no live RL updates during traffic control.
- Use PyTorch Geometric for relation-aware graph policy code.
- Use deterministic schedule generation after learned operation ordering.
- Keep base reward as negative delay until smoother-integrated ablations.
- Commit source, configs, tests, docs, and small demo assets only.
- Do not commit generated logs, checkpoints, compiled paper artifacts, or simulation outputs.
