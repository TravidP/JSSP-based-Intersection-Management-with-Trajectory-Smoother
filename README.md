# JSSP-Based Intersection Management With Trajectory Smoothing

This repository contains an IEEE-style paper draft and a planned software roadmap for a hierarchical autonomous intersection management framework. The method treats intersection scheduling as a job shop scheduling problem (JSSP), uses an offline-trained reinforcement-learning policy for online sequential rollout, and passes target conflict-zone times to a low-level trajectory smoother.

The repository currently prioritizes the paper and design plan. The `src/`, `configs/`, and `tests/` folders are lightweight scaffolding for future implementation; they are not yet runnable software.

## Paper Build

Build the paper with the existing pdfLaTeX workflow:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error "Hierarchical JSSP-Based Scheduling.tex"
bibtex "Hierarchical JSSP-Based Scheduling"
pdflatex -interaction=nonstopmode -halt-on-error "Hierarchical JSSP-Based Scheduling.tex"
pdflatex -interaction=nonstopmode -halt-on-error "Hierarchical JSSP-Based Scheduling.tex"
```

Main paper files:

- `Hierarchical JSSP-Based Scheduling.tex`: main IEEE manuscript.
- `sections/`: modular paper sections.
- `references.bib`: verified bibliography entries.
- `assets/figures/`: figures used by the draft.

Revision colors in the paper:

- Blue text marks the first revision round.
- Purple text marks the second revision round, including the operation graph and relation-aware GAT scheduler additions.

## Mathematical Formulation

The target intersection is represented as

```text
I = (Z, T)
```

where:

- `Z` is the set of conflict zones.
- `T` is the set of admissible route or trajectory templates.

Each active vehicle route is converted into ordered conflict-zone operations. The online scheduling state is represented as an operation graph

```text
G = (V_g, C union D)
```

where:

- `V_g` is the set of operation nodes. A node `v_{i,k}` means vehicle `i` traverses conflict zone `z_{i,k}`.
- `C` contains directed conjunctive edges for same-vehicle route precedence.
- `D` contains disjunctive same-zone conflict edges that must be resolved into a passing order.

The high-level scheduler performs sequential rollout: at each step, it selects one schedulable operation, updates the partial schedule, and repeats until all remaining operations of the current active vehicles are scheduled.

## Proposed Software Architecture

Planned modules:

```text
src/aim_jssp/
  graphs/      graph construction, feature extraction, and masks
  env/         abstract JSSP/AIM environment and SUMO adapters
  models/      relation-aware GAT policy and value networks
  training/    rollout training, evaluation loops, and logging
configs/       experiment and model configuration files
tests/         unit and integration tests
```

Core data flow:

1. Collect active vehicle states from synthetic scenarios or SUMO.
2. Convert each route into conflict-zone operations.
3. Build `G = (V_g, C union D)` with node features and relation-typed edges.
4. Apply the trained relation-aware GAT policy with schedulability masks.
5. Generate target entry times and occupancy intervals.
6. Send reservations to the low-level smoother.
7. If smoothing is infeasible, trigger replanning or fallback.

## Node Features

Each operation node should contain three compact feature groups:

| Group | Planned features |
| --- | --- |
| Operation identity and status | status `s_v`, conflict-zone id `z_v`, vehicle type `tau_v`; encoded with learned embeddings |
| Motion and timing state | continuous operation features `c_v`: current speed, distance to zone, nominal free-flow entry time, occupancy time, waiting time, incremental delay, route completion ratio, remaining-operation count |
| Scheduling context and masks | binary features `b_v`: fixed/committed flag and current schedulability flag; the schedulability flag is also a hard actor mask |

Use normalization for continuous features, learned embeddings for categorical fields, and explicit masks for fixed or unschedulable operations.

## Relation-Aware GAT Policy

Initial encoder:

```text
x_tilde_v = concat(
  Norm(c_v),
  b_v,
  E_status(s_v),
  E_zone(z_v),
  E_vehicle_type(tau_v)
)
h_v^(0) = phi_enc(x_tilde_v)
```

Here `c_v` contains normalized continuous operation features, `b_v` contains binary and mask features, and the remaining terms are learned embeddings for categorical variables. The actor also applies the schedulability mask as a hard mask by assigning `-inf` to invalid operation logits.

Relation types:

- `pre`: predecessor operations on the same vehicle route.
- `succ`: successor operations on the same vehicle route.
- `disj`: same-conflict-zone disjunctive conflict operations.
- `global`: pooled graph-level context, broadcast back to nodes.

Initial model design:

- 3 relation-aware message-passing layers.
- Multi-head attention per relation type.
- Residual access to `h_v^(0)` at every layer.
- Masked actor head over schedulable operations.
- Optional critic head or rollout baseline for policy-gradient training.

## RL Training Plan

Stage 1: abstract JSSP/AIM scheduler

- Generate synthetic intersections from `I = (Z, T)`.
- Sample active vehicle sets, route templates, speeds, and arrival times.
- Build operation graphs and masks.
- Train the policy to select operations until the schedule is complete.
- Reward: negative weighted incremental delay.

```text
R_t = - sum_i w_i * DeltaD_i(t)
```

Stage 2: SUMO closed-loop validation or fine-tuning

- Connect active vehicle state extraction through TraCI.
- Rebuild the graph when a vehicle enters, leaves, violates tolerance, or smoothing is infeasible.
- Compare against FCFS stop-line, heuristic scheduling, and scheduler-only baselines.

Stage 3: smoother-integrated evaluation

- Pass target entry times and occupancy intervals to the low-level smoother.
- Penalize infeasible smoothing and unnecessary stops in ablations.
- Report delay, throughput, number of stops, acceleration variance, energy proxy, and computation time.

## Development Milestones

1. Implement graph schema and synthetic graph generator.
2. Implement schedule generator for a completed operation order.
3. Implement abstract environment with mask validation.
4. Implement relation-aware GAT actor and optional critic.
5. Train on synthetic JSSP/AIM instances.
6. Add SUMO graph builder and closed-loop evaluation.
7. Add smoother interface and infeasibility feedback.
8. Add experiment scripts, configs, and reproducibility documentation.

## Testing Checklist

Planned tests:

- Graph builder creates one operation per vehicle-zone traversal.
- Route precedence edges are directed and complete.
- Same-zone disjunctive edges are present for all conflicting operations.
- Schedulability mask excludes operations with unscheduled predecessors.
- Rollout terminates only when all remaining operations are scheduled.
- Schedule generator produces non-overlapping same-zone occupancy intervals.
- Delay reward is zero for nominal free-flow travel and negative for additional delay.
- SUMO adapter preserves vehicle IDs, routes, positions, speeds, and vehicle types.

## Current Status

- Paper draft: active.
- RL implementation: planned.
- SUMO integration: planned.
- Low-level smoother implementation: planned.


