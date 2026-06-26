# Literature Search Protocol: Trajectory Smoothing And Avoidance

Date created: 2026-06-26

## Objective

Identify and screen recent literature on trajectory smoothing, stop avoidance, and
collision avoidance for autonomous/connected automated vehicle intersection
management. The review supports the manuscript section
`Trajectory Smoothing and Stop Avoidance` and the proposed hierarchy in which a
JSSP/RL scheduler generates conflict-zone reservations and a low-level smoother
checks executable safe trajectories.

## Core Window

The 15 core papers are limited to work dated from **2021-06-26** through
**2026-06-26**. Older foundational work may be cited only as background when it
is necessary to explain reservation-based AIM, energy-optimal control, or CBF
theory.

## Search Keywords

- Autonomous intersection management: `autonomous intersection management`,
  `connected automated vehicles`, `CAV`, `signal-free intersection`,
  `unsignalized intersection`
- Trajectory smoothing: `trajectory smoothing`, `velocity planning`,
  `speed planning`, `eco-driving`, `optimal control`, `MPC`
- Stop avoidance: `stop avoidance`, `stop-line waiting`, `no-stop crossing`,
  `energy consumption`, `delay reduction`
- Safety: `collision avoidance`, `control barrier function`, `safety constraint`,
  `mixed traffic`, `motion uncertainty`
- Scheduling and learning: `reinforcement learning`, `graph reinforcement
  learning`, `job shop scheduling`, `resequencing`, `passing order`

## Databases And Source Rules

Use primary or traceable sources: arXiv pages, DOI landing pages, IEEE Xplore
metadata, ScienceDirect/Elsevier pages, Springer pages, MDPI pages, Crossref,
OpenAlex, Semantic Scholar, and publisher or author-hosted open PDFs. Download
only legal open-access PDFs. If a strong paper is paywalled or lacks an official
open PDF, keep its metadata and mark the PDF status as closed/no official open
PDF found.

## Inclusion Rules

- The paper must address intersections, CAVs/AVs, or cooperative vehicle
  management near intersections.
- It must contribute to at least one of: smooth speed/trajectory optimization,
  stop/delay/energy reduction, collision/safety constraints, schedule/order
  selection, replanning, or learning-based AIM.
- It must help explain the manuscript gap: high-level ordering is not enough
  unless the resulting reservations can be converted into safe, smooth vehicle
  motion.

## Exclusion Rules

- Pure traffic-signal optimization without vehicle trajectory/control content.
- Pure highway platooning or lane-changing with no intersection relevance.
- Work before 2021-06-26, except for background notes.
- Papers with unverifiable metadata or no traceable source page.

## Scoring Rubric

Relevance is scored out of 100:

| Criterion | Points |
| --- | ---: |
| Intersection/CAV setting | 20 |
| Trajectory smoothing or speed optimization | 20 |
| Stop avoidance / delay / energy benefit | 20 |
| Collision avoidance / safety constraints | 20 |
| Link to scheduling, RL, graph methods, or replanning | 15 |
| Recency and validation quality | 5 |

Venue reputation is recorded separately. Do not invent impact factors. If
publisher rank, impact factor, or journal quartile is not verified, write
`not verified` and rely on the source/venue note.

## Search Log

| Date | Source | Query | Result | Decision |
| --- | --- | --- | --- | --- |
| 2026-06-26 | arXiv | `"connected automated vehicles" "unsignalized intersection" trajectory planning` | Found graph scheduling, spatial-domain control, and trajectory-planning candidates. | Included P02, P03, P11 |
| 2026-06-26 | arXiv / IEEE DOI | `"Real-time Cooperative Vehicle Coordination at Unsignalized Road Intersections"` | Verified IEEE T-ITS reference and DOI on arXiv. | Included P04 |
| 2026-06-26 | arXiv / IEEE DOI | `"Hybrid Reinforcement Learning-Based Eco-Driving" "Signalized Intersections"` | Verified IEEE T-ITS reference and DOI on arXiv. | Included P05 |
| 2026-06-26 | arXiv | `"eco-driving" "connected automated vehicles" "intersection"` | Found RL, PMP, and overtaking-enabled eco-approach papers. | Included P06, P07, P09 |
| 2026-06-26 | arXiv | `"control barrier function" "unsignalized intersections" autonomous vehicles` | Found recent HOCBF safety-filter paper and older CBF background. | Included P12; older CBF paper kept as background only |
| 2026-06-26 | arXiv / IEEE DOI | `"Real-World Evaluation" "Cooperative Intersection Management"` | Verified accepted IEEE ITS Magazine note and DOI. | Included P10 |
| 2026-06-26 | arXiv | `"autonomous intersection management" "reinforcement learning" 2024` | Found recent distributed MARL and adversarial AIM papers. | Included P14, P15 |
| 2026-06-26 | arXiv | `"Safety-Aware and Data-Driven Predictive Control" "Mixed Traffic Signalized Intersection"` | Verified mixed-traffic predictive-control safety paper. | Included P08 |
| 2026-06-26 | arXiv | `"Systematic Survey" "Control Techniques" "Connected and Automated Vehicles"` | Found broad control survey for terminology and background. | Included P13 |

## Background Notes

- Older foundational papers outside the 2021-06-26 to 2026-06-26 core window should be used only for background, e.g., reservation-based AIM, decentralized energy-optimal control at signal-free intersections, and CBF theory.
- The core list intentionally balances stop/energy smoothing sources with safety/collision-avoidance and scheduling/RL sources because the manuscript contribution is the interface between high-level JSSP scheduling and low-level executable trajectories.
