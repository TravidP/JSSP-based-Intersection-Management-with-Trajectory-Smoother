# RL-Based JSSP Scheduler Training Plan

This document turns the paper-level scheduler design into a staged implementation and training plan. It focuses on the reinforcement-learning-based JSSP scheduler described in `sections/05_rl_jssp_scheduler.tex` and assumes the future graph-learning implementation will use PyTorch Geometric.

The repository is currently paper-first. The code folders under `src/aim_jssp/`, `configs/`, and `tests/` are scaffolding, not runnable software. The first implementation milestone should therefore be a small simulator-free scheduler that proves the operation graph, masks, rollout dynamics, and reward are correct before adding SUMO or trajectory smoothing.

## Scheduler Goal

At each scheduling event, the high-level controller receives active vehicles, route templates, and any fixed commitments. It builds an operation graph where each operation node means one vehicle traversing one conflict zone. The policy then constructs a complete schedule by repeatedly selecting exactly one schedulable operation.

The online deployment path should stay simple:

1. Build the current operation graph.
2. Mark already committed or executing operations as fixed.
3. Compute the schedulability mask.
4. Query the frozen policy for one operation.
5. Append the operation to the partial order.
6. Update masks and repeat until all remaining operations are scheduled.
7. Convert the selected order into target entry times and occupancy intervals.
8. Send the reservation set to the low-level smoother.

Online control should use frozen policy inference only. RL training happens offline.

## Stage 1: Abstract JSSP/AIM Training

Stage 1 is the first runnable target. It should not depend on SUMO, TraCI, CARLA, or a vehicle dynamics optimizer. The purpose is to make the graph scheduler correct, measurable, and trainable on generated instances.

### Synthetic Instance Generation

Generate small intersection scheduling instances from an abstract intersection tuple `I = (Z, T)`.

Start with:

- 3 to 8 conflict zones.
- 2 to 12 active vehicles.
- 1 to 4 operations per vehicle route.
- Route templates sampled from a fixed template table.
- Vehicle speeds sampled from a bounded range.
- Nominal free-flow entry times computed from distance and speed.
- Occupancy times sampled or computed from route geometry and vehicle class.
- Optional priority weights for emergency or high-priority vehicles.

The first training set should include small cases that are easy to inspect manually. Increase density only after graph construction, masks, and schedule generation have tests.

### Graph Construction

Represent each scene as a PyTorch Geometric graph with one node type, operation, and three typed relation groups:

- `pre`: predecessor context on the same vehicle route.
- `succ`: successor context on the same vehicle route.
- `disj`: same-conflict-zone competition.

Either a homogeneous `Data` object with relation-specific `edge_index` tensors or a `HeteroData` object with edge types can work. Prefer the structure that makes relation-specific message passing easiest to test. The first PyG implementation should expose named edge groups directly so tests can verify them without inspecting model internals.

Each operation node should contain:

- Scalar features: speed, distance to zone, nominal free-flow entry time, occupancy time, waiting time, incremental delay, route completion ratio, remaining-operation count.
- Binary flags: fixed or committed, currently schedulable.
- Categorical ids: operation status, conflict-zone id, vehicle type.

Continuous features should be normalized with statistics from generated training instances. Categorical fields should remain integer ids for learned embeddings inside the model.

### Rollout Dynamics

The environment state is the partial order plus graph state:

```text
S_l = (G_l, P_l, F)
```

where `P_l` is the selected partial operation order and `F` is the fixed or committed operation set.

At each rollout step:

1. Compute feasible actions: unscheduled operations whose route predecessors are already selected or fixed.
2. Apply the hard actor mask to invalid operations.
3. Sample one feasible operation during training.
4. Append the operation to the partial order.
5. Update operation status and schedulability flags.
6. Stop only when every remaining operation has been selected.

The environment must reject invalid actions during development. During model training, invalid actions should be impossible because logits for masked operations are set to negative infinity before softmax.

### Schedule Generation

After rollout creates an operation order, a deterministic schedule generator assigns times. The first version can use a simple earliest-feasible rule:

```text
start(operation) = max(
  nominal_free_flow_entry_time,
  previous_operation_finish_for_same_vehicle,
  previous_operation_finish_for_same_zone,
  fixed_commitment_time_if_any
)
finish(operation) = start(operation) + occupancy_time
```

The generated schedule must preserve route precedence and prevent same-zone overlap. This schedule is the source of delay reward and future smoother reservations.

### Reward Design

Use negative weighted incremental delay as the base reward:

```text
R_l = - sum_i w_i * DeltaD_i(l)
```

For Stage 1, keep the base reward focused on scheduling quality:

- Penalize additional delay relative to nominal free-flow crossing.
- Optionally normalize by number of vehicles or operations for stable training.
- Keep stop penalties and smoother infeasibility penalties out of the base reward until Stage 3 ablations.

Two reward variants should be logged during development:

- Step reward: incremental delay introduced by the selected action.
- Episode reward: total final delay after the full schedule is generated.

The first trained policy can use REINFORCE with a rollout baseline. PPO can be added later if variance or stability becomes a bottleneck.

### Model Design

Use a PyTorch Geometric relation-aware graph policy. The model should follow the paper design:

```text
x_tilde_v = concat(
  Norm(c_v),
  b_v,
  E_status(status_v),
  E_zone(zone_v),
  E_vehicle_type(type_v)
)
h_v_0 = phi_enc(x_tilde_v)
```

The encoder should then apply relation-aware message passing over `pre`, `succ`, and `disj` edges, plus a pooled global graph context broadcast back to nodes. A compact first model is enough:

- 3 relation-aware message-passing layers.
- 2 to 4 attention heads.
- Hidden size 64 or 128.
- Residual access to `h_v_0`.
- Masked actor head over operation nodes.
- Optional critic head for graph-level value estimation.

The first non-neural baseline should be implemented before training the neural model. Useful baselines are earliest nominal arrival, shortest occupancy time, and FCFS by first operation arrival.

### Logging

Log enough information to tell whether failure comes from graph construction, mask logic, training, or schedule generation:

- Episode reward and total delay.
- Average delay per vehicle.
- Makespan.
- Rollout length.
- Number of invalid-action attempts in debug mode.
- Mask size at each step.
- Same-zone overlap count after schedule generation.
- Route-precedence violation count.
- Policy entropy.
- Approximate inference time per graph.
- Random seed, instance size, route mix, model config, and git commit.

For the first runs, store small JSON or CSV summaries under a future ignored output folder such as `runs/`. Do not commit generated training logs by default.

### Acceptance Criteria

Stage 1 is complete when:

- The graph builder creates exactly one node per vehicle-zone operation.
- `pre`, `succ`, and `disj` relation groups are correct on inspected examples.
- The schedulability mask exposes only operations with satisfied predecessors.
- Rollout terminates with a complete operation order.
- The schedule generator produces no same-zone overlaps.
- Reward is zero or near zero for a no-delay free-flow case.
- Heuristic baselines and the learned policy can be evaluated on the same instance set.
- The learned policy improves over at least one simple heuristic on held-out synthetic instances, or the logs clearly show why it does not.

## Stage 2: SUMO Closed-Loop Validation

Stage 2 connects the abstract scheduler to traffic simulation while keeping the low-level smoother optional.

### SUMO Adapter Responsibilities

The SUMO adapter should extract:

- Vehicle id.
- Lane and route template.
- Position and distance to conflict zones.
- Speed and acceleration.
- Vehicle type.
- Arrival or entry time into the management region.
- Exit or completion status.

Scheduling events should be triggered when:

- A vehicle enters the management region.
- A vehicle leaves the intersection.
- A fixed commitment is completed.
- A vehicle violates tracking tolerance.
- A planned reservation becomes stale.

### Validation Protocol

Use the Stage 1 policy without online training first. If fine-tuning is later added, keep it offline or simulation-batch based so the online controller remains frozen during evaluation.

Compare against:

- FCFS stop-line controller.
- Earliest-arrival heuristic scheduler.
- Shortest-occupancy heuristic scheduler.
- JSSP scheduler without smoother.
- Full hierarchy once the smoother exists.

Metrics should include:

- Average delay.
- Throughput.
- Waiting time.
- Number of stops.
- Computation time per scheduling event.
- Schedule infeasibility or fallback count.
- Policy generalization across demand levels and route mixes.

Stage 2 is complete when the scheduler can repeatedly build valid operation graphs from SUMO state and produce feasible high-level reservations faster than the event loop requires.

## Stage 3: Smoother-Integrated Evaluation

Stage 3 connects the high-level reservations to the trajectory smoother described in the paper.

The scheduler output to the smoother should be a reservation set:

```text
(vehicle_id, zone_id, operation_rank, target_entry_time, occupancy_time)
```

The smoother should return:

- Predicted arrival times.
- Tracking errors.
- Feasibility status.
- Updated vehicle state.
- Fallback request when needed.

Reward ablations can then add:

- Penalty for smoother infeasibility.
- Penalty for unnecessary stops.
- Penalty for large tracking error.
- Energy or acceleration-variance proxy.

Do not add these penalties to the base Stage 1 reward until the scheduler-only behavior is understood. Otherwise model problems and smoother problems will be hard to separate.

Stage 3 is complete when the full hierarchy reports both scheduling quality and execution quality under repeated closed-loop simulation.

## Future Code Interfaces

These interfaces should be documented first and implemented incrementally. Names may change during coding, but the responsibilities should remain stable.

### `OperationNode`

Represents one traversal of one conflict zone by one vehicle.

Required fields:

- `vehicle_id`
- `operation_index`
- `zone_id`
- `status`
- `vehicle_type`
- `scalar_features`
- `binary_flags`
- `nominal_entry_time`
- `occupancy_time`

### `OperationGraph`

Stores one scheduling graph and its masks.

Required fields:

- `nodes`
- `edge_index_by_relation` for `pre`, `succ`, and `disj`
- `schedulability_mask`
- `fixed_mask`
- `vehicle_to_operations`
- `zone_to_operations`
- conversion helper to PyTorch Geometric data

### `SyntheticAIMEnv`

Simulator-free environment for Stage 1.

Required methods:

- `reset(seed=None)`
- `step(operation_id)`
- `schedulable_actions()`
- `is_terminal()`
- `compute_reward()`
- `current_graph()`

### `ScheduleGenerator`

Converts selected operation orders into time reservations.

Required methods:

- `generate(operation_order, fixed_commitments=None)`
- `validate_precedence(schedule)`
- `validate_same_zone_non_overlap(schedule)`
- `compute_delay(schedule)`

### `RelationAwareGATPolicy`

PyG-compatible masked actor model.

Required behavior:

- Encode scalar, binary, and categorical node features.
- Apply relation-aware message passing for `pre`, `succ`, and `disj`.
- Pool global graph context.
- Produce one logit per operation node.
- Apply the hard schedulability mask before sampling or greedy selection.
- Optionally produce a graph-level value estimate.

### `RolloutTrainer`

Offline training coordinator.

Required behavior:

- Sample synthetic instances.
- Roll out the policy until terminal schedules are produced.
- Store log probabilities, rewards, entropy, and masks.
- Compute returns or advantages.
- Update policy parameters.
- Evaluate against fixed heuristic baselines.
- Write reproducible run summaries.

## Recommended First Training Defaults

Use conservative settings for the first runnable version:

| Setting | Initial value |
| --- | --- |
| Vehicles per instance | 2 to 6 |
| Operations per route | 1 to 3 |
| Conflict zones | 3 to 5 |
| Hidden size | 64 |
| Message-passing layers | 3 |
| Attention heads | 2 |
| Training algorithm | REINFORCE with baseline |
| Batch size | 16 to 64 graphs |
| Evaluation seeds | At least 20 held-out seeds |
| Primary reward | Negative total delay |

Scale only after the implementation passes the graph, mask, schedule, and reward tests.
