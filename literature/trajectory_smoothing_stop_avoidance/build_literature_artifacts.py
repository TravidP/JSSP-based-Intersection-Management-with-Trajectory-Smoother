#!/usr/bin/env python3
"""Build the trajectory smoothing literature-review artifacts.

The environment for this repository is intentionally lightweight, so this
script writes a simple standards-compliant XLSX file using only Python's
standard library. It also emits the Markdown protocol/template, an interactive
HTML review report, and a PDF-download helper.
"""

from __future__ import annotations

import html
import json
import os
import re
import textwrap
import zipfile
from datetime import date
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
PDF_DIR = ROOT / "pdfs"
TODAY = "2026-06-26"


PAPERS: list[dict[str, Any]] = [
    {
        "id": "P01",
        "bibkey": "chalaki2021priority",
        "title": "A Priority-Aware Replanning and Resequencing Framework for Coordination of Connected and Automated Vehicles",
        "authors": "Behdad Chalaki; Andreas A. Malikopoulos",
        "year": 2021,
        "venue": "arXiv preprint",
        "venue_type": "Preprint",
        "source_url": "https://arxiv.org/abs/2109.05573",
        "pdf_url": "https://arxiv.org/pdf/2109.05573",
        "doi": "10.48550/arXiv.2109.05573",
        "theme": "Scheduling/resequencing + optimal control",
        "method": "Event-driven replanning and priority-aware resequencing layered on decentralized CAV optimal control at a signal-free intersection.",
        "stop_avoidance": "The lower-level optimal-control trajectory is constructed so vehicles can conserve momentum rather than stop at the intersection when a feasible exit time exists.",
        "collision_avoidance": "Uses rear-end and lateral safety constraints around conflict points, with replanning when disturbances change feasibility.",
        "validation": "Numerical simulation of signal-free intersection coordination under resequencing and replanning.",
        "limitations": "Assumes connected automated vehicles, known paths, and simplified dynamics; the paper is closer to resequencing theory than to learned graph scheduling.",
        "support": "Directly supports this project's hierarchy: a high-level sequence or schedule provides target times, and a low-level controller checks executable motion.",
        "relevance": 94,
        "venue_reputation": "Useful technical preprint from a well-known CAV optimal-control group; venue reputation not verified beyond arXiv.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Core",
        "include_reason": "Recent JSSP-inspired resequencing paper with explicit schedule-to-control linkage.",
    },
    {
        "id": "P02",
        "bibkey": "chen2021conflictfree",
        "title": "Conflict-free Cooperation Method for Connected and Automated Vehicles at Unsignalized Intersections: Graph-based Modeling and Optimality Analysis",
        "authors": "Chaoyi Chen; Qing Xu; Mengchi Cai; Jiawei Wang; Jianqiang Wang; Biao Xu; Keqiang Li",
        "year": 2021,
        "venue": "Transportation Research Part C: Emerging Technologies / arXiv version",
        "venue_type": "Journal / Preprint",
        "source_url": "https://arxiv.org/abs/2107.07179",
        "pdf_url": "https://arxiv.org/pdf/2107.07179",
        "doi": "10.48550/arXiv.2107.07179",
        "theme": "Graph conflict modeling + passing order",
        "method": "Models trajectory conflicts as a conflict directed graph and coexisting undirected graph; solves passing order through improved depth-first spanning tree and minimum clique cover methods.",
        "stop_avoidance": "Optimizes evacuation time and average delay, using distributed control to reduce idling near the stop line.",
        "collision_avoidance": "Conflict-free graph edges represent crossing, diverging, converging, and reachability conflicts before scheduling.",
        "validation": "Traffic simulations over varying vehicle counts and volumes; reports efficiency and fuel-economy improvements.",
        "limitations": "Mostly longitudinal control, ideal communication, and no lane changing in this paper's base formulation.",
        "support": "Strong support for representing intersection conflicts as typed graph relations, similar to the operation graph in this manuscript.",
        "relevance": 92,
        "venue_reputation": "Transportation Research Part C is a leading transportation automation journal; exact publication metadata should be checked before final submission.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Core",
        "include_reason": "Recent graph-based conflict-free scheduling paper with explicit conflict types and control execution.",
    },
    {
        "id": "P03",
        "bibkey": "chen2021lanechanging",
        "title": "Cooperation Method of Connected and Automated Vehicles at Unsignalized Intersections: Lane Changing and Arrival Scheduling",
        "authors": "Chaoyi Chen; Mengchi Cai; Jiawei Wang; Kai Li; Qing Xu; Jianqiang Wang; Keqiang Li",
        "year": 2021,
        "venue": "arXiv preprint",
        "venue_type": "Preprint",
        "source_url": "https://arxiv.org/abs/2109.14175",
        "pdf_url": "https://arxiv.org/pdf/2109.14175",
        "doi": "10.48550/arXiv.2109.14175",
        "theme": "Lane changing + arrival scheduling",
        "method": "Two-stage framework decoupling lateral lane assignment/path planning from graph-based arrival scheduling with minimum clique cover.",
        "stop_avoidance": "Improves traffic efficiency by choosing target lanes and arrival schedules that avoid unnecessary queuing.",
        "collision_avoidance": "Conflict-free arrival scheduling and formation-control assumptions prevent incompatible movements.",
        "validation": "Numerical simulations for different vehicle counts and traffic volumes.",
        "limitations": "arXiv note reports text overlap with the authors' earlier graph-based paper; use mainly for lane-changing extension context.",
        "support": "Useful for discussing route-template/lane-choice extensions beyond the current fixed-route JSSP formulation.",
        "relevance": 82,
        "venue_reputation": "arXiv preprint; venue reputation not verified.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Supporting core",
        "include_reason": "Extends graph scheduling toward lateral planning, which helps position the route-template assumption.",
    },
    {
        "id": "P04",
        "bibkey": "luo2023realtime",
        "title": "Real-time Cooperative Vehicle Coordination at Unsignalized Road Intersections",
        "authors": "Jiping Luo; Tingting Zhang; Rui Hao; Donglin Li; Chunsheng Chen; Zhenyu Na; Qinyu Zhang",
        "year": 2023,
        "venue": "IEEE Transactions on Intelligent Transportation Systems",
        "venue_type": "Journal",
        "source_url": "https://arxiv.org/abs/2205.01278",
        "pdf_url": "https://arxiv.org/pdf/2205.01278",
        "doi": "10.1109/TITS.2023.3243940",
        "theme": "DRL cooperative trajectory optimization",
        "method": "Formulates unified cooperative trajectory optimization for unsignalized intersections and solves the sequential decision problem with TD3.",
        "stop_avoidance": "Optimizes throughput and continuous flow, reducing delay compared with conservative coordination.",
        "collision_avoidance": "Safety and long-term stability constraints are embedded in the cooperative trajectory optimization framework.",
        "validation": "Simulation and practical experiments; authors report millisecond-scale computation and scalability with lane count.",
        "limitations": "Centralized control-authority handoff and DRL policy behavior may be difficult to certify in mixed traffic.",
        "support": "Shows why learned policies are attractive for online intersection coordination but need a structured safety/smoothing interface.",
        "relevance": 91,
        "venue_reputation": "IEEE T-ITS is a highly reputable ITS journal; DOI and journal reference verified on arXiv.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Core",
        "include_reason": "Recent high-quality DRL trajectory coordination paper for unsignalized CAV intersections.",
    },
    {
        "id": "P05",
        "bibkey": "bai2022hybrid",
        "title": "Hybrid Reinforcement Learning-Based Eco-Driving Strategy for Connected and Automated Vehicles at Signalized Intersections",
        "authors": "Zhengwei Bai; Peng Hao; Wei Shangguan; Baigen Cai; Matthew J. Barth",
        "year": 2022,
        "venue": "IEEE Transactions on Intelligent Transportation Systems",
        "venue_type": "Journal",
        "source_url": "https://arxiv.org/abs/2201.07833",
        "pdf_url": "https://arxiv.org/pdf/2201.07833",
        "doi": "10.1109/TITS.2022.3145798",
        "theme": "Eco-driving + hybrid RL",
        "method": "Combines a rule-based driving manager, V2I/vision features, and RL to generate longitudinal and lateral eco-driving actions.",
        "stop_avoidance": "Targets energy and travel-time reduction by smoothing approach behavior at signalized intersections.",
        "collision_avoidance": "Mixed-traffic policy includes rule-based safety management around surrounding vehicles.",
        "validation": "Unity-based mixed-traffic intersection simulation; reports 12.70 percent energy reduction and 11.75 percent travel-time saving against a model-based eco-driving baseline.",
        "limitations": "Signalized setting and policy-level action output differ from a scheduler-to-smoother architecture.",
        "support": "Supports the argument that stop-and-go reduction and energy-aware smoothing are important low-level objectives.",
        "relevance": 86,
        "venue_reputation": "IEEE T-ITS is a highly reputable ITS journal; DOI and journal reference verified on arXiv.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Core",
        "include_reason": "Strong recent source for smoothing/eco-driving benefits at intersections.",
    },
    {
        "id": "P06",
        "bibkey": "jiang2023ecodriving",
        "title": "Eco-driving for Electric Connected Vehicles at Signalized Intersections: A Parameterized Reinforcement Learning Approach",
        "authors": "Xia Jiang; Jian Zhang; Dan Li",
        "year": 2023,
        "venue": "Journal article related DOI / arXiv version",
        "venue_type": "Journal / Preprint",
        "source_url": "https://arxiv.org/abs/2206.12065",
        "pdf_url": "https://arxiv.org/pdf/2206.12065",
        "doi": "10.1080/21680566.2023.2215957",
        "theme": "Electric CV eco-driving + parameterized RL",
        "method": "Parameterized RL combines model-based car-following, lane-changing policy, and learned longitudinal/lateral decisions.",
        "stop_avoidance": "Learns energy-saving actions around signalized intersections without interrupting surrounding HDVs.",
        "collision_avoidance": "Safety is handled through model-based car-following and lane-changing constraints around human-driven vehicles.",
        "validation": "SUMO evaluation from single-vehicle and flow perspectives.",
        "limitations": "Signalized intersections and electric connected vehicles rather than fully signal-free autonomous scheduling.",
        "support": "Provides a SUMO-compatible example of energy and stop reduction metrics for the experimental section.",
        "relevance": 83,
        "venue_reputation": "Related DOI exists on arXiv; exact journal reputation not verified in this pass.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Core",
        "include_reason": "Recent RL eco-driving paper with SUMO validation and safety-aware mixed-traffic behavior.",
    },
    {
        "id": "P07",
        "bibkey": "lakshmanan2022cooperative",
        "title": "Cooperative Control in Eco-Driving of Electric Connected and Autonomous Vehicles in an Un-Signalized Urban Intersection",
        "authors": "Vinith Kumar Lakshmanan; Antonio Sciarretta; Ouafae El Ganaoui-Mourlan",
        "year": 2022,
        "venue": "AAC 2022 submission / arXiv version",
        "venue_type": "Conference / Preprint",
        "source_url": "https://arxiv.org/abs/2206.12360",
        "pdf_url": "https://arxiv.org/pdf/2206.12360",
        "doi": "10.48550/arXiv.2206.12360",
        "theme": "Eco-driving optimal speed profile",
        "method": "Single-level eco-driving optimization solved with Pontryagin's Minimum Principle for electric CAV speed profiles at an unsignalized intersection.",
        "stop_avoidance": "Focuses directly on optimal speed profiles that reduce energy use and avoid inefficient stop-and-go behavior.",
        "collision_avoidance": "Analytical conflict cases and cooperation levels encode interaction safety among CAVs.",
        "validation": "Simulation comparison of cooperative and non-cooperative eco-driving against IDM baseline.",
        "limitations": "Narrower single-vehicle/eco-driving emphasis; less detail on high-level scheduling.",
        "support": "Supports the smoothing objective terms for acceleration, energy proxy, and stop avoidance.",
        "relevance": 81,
        "venue_reputation": "Conference/preprint status only; venue reputation not verified.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Core",
        "include_reason": "Directly relevant to no-stop and energy-aware speed smoothing at unsignalized intersections.",
    },
    {
        "id": "P08",
        "bibkey": "mahbub2022safety",
        "title": "Safety-Aware and Data-Driven Predictive Control for Connected Automated Vehicles at a Mixed Traffic Signalized Intersection",
        "authors": "A. M. Ishtiaque Mahbub; Viet-Anh Le; Andreas A. Malikopoulos",
        "year": 2022,
        "venue": "arXiv preprint",
        "venue_type": "Preprint",
        "source_url": "https://arxiv.org/abs/2203.05739",
        "pdf_url": "https://arxiv.org/pdf/2203.05739",
        "doi": "10.48550/arXiv.2203.05739",
        "theme": "Data-driven predictive control + mixed traffic safety",
        "method": "Finite-horizon predictive control uses recursive least squares to estimate preceding HDV behavior in real time.",
        "stop_avoidance": "Smooths CAV response near yellow/red phases while avoiding overly conservative braking behind HDVs.",
        "collision_avoidance": "Prioritizes rear-end collision avoidance when preceding human-driven vehicles approach signal changes.",
        "validation": "Numerical simulation and robustness analysis.",
        "limitations": "Signalized and rear-end-focused rather than conflict-zone scheduling across all movements.",
        "support": "Useful for fallback and mixed-traffic safety discussion, especially when predicted trajectories deviate.",
        "relevance": 78,
        "venue_reputation": "arXiv preprint; venue reputation not verified.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Core",
        "include_reason": "Strong safety-focused predictive-control source for collision avoidance near intersections.",
    },
    {
        "id": "P09",
        "bibkey": "dong2023overtaking",
        "title": "Overtaking-enabled Eco-approach Control at Signalized Intersections for Connected and Automated Vehicles",
        "authors": "Haoxuan Dong; Weichao Zhuang; Guoyuan Wu; Zhaojian Li; Guodong Yin; Ziyou Song",
        "year": 2023,
        "venue": "arXiv preprint",
        "venue_type": "Preprint",
        "source_url": "https://arxiv.org/abs/2306.09736",
        "pdf_url": "https://arxiv.org/pdf/2306.09736",
        "doi": "10.48550/arXiv.2306.09736",
        "theme": "Eco-approach + relaxed FIFO",
        "method": "Receding-horizon two-stage control: dynamic-programming lane optimization followed by PMP speed trajectory optimization.",
        "stop_avoidance": "Relaxes FIFO queuing at signalized intersections to reduce driving cost, energy consumption, and delay.",
        "collision_avoidance": "Handles dynamic disturbance from preceding vehicles and lane-choice constraints.",
        "validation": "Extensive simulations report average driving-cost improvements over constant-speed and regular eco-approach baselines.",
        "limitations": "Signalized intersection and overtaking/lane planning assumptions are outside the current fixed-route JSSP scope.",
        "support": "Supports the critique that FCFS/FIFO can be suboptimal and that speed smoothing should be coupled to sequencing.",
        "relevance": 84,
        "venue_reputation": "arXiv preprint; venue reputation not verified.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Core",
        "include_reason": "Recent source connecting FIFO relaxation, speed optimization, delay, and energy.",
    },
    {
        "id": "P10",
        "bibkey": "klimke2026realworld",
        "title": "Real-World Evaluation of Two Cooperative Intersection Management Approaches",
        "authors": "Marvin Klimke; Max Bastian Mertens; Benjamin Volz; Michael Buchholz",
        "year": 2026,
        "venue": "IEEE Intelligent Transportation Systems Magazine (accepted)",
        "venue_type": "Magazine / Preprint",
        "source_url": "https://arxiv.org/abs/2403.16478",
        "pdf_url": "https://arxiv.org/pdf/2403.16478",
        "doi": "10.1109/MITS.2025.3643199",
        "theme": "Real-world cooperative intersection management",
        "method": "Compares multi-scenario prediction and graph-based reinforcement learning approaches in mixed-traffic simulation and real drives.",
        "stop_avoidance": "Reports substantial reductions in crossing time and number of stops for cooperative maneuver planning.",
        "collision_avoidance": "Evaluates criticality metrics while operating with prototype connected automated vehicles in public traffic.",
        "validation": "Novel mixed-traffic simulation framework plus real-world prototype connected automated vehicle drives.",
        "limitations": "Focuses on cooperative maneuver planning evaluation, not a JSSP formulation.",
        "support": "Excellent evidence that stop count is a practical metric and that real-world mixed traffic should be considered in future validation.",
        "relevance": 90,
        "venue_reputation": "IEEE ITS Magazine is reputable and practice-facing; accepted-publication note and DOI are verified on arXiv.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Core",
        "include_reason": "Recent real-world evaluation directly reports stop-count reduction and criticality metrics.",
    },
    {
        "id": "P11",
        "bibkey": "zhao2025spatial",
        "title": "A Spatial-Domain Coordinated Control Method for CAVs at Unsignalized Intersections Considering Motion Uncertainty",
        "authors": "Tong Zhao; Nikolce Murgovski; Baigen Cai; Wei ShangGuan",
        "year": 2025,
        "venue": "arXiv preprint",
        "venue_type": "Preprint",
        "source_url": "https://arxiv.org/abs/2412.04290",
        "pdf_url": "https://arxiv.org/pdf/2412.04290",
        "doi": "10.48550/arXiv.2412.04290",
        "theme": "Spatial-domain robust trajectory planning",
        "method": "Transforms coordinated control into a spatial-domain nonlinear program with unified linear collision-avoidance constraints and real-time iteration.",
        "stop_avoidance": "Generates smooth trajectories under state/control constraints, avoiding unnecessary braking where robust constraints permit.",
        "collision_avoidance": "Handles crossing, following, merging, and diverging conflicts under path and speed uncertainty of HDVs.",
        "validation": "Simulation case studies; reported RTI computation reduction by orders of magnitude with small optimality loss.",
        "limitations": "Optimization-heavy; not a learned scheduler, and publication venue beyond arXiv not verified.",
        "support": "Very strong for the smoother's feasibility and robust collision-avoidance constraints.",
        "relevance": 92,
        "venue_reputation": "Recent technical arXiv preprint; venue reputation not verified.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Core",
        "include_reason": "Most directly relevant recent robust trajectory-planning paper for unsignalized mixed traffic.",
    },
    {
        "id": "P12",
        "bibkey": "yu2025uncertainty",
        "title": "Uncertainty-Aware Safety-Critical Decision and Control for Autonomous Vehicles at Unsignalized Intersections",
        "authors": "Ran Yu; Zhuoren Li; Lu Xiong; Wei Han; Bo Leng",
        "year": 2025,
        "venue": "arXiv preprint",
        "venue_type": "Preprint",
        "source_url": "https://arxiv.org/abs/2505.19939",
        "pdf_url": "https://arxiv.org/pdf/2505.19939",
        "doi": "10.48550/arXiv.2505.19939",
        "theme": "Uncertainty-aware safe RL + HOCBF",
        "method": "Risk-aware ensemble distributional RL estimates policy uncertainty, then a high-order control barrier function acts as a safety filter.",
        "stop_avoidance": "Balances safety and traffic efficiency by switching between flexible RL behavior and conservative HOCBF intervention.",
        "collision_avoidance": "HOCBF safety filter dynamically adjusts constraints using joint uncertainty in unsignalized-intersection tasks.",
        "validation": "Simulation tests on multiple unsignalized-intersection tasks against safety and efficiency baselines.",
        "limitations": "Single-agent urban autonomous-driving framing rather than centralized conflict-zone scheduling.",
        "support": "Supports adding CBF/HOCBF safety filters or fallback logic to learned policies.",
        "relevance": 84,
        "venue_reputation": "Recent arXiv preprint; venue reputation not verified.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Core",
        "include_reason": "Recent safety-filter paper directly relevant to collision avoidance under learned decisions.",
    },
    {
        "id": "P13",
        "bibkey": "liu2023systematic",
        "title": "A Systematic Survey of Control Techniques and Applications in Connected and Automated Vehicles",
        "authors": "Wei Liu; Min Hua; Zhiyun Deng; Zonglin Meng; Yanjun Huang; Chuan Hu; Shunhui Song; Letian Gao; Changsheng Liu; Bin Shuai; Amir Khajepour; Lu Xiong; Xin Xia",
        "year": 2023,
        "venue": "arXiv survey",
        "venue_type": "Survey / Preprint",
        "source_url": "https://arxiv.org/abs/2303.05665",
        "pdf_url": "https://arxiv.org/pdf/2303.05665",
        "doi": "10.48550/arXiv.2303.05665",
        "theme": "CAV control survey",
        "method": "Systematic survey from vehicle state estimation and trajectory tracking to collaborative CAV control applications.",
        "stop_avoidance": "Frames comfort, energy saving, and transportation efficiency as central CAV control goals.",
        "collision_avoidance": "Reviews vehicle-control approaches relevant to safety and collaborative control.",
        "validation": "Literature survey rather than original experiments.",
        "limitations": "Broad CAV control overview; not intersection-smoothing specific.",
        "support": "Useful context citation for why trajectory tracking, collaborative control, safety, comfort, and energy belong together.",
        "relevance": 72,
        "venue_reputation": "Survey preprint; broad coverage, venue reputation not verified.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Context",
        "include_reason": "Recent control survey to ground terminology and broader CAV-control trends.",
    },
    {
        "id": "P14",
        "bibkey": "cederle2024distributed",
        "title": "A Distributed Approach to Autonomous Intersection Management via Multi-Agent Reinforcement Learning",
        "authors": "Matteo Cederle; Marco Fabris; Gian Antonio Susto",
        "year": 2024,
        "venue": "ATT 2024 Workshop, CEUR-WS Vol. 3813",
        "venue_type": "Workshop",
        "source_url": "https://arxiv.org/abs/2405.08655",
        "pdf_url": "https://arxiv.org/pdf/2405.08655",
        "doi": "10.48550/arXiv.2405.08655",
        "theme": "Distributed MARL for AIM",
        "method": "Distributed multi-agent RL for autonomous intersection management using 3D surround-view assumptions and prioritized scenario replay.",
        "stop_avoidance": "Improves benchmark metrics in SMARTS, implying smoother flow through decentralized decisions.",
        "collision_avoidance": "Aims for accurate decentralized navigation without a central server; safety is evaluated through simulation metrics.",
        "validation": "SMARTS virtual environment; accepted at ATT 2024 and available through CEUR-WS.",
        "limitations": "Workshop paper; not focused on explicit trajectory smoothing or formal safety constraints.",
        "support": "Useful contrast to the proposed centralized JSSP/RL rollout, showing distributed AIM as an alternative branch.",
        "relevance": 70,
        "venue_reputation": "Peer-reviewed workshop proceedings in CEUR-WS; reputable but less archival than major journals.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Context",
        "include_reason": "Recent AIM learning paper for contrasting centralized and distributed control choices.",
    },
    {
        "id": "P15",
        "bibkey": "li2023dhal",
        "title": "D-HAL: Distributed Hierarchical Adversarial Learning for Multi-Agent Interaction in Autonomous Intersection Management",
        "authors": "Guanzhou Li; Jianping Wu; Yujing He",
        "year": 2023,
        "venue": "arXiv preprint",
        "venue_type": "Preprint",
        "source_url": "https://arxiv.org/abs/2303.02630",
        "pdf_url": "https://arxiv.org/pdf/2303.02630",
        "doi": "10.48550/arXiv.2303.02630",
        "theme": "Distributed hierarchical learning for AIM",
        "method": "Non-RL adversarial actor/discriminator framework evaluates immediate interaction and final trajectory quality for multi-agent AIM.",
        "stop_avoidance": "Targets reduced travel time and smoother interaction outcomes compared with distributed learning baselines.",
        "collision_avoidance": "Immediate and final discriminators score interaction safety and trajectory outcomes.",
        "validation": "Four-way six-lane intersection experiments against state-of-the-art methods.",
        "limitations": "Learning framework lacks explicit optimization/smoothing formulation and formal safety guarantees.",
        "support": "Useful for explaining why learned interaction policies must still be checked by a low-level feasibility/safety layer.",
        "relevance": 73,
        "venue_reputation": "arXiv preprint; venue reputation not verified.",
        "pdf_status": "open PDF downloaded from arXiv",
        "review_status": "Context",
        "include_reason": "Recent learning-based AIM source with safety/travel-time claims for positioning the RL scheduler.",
    },
]


SEARCH_LOG = [
    ["2026-06-26", "arXiv", '"connected automated vehicles" "unsignalized intersection" trajectory planning', "Found graph scheduling, spatial-domain control, and trajectory-planning candidates.", "Included P02, P03, P11"],
    ["2026-06-26", "arXiv / IEEE DOI", '"Real-time Cooperative Vehicle Coordination at Unsignalized Road Intersections"', "Verified IEEE T-ITS reference and DOI on arXiv.", "Included P04"],
    ["2026-06-26", "arXiv / IEEE DOI", '"Hybrid Reinforcement Learning-Based Eco-Driving" "Signalized Intersections"', "Verified IEEE T-ITS reference and DOI on arXiv.", "Included P05"],
    ["2026-06-26", "arXiv", '"eco-driving" "connected automated vehicles" "intersection"', "Found RL, PMP, and overtaking-enabled eco-approach papers.", "Included P06, P07, P09"],
    ["2026-06-26", "arXiv", '"control barrier function" "unsignalized intersections" autonomous vehicles', "Found recent HOCBF safety-filter paper and older CBF background.", "Included P12; older CBF paper kept as background only"],
    ["2026-06-26", "arXiv / IEEE DOI", '"Real-World Evaluation" "Cooperative Intersection Management"', "Verified accepted IEEE ITS Magazine note and DOI.", "Included P10"],
    ["2026-06-26", "arXiv", '"autonomous intersection management" "reinforcement learning" 2024', "Found recent distributed MARL and adversarial AIM papers.", "Included P14, P15"],
    ["2026-06-26", "arXiv", '"Safety-Aware and Data-Driven Predictive Control" "Mixed Traffic Signalized Intersection"', "Verified mixed-traffic predictive-control safety paper.", "Included P08"],
    ["2026-06-26", "arXiv", '"Systematic Survey" "Control Techniques" "Connected and Automated Vehicles"', "Found broad control survey for terminology and background.", "Included P13"],
]


BACKGROUND_NOTES = [
    "Older foundational papers outside the 2021-06-26 to 2026-06-26 core window should be used only for background, e.g., reservation-based AIM, decentralized energy-optimal control at signal-free intersections, and CBF theory.",
    "The core list intentionally balances stop/energy smoothing sources with safety/collision-avoidance and scheduling/RL sources because the manuscript contribution is the interface between high-level JSSP scheduling and low-level executable trajectories.",
]


def wrap(text: str, width: int = 88) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def paper_markdown(p: dict[str, Any]) -> str:
    return f"""### {p['id']}. {p['title']}

- **Authors:** {p['authors']}
- **Year / venue:** {p['year']}, {p['venue']}
- **Source:** {p['source_url']}
- **PDF:** {p['pdf_url']}
- **Theme:** {p['theme']}
- **Project relevance:** {p['relevance']}/100
- **Technical method:** {p['method']}
- **Stop avoidance / smoothing:** {p['stop_avoidance']}
- **Collision avoidance / safety:** {p['collision_avoidance']}
- **Validation:** {p['validation']}
- **Limitations:** {p['limitations']}
- **How it supports this project:** {p['support']}
"""


def write_search_protocol() -> None:
    rows = "\n".join(
        f"| {d} | {db} | `{q}` | {result} | {decision} |"
        for d, db, q, result, decision in SEARCH_LOG
    )
    content = f"""# Literature Search Protocol: Trajectory Smoothing And Avoidance

Date created: {TODAY}

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
{rows}

## Background Notes

{chr(10).join(f'- {note}' for note in BACKGROUND_NOTES)}
"""
    (ROOT / "search_protocol.md").write_text(content, encoding="utf-8")


def write_review_template() -> None:
    content = """# Paper Review Template

Use one copy of this template per paper when extending the review.

## Bibliographic Data

- Review ID:
- BibTeX key:
- Title:
- Authors:
- Year:
- Venue:
- DOI:
- Source URL:
- PDF status:

## Screening

- Include / exclude / maybe:
- Main theme:
- Reason for inclusion:
- Relevance score:
- Venue/source reputation note:

## Technical Extraction

- Problem setting:
- Vehicle assumptions:
- Intersection assumptions:
- High-level decision variable:
- Low-level trajectory/control variable:
- Objective function:
- Stop avoidance / smoothing mechanism:
- Collision-avoidance mechanism:
- Replanning or feedback mechanism:
- Solver / learning method:
- Validation platform:
- Metrics:
- Main reported results:
- Limitations:

## Use In This Manuscript

- Which manuscript claim does this support?
- Suggested citation sentence:
- Does it support the scheduler, smoother, safety fallback, or evaluation metrics?
- Notes for future experiments:
"""
    (ROOT / "review_template.md").write_text(content, encoding="utf-8")


def col_name(n: int) -> str:
    out = ""
    while n:
        n, r = divmod(n - 1, 26)
        out = chr(65 + r) + out
    return out


def cell_ref(row: int, col: int) -> str:
    return f"{col_name(col)}{row}"


def xml_cell(value: Any, row: int, col: int, style: int = 0) -> str:
    ref = cell_ref(row, col)
    s = f' s="{style}"' if style else ""
    if value is None:
        return f'<c r="{ref}"{s}/>'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}"{s}><v>{value}</v></c>'
    text = escape(str(value))
    return f'<c r="{ref}" t="inlineStr"{s}><is><t xml:space="preserve">{text}</t></is></c>'


def sheet_xml(rows: list[list[Any]], widths: list[int] | None = None, autofilter: bool = True, validations: str = "") -> str:
    max_col = max(len(r) for r in rows) if rows else 1
    max_row = len(rows)
    dim = f"A1:{cell_ref(max_row, max_col)}"
    cols = ""
    if widths:
        col_entries = []
        for idx, width in enumerate(widths, start=1):
            col_entries.append(f'<col min="{idx}" max="{idx}" width="{width}" customWidth="1"/>')
        cols = f"<cols>{''.join(col_entries)}</cols>"
    row_xml = []
    for r_idx, row in enumerate(rows, start=1):
        style = 1 if r_idx == 1 else 0
        cells = "".join(xml_cell(v, r_idx, c_idx, style) for c_idx, v in enumerate(row, start=1))
        ht = ' ht="24" customHeight="1"' if r_idx == 1 else ""
        row_xml.append(f'<row r="{r_idx}"{ht}>{cells}</row>')
    filter_xml = f'<autoFilter ref="{dim}"/>' if autofilter and max_row > 1 else ""
    pane = '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<dimension ref="{dim}"/>{pane}{cols}<sheetData>{''.join(row_xml)}</sheetData>{filter_xml}{validations}<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>
</worksheet>'''


def write_xlsx() -> None:
    xlsx_path = ROOT / "papers.xlsx"
    summary_rows = [
        ["Metric", "Value", "Note"],
        ["Review date", TODAY, "Generated for manuscript revision"],
        ["Core papers", len(PAPERS), "Strict 2021-06-26 to 2026-06-26 window"],
        ["Average relevance", round(sum(p["relevance"] for p in PAPERS) / len(PAPERS), 1), "Out of 100"],
        ["Open PDFs", sum(1 for p in PAPERS if p["pdf_status"].startswith("open")), "Downloaded from official/open pages"],
        ["Top relevance", max(p["relevance"] for p in PAPERS), "Highest project-fit score"],
    ]
    paper_rows = [[
        "ID", "Selected", "Stars", "Review Status", "BibTeX Key", "Year", "Title", "Authors",
        "Venue", "Venue Type", "Theme", "Relevance", "Source URL", "PDF URL", "PDF Status",
        "DOI", "Inclusion Reason"
    ]]
    for p in PAPERS:
        paper_rows.append([
            p["id"], "", "", p["review_status"], p["bibkey"], p["year"], p["title"], p["authors"],
            p["venue"], p["venue_type"], p["theme"], p["relevance"], p["source_url"], p["pdf_url"],
            p["pdf_status"], p["doi"], p["include_reason"],
        ])
    matrix_rows = [[
        "ID", "Title", "Method", "Stop Avoidance / Smoothing", "Collision Avoidance / Safety",
        "Validation", "Limitations", "How It Supports This Project"
    ]]
    for p in PAPERS:
        matrix_rows.append([
            p["id"], p["title"], p["method"], p["stop_avoidance"], p["collision_avoidance"],
            p["validation"], p["limitations"], p["support"],
        ])
    venue_rows = [["ID", "Venue", "Venue Type", "Reputation Note", "Source URL"]]
    for p in PAPERS:
        venue_rows.append([p["id"], p["venue"], p["venue_type"], p["venue_reputation"], p["source_url"]])
    search_rows = [["Date", "Source", "Query", "Result", "Decision"], *SEARCH_LOG]
    sheets = [
        ("Summary", summary_rows, [24, 18, 64]),
        ("Papers", paper_rows, [8, 10, 8, 18, 22, 8, 56, 40, 34, 18, 28, 12, 40, 40, 30, 28, 56]),
        ("Review Matrix", matrix_rows, [8, 56, 48, 48, 48, 42, 42, 50]),
        ("Venue Reputation", venue_rows, [8, 42, 20, 72, 44]),
        ("Search Log", search_rows, [14, 20, 54, 62, 36]),
    ]
    validations = {
        "Papers": '<dataValidations count="2"><dataValidation type="list" allowBlank="1" sqref="B2:B200"><formula1>"yes,no,maybe"</formula1></dataValidation><dataValidation type="whole" operator="between" allowBlank="1" sqref="C2:C200"><formula1>1</formula1><formula2>5</formula2></dataValidation></dataValidations>',
    }
    with zipfile.ZipFile(xlsx_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
""" + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1, len(sheets) + 1)) + "</Types>")
        zf.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>""")
        zf.writestr("docProps/core.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>Trajectory Smoothing And Avoidance Literature Review</dc:title>
<dc:creator>Codex</dc:creator>
<cp:lastModifiedBy>Codex</cp:lastModifiedBy>
<dcterms:created xsi:type="dcterms:W3CDTF">{TODAY}T00:00:00Z</dcterms:created>
<dcterms:modified xsi:type="dcterms:W3CDTF">{TODAY}T00:00:00Z</dcterms:modified>
</cp:coreProperties>""")
        zf.writestr("docProps/app.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Codex</Application></Properties>""")
        workbook_sheets = "".join(f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>' for i, (name, _, _) in enumerate(sheets, start=1))
        zf.writestr("xl/workbook.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>{workbook_sheets}</sheets></workbook>""")
        rels = "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, len(sheets) + 1))
        rels += f'<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        zf.writestr("xl/_rels/workbook.xml.rels", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>""")
        zf.writestr("xl/styles.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF2F5597"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border><border><left style="thin"><color rgb="FFD9E2F3"/></left><right style="thin"><color rgb="FFD9E2F3"/></right><top style="thin"><color rgb="FFD9E2F3"/></top><bottom style="thin"><color rgb="FFD9E2F3"/></bottom><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf><xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf></cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>""")
        for idx, (name, rows, widths) in enumerate(sheets, start=1):
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", sheet_xml(rows, widths, validations=validations.get(name, "")))


def write_html() -> None:
    data_json = json.dumps(PAPERS, ensure_ascii=False)
    cards = []
    for p in PAPERS:
        cards.append(f"""
<article class="paper-card" data-year="{p['year']}" data-theme="{html.escape(p['theme'])}" data-venue="{html.escape(p['venue_type'])}" data-score="{p['relevance']}" data-pdf="{html.escape(p['pdf_status'])}" id="{p['id']}">
  <header>
    <div class="paper-select"><input type="checkbox" id="sel-{p['id']}" data-paper="{p['id']}"><label for="sel-{p['id']}">Select</label></div>
    <div>
      <p class="meta">{p['id']} · {p['year']} · {html.escape(p['venue_type'])} · relevance {p['relevance']}/100</p>
      <h2>{html.escape(p['title'])}</h2>
      <p class="authors">{html.escape(p['authors'])}</p>
    </div>
    <div class="stars" data-paper="{p['id']}" aria-label="Star rating for {p['id']}"></div>
  </header>
  <dl class="facts">
    <div><dt>Venue</dt><dd>{html.escape(p['venue'])}</dd></div>
    <div><dt>Theme</dt><dd>{html.escape(p['theme'])}</dd></div>
    <div><dt>Source</dt><dd><a href="{p['source_url']}">{p['source_url']}</a></dd></div>
    <div><dt>PDF</dt><dd><a href="{p['pdf_url']}">{p['pdf_url']}</a><br>{html.escape(p['pdf_status'])}</dd></div>
  </dl>
  <section class="summary-grid">
    <div><h3>Technical Summary</h3><p>{html.escape(p['method'])}</p></div>
    <div><h3>Stop Avoidance</h3><p>{html.escape(p['stop_avoidance'])}</p></div>
    <div><h3>Collision Avoidance</h3><p>{html.escape(p['collision_avoidance'])}</p></div>
    <div><h3>Validation</h3><p>{html.escape(p['validation'])}</p></div>
    <div><h3>Limitations</h3><p>{html.escape(p['limitations'])}</p></div>
    <div><h3>Use In This Project</h3><p>{html.escape(p['support'])}</p></div>
  </section>
  <p class="venue-note"><strong>Venue/source note:</strong> {html.escape(p['venue_reputation'])}</p>
</article>""")
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Trajectory Smoothing And Avoidance Literature Review</title>
  <style>
    :root {{
      --ink: #1f2933;
      --muted: #5f6b7a;
      --line: #d6dde8;
      --surface: #f6f8fb;
      --accent: #9a4a12;
      --blue: #1f5f8b;
      --green: #1b7254;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font: 14px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: #fff; }}
    header.hero {{ padding: 28px 34px 18px; background: #f2f5f9; border-bottom: 1px solid var(--line); }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .hero p {{ margin: 4px 0; color: var(--muted); max-width: 980px; }}
    .toolbar {{ position: sticky; top: 0; z-index: 5; display: grid; grid-template-columns: repeat(6, minmax(120px, 1fr)); gap: 10px; padding: 14px 34px; background: rgba(255,255,255,.96); border-bottom: 1px solid var(--line); }}
    .toolbar label {{ display: grid; gap: 4px; font-size: 12px; color: var(--muted); }}
    select, input[type="number"], button {{ min-height: 34px; border: 1px solid var(--line); border-radius: 6px; background: white; padding: 6px 8px; color: var(--ink); }}
    button {{ cursor: pointer; font-weight: 650; }}
    main {{ padding: 24px 34px 50px; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; margin-bottom: 20px; }}
    .stat {{ border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: var(--surface); }}
    .stat b {{ display: block; font-size: 24px; color: var(--blue); }}
    .paper-card {{ border: 1px solid var(--line); border-radius: 8px; padding: 18px; margin: 0 0 18px; break-inside: avoid; }}
    .paper-card > header {{ display: grid; grid-template-columns: 88px 1fr 130px; gap: 16px; align-items: start; }}
    .paper-select {{ display: flex; gap: 6px; align-items: center; color: var(--muted); }}
    .meta {{ margin: 0 0 4px; color: var(--accent); font-weight: 700; }}
    h2 {{ margin: 0 0 4px; font-size: 20px; line-height: 1.25; }}
    .authors {{ margin: 0; color: var(--muted); }}
    .stars button {{ border: 0; background: transparent; color: #c4a15b; font-size: 22px; min-height: 28px; padding: 0 1px; }}
    .stars button.active {{ color: #a25c00; }}
    .facts {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 18px; padding: 12px 0; margin: 10px 0 0; border-top: 1px solid var(--line); }}
    .facts div {{ min-width: 0; }}
    dt {{ font-weight: 700; color: var(--muted); }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .summary-grid div {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 12px; }}
    h3 {{ margin: 0 0 5px; font-size: 14px; color: var(--green); }}
    .summary-grid p, .venue-note {{ margin: 0; }}
    .venue-note {{ margin-top: 12px; color: var(--muted); }}
    .hidden {{ display: none !important; }}
    @media print {{
      .toolbar {{ display: none; }}
      body {{ font-size: 11px; }}
      header.hero {{ padding: 16px 20px; }}
      main {{ padding: 14px 20px; }}
      .paper-card {{ page-break-inside: avoid; }}
      .paper-card > header {{ grid-template-columns: 1fr; }}
      .paper-select, .stars {{ display: none; }}
      a {{ color: var(--ink); text-decoration: none; }}
    }}
  </style>
</head>
<body>
  <header class="hero">
    <h1>Trajectory Smoothing And Avoidance Literature Review</h1>
    <p>Fifteen recent papers selected for a JSSP/RL autonomous intersection manager with low-level smooth trajectory execution. Review date: {TODAY}.</p>
    <p>The list balances stop avoidance, energy/delay reduction, collision avoidance, graph scheduling, RL, and replanning.</p>
  </header>
  <section class="toolbar" aria-label="Filters">
    <label>Theme
      <select id="themeFilter"><option value="">All themes</option></select>
    </label>
    <label>Venue type
      <select id="venueFilter"><option value="">All venues</option></select>
    </label>
    <label>Year
      <select id="yearFilter"><option value="">All years</option></select>
    </label>
    <label>Minimum score
      <input id="scoreFilter" type="number" min="0" max="100" value="0">
    </label>
    <button id="selectedOnly">Show selected only</button>
    <button onclick="window.print()">Print / Export PDF</button>
  </section>
  <main>
    <section class="stats">
      <div class="stat"><b>{len(PAPERS)}</b>Core papers</div>
      <div class="stat"><b>{round(sum(p['relevance'] for p in PAPERS)/len(PAPERS), 1)}</b>Average relevance</div>
      <div class="stat"><b>{sum(1 for p in PAPERS if p['relevance'] >= 85)}</b>High-fit papers</div>
      <div class="stat"><b>{sum(1 for p in PAPERS if p['pdf_status'].startswith('open'))}</b>Open PDFs</div>
    </section>
    <section id="papers">{''.join(cards)}</section>
  </main>
  <script>
    const papers = {data_json};
    const stateKey = "trajectory-smoothing-review-state-v1";
    const state = JSON.parse(localStorage.getItem(stateKey) || "{{}}");
    const save = () => localStorage.setItem(stateKey, JSON.stringify(state));
    function unique(field) {{ return [...new Set(papers.map(p => p[field]))].sort(); }}
    function fillSelect(id, values) {{
      const el = document.getElementById(id);
      values.forEach(v => {{
        const opt = document.createElement("option");
        opt.value = v; opt.textContent = v; el.appendChild(opt);
      }});
    }}
    fillSelect("themeFilter", unique("theme"));
    fillSelect("venueFilter", unique("venue_type"));
    fillSelect("yearFilter", unique("year"));
    let selectedOnly = false;
    document.querySelectorAll(".stars").forEach(box => {{
      const id = box.dataset.paper;
      state[id] ||= {{ selected: false, stars: 0 }};
      for (let i = 1; i <= 5; i++) {{
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = "★";
        b.title = `${{i}} star${{i > 1 ? "s" : ""}}`;
        b.onclick = () => {{ state[id].stars = i; save(); renderState(); }};
        box.appendChild(b);
      }}
    }});
    document.querySelectorAll("input[type='checkbox'][data-paper]").forEach(cb => {{
      const id = cb.dataset.paper;
      cb.checked = !!state[id]?.selected;
      cb.onchange = () => {{ state[id] ||= {{ stars: 0 }}; state[id].selected = cb.checked; save(); filterCards(); }};
    }});
    function renderState() {{
      document.querySelectorAll(".stars").forEach(box => {{
        const rating = state[box.dataset.paper]?.stars || 0;
        [...box.children].forEach((b, idx) => b.classList.toggle("active", idx < rating));
      }});
    }}
    function filterCards() {{
      const theme = document.getElementById("themeFilter").value;
      const venue = document.getElementById("venueFilter").value;
      const year = document.getElementById("yearFilter").value;
      const score = Number(document.getElementById("scoreFilter").value || 0);
      document.querySelectorAll(".paper-card").forEach(card => {{
        const id = card.id;
        const show = (!theme || card.dataset.theme === theme)
          && (!venue || card.dataset.venue === venue)
          && (!year || card.dataset.year === year)
          && Number(card.dataset.score) >= score
          && (!selectedOnly || state[id]?.selected);
        card.classList.toggle("hidden", !show);
      }});
    }}
    ["themeFilter", "venueFilter", "yearFilter", "scoreFilter"].forEach(id => document.getElementById(id).addEventListener("input", filterCards));
    document.getElementById("selectedOnly").onclick = () => {{
      selectedOnly = !selectedOnly;
      document.getElementById("selectedOnly").textContent = selectedOnly ? "Show all papers" : "Show selected only";
      filterCards();
    }};
    renderState();
    filterCards();
  </script>
</body>
</html>
"""
    (ROOT / "paper_analysis.html").write_text(content, encoding="utf-8")


def bibtex_entries() -> str:
    entries = []
    for p in PAPERS:
        authors = " and ".join(a.strip() for a in p["authors"].split(";"))
        typ = "article" if p["venue_type"] in {"Journal", "Journal / Preprint", "Magazine / Preprint", "Survey / Preprint"} else "inproceedings" if "Workshop" in p["venue_type"] or "Conference" in p["venue_type"] else "misc"
        fields = {
            "author": authors,
            "title": p["title"],
            "year": str(p["year"]),
            "doi": p["doi"],
            "url": p["source_url"],
            "note": p["venue"],
        }
        if typ == "article":
            fields["journal"] = p["venue"]
        elif typ == "inproceedings":
            fields["booktitle"] = p["venue"]
        body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items())
        entries.append(f"@{typ}{{{p['bibkey']},\n{body}\n}}")
    return "\n\n".join(entries)


def tex_related_work_subsection() -> str:
    return r"""\subsection{Trajectory Smoothing and Stop Avoidance}
% EN: Review velocity planning, energy-aware control, control barrier functions, and smooth crossing strategies.
% CN: 回顾速度规划、能耗优化、控制屏障函数和平滑通过路口的方法。
\begin{addedtodayblock}
Recent work shows that intersection efficiency depends not only on the discrete passing order but also on whether the assigned order can be executed by dynamically feasible vehicle trajectories. Graph-based CAV cooperation methods model crossing, diverging, converging, and reachability conflicts before selecting a passing order, which is close in spirit to representing conflict zones as shared scheduling resources \cite{chen2021conflictfree,chen2021lanechanging}. Priority-aware resequencing further shows that strict FCFS/FIFO decision orders can be relaxed through replanning while still passing target times to a lower-level optimal controller \cite{chalaki2021priority}. These studies motivate the scheduling layer in this paper, but they usually rely on handcrafted graph algorithms or analytic resequencing rather than an offline-trained graph policy.

Trajectory-level studies address the complementary question of how a vehicle should move after a desired crossing time, phase, or maneuver has been selected. Eco-driving and eco-approach controllers use reinforcement learning, Pontryagin-minimum-principle solutions, or hybrid rule-learning structures to reduce energy consumption, delay, and unnecessary acceleration near intersections \cite{bai2022hybrid,jiang2023ecodriving,lakshmanan2022cooperative,dong2023overtaking}. These papers support the use of stop count, acceleration variation, and energy proxy metrics in the evaluation, because stop-line waiting is not merely a delay phenomenon but also changes the smoothness and energy profile of the vehicle trajectory.

Safety-oriented trajectory planning adds constraints that the high-level schedule alone cannot guarantee. Predictive-control and spatial-domain formulations derive trajectories under rear-end, crossing, merging, diverging, and mixed-traffic uncertainty constraints \cite{mahbub2022safety,zhao2025spatial}. Learning-based AIM approaches can improve flexibility and travel time, but recent work also emphasizes that learned decisions need explicit safety evaluation or filtering, such as uncertainty-aware high-order control barrier functions \cite{luo2023realtime,yu2025uncertainty,cederle2024distributed,li2023dhal}. A broad CAV-control survey similarly identifies trajectory tracking, collaborative control, safety, comfort, and energy saving as coupled requirements rather than independent design goals \cite{liu2023systematic}.

The proposed framework follows this schedule-to-trajectory view. The high-level JSSP/RL scheduler determines the conflict-zone order and target entry times, while the low-level smoother treats those times as references to be tracked under speed, acceleration, jerk, and safety constraints. If the smoother cannot track the assigned reservations without violating collision-avoidance or comfort bounds, it reports infeasibility and triggers replanning or conservative stop-line fallback. This feedback interface is the main distinction from methods that optimize only the passing order or only the vehicle trajectory in isolation.
\end{addedtodayblock}"""


def write_auxiliary_outputs() -> None:
    (ROOT / "selected_papers_summary.md").write_text(
        "# Selected Core Papers\n\n" + "\n".join(paper_markdown(p) for p in PAPERS),
        encoding="utf-8",
    )
    (ROOT / "papers.json").write_text(json.dumps(PAPERS, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "bibtex_entries.bib").write_text(bibtex_entries() + "\n", encoding="utf-8")
    (ROOT / "related_work_replacement.tex").write_text(tex_related_work_subsection() + "\n", encoding="utf-8")
    download_lines = [
        "#!/usr/bin/env python3",
        "from pathlib import Path",
        "from urllib.request import urlretrieve",
        "PDF_DIR = Path(__file__).resolve().parent / 'pdfs'",
        "PDF_DIR.mkdir(exist_ok=True)",
        f"PAPERS = {json.dumps([(p['id'], p['bibkey'], p['pdf_url']) for p in PAPERS], indent=2)}",
        "for pid, key, url in PAPERS:",
        "    target = PDF_DIR / f'{pid}_{key}.pdf'",
        "    if target.exists() and target.stat().st_size > 1000:",
        "        print(f'skip {target.name}')",
        "        continue",
        "    print(f'download {target.name} <- {url}')",
        "    urlretrieve(url, target)",
    ]
    (ROOT / "download_pdfs.py").write_text("\n".join(download_lines) + "\n", encoding="utf-8")
    os.chmod(ROOT / "download_pdfs.py", 0o755)


def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    write_search_protocol()
    write_review_template()
    write_xlsx()
    write_html()
    write_auxiliary_outputs()
    print(f"Built literature artifacts in {ROOT}")


if __name__ == "__main__":
    main()
