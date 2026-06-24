# Model Plan

This module will contain neural scheduler models.

Planned architecture:

```text
x_tilde_v = concat(Norm(c_v), b_v, E_status(s_v), E_zone(z_v), E_vehicle_type(tau_v))
h_v^(0) = phi_enc(x_tilde_v)
```

- Linear input encoder for continuous node features.
- Learned embeddings for operation status, conflict zone, and vehicle type.
- Relation-aware multi-head GAT layers for predecessor, successor, and disjunctive neighbors.
- Global graph context pooling.
- Masked actor head over schedulable operations.
- Optional critic or rollout baseline for training.

The first model target is a compact `K=3` relation-aware GAT suitable for online rollout.

