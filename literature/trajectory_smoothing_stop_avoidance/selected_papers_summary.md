# Selected Core Papers

### P01. A Priority-Aware Replanning and Resequencing Framework for Coordination of Connected and Automated Vehicles

- **Authors:** Behdad Chalaki; Andreas A. Malikopoulos
- **Year / venue:** 2021, arXiv preprint
- **Source:** https://arxiv.org/abs/2109.05573
- **PDF:** https://arxiv.org/pdf/2109.05573
- **Theme:** Scheduling/resequencing + optimal control
- **Project relevance:** 94/100
- **Technical method:** Event-driven replanning and priority-aware resequencing layered on decentralized CAV optimal control at a signal-free intersection.
- **Stop avoidance / smoothing:** The lower-level optimal-control trajectory is constructed so vehicles can conserve momentum rather than stop at the intersection when a feasible exit time exists.
- **Collision avoidance / safety:** Uses rear-end and lateral safety constraints around conflict points, with replanning when disturbances change feasibility.
- **Validation:** Numerical simulation of signal-free intersection coordination under resequencing and replanning.
- **Limitations:** Assumes connected automated vehicles, known paths, and simplified dynamics; the paper is closer to resequencing theory than to learned graph scheduling.
- **How it supports this project:** Directly supports this project's hierarchy: a high-level sequence or schedule provides target times, and a low-level controller checks executable motion.

### P02. Conflict-free Cooperation Method for Connected and Automated Vehicles at Unsignalized Intersections: Graph-based Modeling and Optimality Analysis

- **Authors:** Chaoyi Chen; Qing Xu; Mengchi Cai; Jiawei Wang; Jianqiang Wang; Biao Xu; Keqiang Li
- **Year / venue:** 2021, Transportation Research Part C: Emerging Technologies / arXiv version
- **Source:** https://arxiv.org/abs/2107.07179
- **PDF:** https://arxiv.org/pdf/2107.07179
- **Theme:** Graph conflict modeling + passing order
- **Project relevance:** 92/100
- **Technical method:** Models trajectory conflicts as a conflict directed graph and coexisting undirected graph; solves passing order through improved depth-first spanning tree and minimum clique cover methods.
- **Stop avoidance / smoothing:** Optimizes evacuation time and average delay, using distributed control to reduce idling near the stop line.
- **Collision avoidance / safety:** Conflict-free graph edges represent crossing, diverging, converging, and reachability conflicts before scheduling.
- **Validation:** Traffic simulations over varying vehicle counts and volumes; reports efficiency and fuel-economy improvements.
- **Limitations:** Mostly longitudinal control, ideal communication, and no lane changing in this paper's base formulation.
- **How it supports this project:** Strong support for representing intersection conflicts as typed graph relations, similar to the operation graph in this manuscript.

### P03. Cooperation Method of Connected and Automated Vehicles at Unsignalized Intersections: Lane Changing and Arrival Scheduling

- **Authors:** Chaoyi Chen; Mengchi Cai; Jiawei Wang; Kai Li; Qing Xu; Jianqiang Wang; Keqiang Li
- **Year / venue:** 2021, arXiv preprint
- **Source:** https://arxiv.org/abs/2109.14175
- **PDF:** https://arxiv.org/pdf/2109.14175
- **Theme:** Lane changing + arrival scheduling
- **Project relevance:** 82/100
- **Technical method:** Two-stage framework decoupling lateral lane assignment/path planning from graph-based arrival scheduling with minimum clique cover.
- **Stop avoidance / smoothing:** Improves traffic efficiency by choosing target lanes and arrival schedules that avoid unnecessary queuing.
- **Collision avoidance / safety:** Conflict-free arrival scheduling and formation-control assumptions prevent incompatible movements.
- **Validation:** Numerical simulations for different vehicle counts and traffic volumes.
- **Limitations:** arXiv note reports text overlap with the authors' earlier graph-based paper; use mainly for lane-changing extension context.
- **How it supports this project:** Useful for discussing route-template/lane-choice extensions beyond the current fixed-route JSSP formulation.

### P04. Real-time Cooperative Vehicle Coordination at Unsignalized Road Intersections

- **Authors:** Jiping Luo; Tingting Zhang; Rui Hao; Donglin Li; Chunsheng Chen; Zhenyu Na; Qinyu Zhang
- **Year / venue:** 2023, IEEE Transactions on Intelligent Transportation Systems
- **Source:** https://arxiv.org/abs/2205.01278
- **PDF:** https://arxiv.org/pdf/2205.01278
- **Theme:** DRL cooperative trajectory optimization
- **Project relevance:** 91/100
- **Technical method:** Formulates unified cooperative trajectory optimization for unsignalized intersections and solves the sequential decision problem with TD3.
- **Stop avoidance / smoothing:** Optimizes throughput and continuous flow, reducing delay compared with conservative coordination.
- **Collision avoidance / safety:** Safety and long-term stability constraints are embedded in the cooperative trajectory optimization framework.
- **Validation:** Simulation and practical experiments; authors report millisecond-scale computation and scalability with lane count.
- **Limitations:** Centralized control-authority handoff and DRL policy behavior may be difficult to certify in mixed traffic.
- **How it supports this project:** Shows why learned policies are attractive for online intersection coordination but need a structured safety/smoothing interface.

### P05. Hybrid Reinforcement Learning-Based Eco-Driving Strategy for Connected and Automated Vehicles at Signalized Intersections

- **Authors:** Zhengwei Bai; Peng Hao; Wei Shangguan; Baigen Cai; Matthew J. Barth
- **Year / venue:** 2022, IEEE Transactions on Intelligent Transportation Systems
- **Source:** https://arxiv.org/abs/2201.07833
- **PDF:** https://arxiv.org/pdf/2201.07833
- **Theme:** Eco-driving + hybrid RL
- **Project relevance:** 86/100
- **Technical method:** Combines a rule-based driving manager, V2I/vision features, and RL to generate longitudinal and lateral eco-driving actions.
- **Stop avoidance / smoothing:** Targets energy and travel-time reduction by smoothing approach behavior at signalized intersections.
- **Collision avoidance / safety:** Mixed-traffic policy includes rule-based safety management around surrounding vehicles.
- **Validation:** Unity-based mixed-traffic intersection simulation; reports 12.70 percent energy reduction and 11.75 percent travel-time saving against a model-based eco-driving baseline.
- **Limitations:** Signalized setting and policy-level action output differ from a scheduler-to-smoother architecture.
- **How it supports this project:** Supports the argument that stop-and-go reduction and energy-aware smoothing are important low-level objectives.

### P06. Eco-driving for Electric Connected Vehicles at Signalized Intersections: A Parameterized Reinforcement Learning Approach

- **Authors:** Xia Jiang; Jian Zhang; Dan Li
- **Year / venue:** 2023, Journal article related DOI / arXiv version
- **Source:** https://arxiv.org/abs/2206.12065
- **PDF:** https://arxiv.org/pdf/2206.12065
- **Theme:** Electric CV eco-driving + parameterized RL
- **Project relevance:** 83/100
- **Technical method:** Parameterized RL combines model-based car-following, lane-changing policy, and learned longitudinal/lateral decisions.
- **Stop avoidance / smoothing:** Learns energy-saving actions around signalized intersections without interrupting surrounding HDVs.
- **Collision avoidance / safety:** Safety is handled through model-based car-following and lane-changing constraints around human-driven vehicles.
- **Validation:** SUMO evaluation from single-vehicle and flow perspectives.
- **Limitations:** Signalized intersections and electric connected vehicles rather than fully signal-free autonomous scheduling.
- **How it supports this project:** Provides a SUMO-compatible example of energy and stop reduction metrics for the experimental section.

### P07. Cooperative Control in Eco-Driving of Electric Connected and Autonomous Vehicles in an Un-Signalized Urban Intersection

- **Authors:** Vinith Kumar Lakshmanan; Antonio Sciarretta; Ouafae El Ganaoui-Mourlan
- **Year / venue:** 2022, AAC 2022 submission / arXiv version
- **Source:** https://arxiv.org/abs/2206.12360
- **PDF:** https://arxiv.org/pdf/2206.12360
- **Theme:** Eco-driving optimal speed profile
- **Project relevance:** 81/100
- **Technical method:** Single-level eco-driving optimization solved with Pontryagin's Minimum Principle for electric CAV speed profiles at an unsignalized intersection.
- **Stop avoidance / smoothing:** Focuses directly on optimal speed profiles that reduce energy use and avoid inefficient stop-and-go behavior.
- **Collision avoidance / safety:** Analytical conflict cases and cooperation levels encode interaction safety among CAVs.
- **Validation:** Simulation comparison of cooperative and non-cooperative eco-driving against IDM baseline.
- **Limitations:** Narrower single-vehicle/eco-driving emphasis; less detail on high-level scheduling.
- **How it supports this project:** Supports the smoothing objective terms for acceleration, energy proxy, and stop avoidance.

### P08. Safety-Aware and Data-Driven Predictive Control for Connected Automated Vehicles at a Mixed Traffic Signalized Intersection

- **Authors:** A. M. Ishtiaque Mahbub; Viet-Anh Le; Andreas A. Malikopoulos
- **Year / venue:** 2022, arXiv preprint
- **Source:** https://arxiv.org/abs/2203.05739
- **PDF:** https://arxiv.org/pdf/2203.05739
- **Theme:** Data-driven predictive control + mixed traffic safety
- **Project relevance:** 78/100
- **Technical method:** Finite-horizon predictive control uses recursive least squares to estimate preceding HDV behavior in real time.
- **Stop avoidance / smoothing:** Smooths CAV response near yellow/red phases while avoiding overly conservative braking behind HDVs.
- **Collision avoidance / safety:** Prioritizes rear-end collision avoidance when preceding human-driven vehicles approach signal changes.
- **Validation:** Numerical simulation and robustness analysis.
- **Limitations:** Signalized and rear-end-focused rather than conflict-zone scheduling across all movements.
- **How it supports this project:** Useful for fallback and mixed-traffic safety discussion, especially when predicted trajectories deviate.

### P09. Overtaking-enabled Eco-approach Control at Signalized Intersections for Connected and Automated Vehicles

- **Authors:** Haoxuan Dong; Weichao Zhuang; Guoyuan Wu; Zhaojian Li; Guodong Yin; Ziyou Song
- **Year / venue:** 2023, arXiv preprint
- **Source:** https://arxiv.org/abs/2306.09736
- **PDF:** https://arxiv.org/pdf/2306.09736
- **Theme:** Eco-approach + relaxed FIFO
- **Project relevance:** 84/100
- **Technical method:** Receding-horizon two-stage control: dynamic-programming lane optimization followed by PMP speed trajectory optimization.
- **Stop avoidance / smoothing:** Relaxes FIFO queuing at signalized intersections to reduce driving cost, energy consumption, and delay.
- **Collision avoidance / safety:** Handles dynamic disturbance from preceding vehicles and lane-choice constraints.
- **Validation:** Extensive simulations report average driving-cost improvements over constant-speed and regular eco-approach baselines.
- **Limitations:** Signalized intersection and overtaking/lane planning assumptions are outside the current fixed-route JSSP scope.
- **How it supports this project:** Supports the critique that FCFS/FIFO can be suboptimal and that speed smoothing should be coupled to sequencing.

### P10. Real-World Evaluation of Two Cooperative Intersection Management Approaches

- **Authors:** Marvin Klimke; Max Bastian Mertens; Benjamin Volz; Michael Buchholz
- **Year / venue:** 2026, IEEE Intelligent Transportation Systems Magazine (accepted)
- **Source:** https://arxiv.org/abs/2403.16478
- **PDF:** https://arxiv.org/pdf/2403.16478
- **Theme:** Real-world cooperative intersection management
- **Project relevance:** 90/100
- **Technical method:** Compares multi-scenario prediction and graph-based reinforcement learning approaches in mixed-traffic simulation and real drives.
- **Stop avoidance / smoothing:** Reports substantial reductions in crossing time and number of stops for cooperative maneuver planning.
- **Collision avoidance / safety:** Evaluates criticality metrics while operating with prototype connected automated vehicles in public traffic.
- **Validation:** Novel mixed-traffic simulation framework plus real-world prototype connected automated vehicle drives.
- **Limitations:** Focuses on cooperative maneuver planning evaluation, not a JSSP formulation.
- **How it supports this project:** Excellent evidence that stop count is a practical metric and that real-world mixed traffic should be considered in future validation.

### P11. A Spatial-Domain Coordinated Control Method for CAVs at Unsignalized Intersections Considering Motion Uncertainty

- **Authors:** Tong Zhao; Nikolce Murgovski; Baigen Cai; Wei ShangGuan
- **Year / venue:** 2025, arXiv preprint
- **Source:** https://arxiv.org/abs/2412.04290
- **PDF:** https://arxiv.org/pdf/2412.04290
- **Theme:** Spatial-domain robust trajectory planning
- **Project relevance:** 92/100
- **Technical method:** Transforms coordinated control into a spatial-domain nonlinear program with unified linear collision-avoidance constraints and real-time iteration.
- **Stop avoidance / smoothing:** Generates smooth trajectories under state/control constraints, avoiding unnecessary braking where robust constraints permit.
- **Collision avoidance / safety:** Handles crossing, following, merging, and diverging conflicts under path and speed uncertainty of HDVs.
- **Validation:** Simulation case studies; reported RTI computation reduction by orders of magnitude with small optimality loss.
- **Limitations:** Optimization-heavy; not a learned scheduler, and publication venue beyond arXiv not verified.
- **How it supports this project:** Very strong for the smoother's feasibility and robust collision-avoidance constraints.

### P12. Uncertainty-Aware Safety-Critical Decision and Control for Autonomous Vehicles at Unsignalized Intersections

- **Authors:** Ran Yu; Zhuoren Li; Lu Xiong; Wei Han; Bo Leng
- **Year / venue:** 2025, arXiv preprint
- **Source:** https://arxiv.org/abs/2505.19939
- **PDF:** https://arxiv.org/pdf/2505.19939
- **Theme:** Uncertainty-aware safe RL + HOCBF
- **Project relevance:** 84/100
- **Technical method:** Risk-aware ensemble distributional RL estimates policy uncertainty, then a high-order control barrier function acts as a safety filter.
- **Stop avoidance / smoothing:** Balances safety and traffic efficiency by switching between flexible RL behavior and conservative HOCBF intervention.
- **Collision avoidance / safety:** HOCBF safety filter dynamically adjusts constraints using joint uncertainty in unsignalized-intersection tasks.
- **Validation:** Simulation tests on multiple unsignalized-intersection tasks against safety and efficiency baselines.
- **Limitations:** Single-agent urban autonomous-driving framing rather than centralized conflict-zone scheduling.
- **How it supports this project:** Supports adding CBF/HOCBF safety filters or fallback logic to learned policies.

### P13. A Systematic Survey of Control Techniques and Applications in Connected and Automated Vehicles

- **Authors:** Wei Liu; Min Hua; Zhiyun Deng; Zonglin Meng; Yanjun Huang; Chuan Hu; Shunhui Song; Letian Gao; Changsheng Liu; Bin Shuai; Amir Khajepour; Lu Xiong; Xin Xia
- **Year / venue:** 2023, arXiv survey
- **Source:** https://arxiv.org/abs/2303.05665
- **PDF:** https://arxiv.org/pdf/2303.05665
- **Theme:** CAV control survey
- **Project relevance:** 72/100
- **Technical method:** Systematic survey from vehicle state estimation and trajectory tracking to collaborative CAV control applications.
- **Stop avoidance / smoothing:** Frames comfort, energy saving, and transportation efficiency as central CAV control goals.
- **Collision avoidance / safety:** Reviews vehicle-control approaches relevant to safety and collaborative control.
- **Validation:** Literature survey rather than original experiments.
- **Limitations:** Broad CAV control overview; not intersection-smoothing specific.
- **How it supports this project:** Useful context citation for why trajectory tracking, collaborative control, safety, comfort, and energy belong together.

### P14. A Distributed Approach to Autonomous Intersection Management via Multi-Agent Reinforcement Learning

- **Authors:** Matteo Cederle; Marco Fabris; Gian Antonio Susto
- **Year / venue:** 2024, ATT 2024 Workshop, CEUR-WS Vol. 3813
- **Source:** https://arxiv.org/abs/2405.08655
- **PDF:** https://arxiv.org/pdf/2405.08655
- **Theme:** Distributed MARL for AIM
- **Project relevance:** 70/100
- **Technical method:** Distributed multi-agent RL for autonomous intersection management using 3D surround-view assumptions and prioritized scenario replay.
- **Stop avoidance / smoothing:** Improves benchmark metrics in SMARTS, implying smoother flow through decentralized decisions.
- **Collision avoidance / safety:** Aims for accurate decentralized navigation without a central server; safety is evaluated through simulation metrics.
- **Validation:** SMARTS virtual environment; accepted at ATT 2024 and available through CEUR-WS.
- **Limitations:** Workshop paper; not focused on explicit trajectory smoothing or formal safety constraints.
- **How it supports this project:** Useful contrast to the proposed centralized JSSP/RL rollout, showing distributed AIM as an alternative branch.

### P15. D-HAL: Distributed Hierarchical Adversarial Learning for Multi-Agent Interaction in Autonomous Intersection Management

- **Authors:** Guanzhou Li; Jianping Wu; Yujing He
- **Year / venue:** 2023, arXiv preprint
- **Source:** https://arxiv.org/abs/2303.02630
- **PDF:** https://arxiv.org/pdf/2303.02630
- **Theme:** Distributed hierarchical learning for AIM
- **Project relevance:** 73/100
- **Technical method:** Non-RL adversarial actor/discriminator framework evaluates immediate interaction and final trajectory quality for multi-agent AIM.
- **Stop avoidance / smoothing:** Targets reduced travel time and smoother interaction outcomes compared with distributed learning baselines.
- **Collision avoidance / safety:** Immediate and final discriminators score interaction safety and trajectory outcomes.
- **Validation:** Four-way six-lane intersection experiments against state-of-the-art methods.
- **Limitations:** Learning framework lacks explicit optimization/smoothing formulation and formal safety guarantees.
- **How it supports this project:** Useful for explaining why learned interaction policies must still be checked by a low-level feasibility/safety layer.
