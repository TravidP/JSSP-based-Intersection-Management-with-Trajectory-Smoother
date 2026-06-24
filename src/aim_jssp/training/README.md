# Training Plan

This module will contain training and evaluation loops.

Planned responsibilities:

- Roll out complete schedules from masked policy decisions.
- Compute negative weighted incremental delay reward.
- Log feasibility, mask validity, rollout length, delay, stop count, and infeasibility events.
- Train first on synthetic graph instances.
- Add SUMO closed-loop validation after abstract training is stable.
- Add smoother-integrated penalties in later ablations.

Training should keep deployment separate: online deployment uses frozen policy inference only.
