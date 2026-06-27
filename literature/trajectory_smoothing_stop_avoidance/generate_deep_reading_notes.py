#!/usr/bin/env python3
"""Generate bilingual deep-reading notes for the selected PDF collection.

The generator intentionally stores structured synthesis rather than extracted
paper text. PDF extraction is used for page counts and section/source anchors so
each note remains tied to the original article without reproducing it.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
PDF_DIR = ROOT / "pdfs"
OUTPUT_ROOT = ROOT / "deep_reading_notes"
PAPERS_JSON = ROOT / "papers.json"


@dataclass(frozen=True)
class InteractiveSpec:
    label_zh: str
    label_en: str
    min_value: float
    max_value: float
    default: float
    unit: str
    response_zh: str
    response_en: str


def tex_escape(text: Any) -> str:
    """Escape text for LaTeX while preserving CJK characters."""
    s = "" if text is None else str(text)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in s)


def slug_for(paper: dict[str, Any]) -> str:
    return f"{paper['id']}_{paper['bibkey']}"


def find_pdf(paper: dict[str, Any]) -> Path:
    matches = sorted(PDF_DIR.glob(f"{paper['id']}_*.pdf"))
    if not matches:
        raise FileNotFoundError(f"No PDF found for {paper['id']}")
    return matches[0]


def normalize_heading(line: str) -> str:
    line = re.sub(r"\s+", " ", line).strip()
    line = line.replace(" I NTRODUCTION", " INTRODUCTION")
    line = line.replace(" P ROBLEM", " PROBLEM")
    line = line.replace(" M ETHODOLOGY", " METHODOLOGY")
    line = line.replace(" S IMULATION", " SIMULATION")
    line = line.replace(" C ONCLUSION", " CONCLUSION")
    line = line.replace(" C ONCLUDING", " CONCLUDING")
    line = line.replace(" -", "-")
    return line


def is_probable_heading(line: str) -> bool:
    s = normalize_heading(line)
    if len(s) < 4 or len(s) > 120:
        return False
    patterns = [
        r"^Abstract$",
        r"^[IVX]+\.\s+.+",
        r"^\d+\.?\s+[A-Z][A-Za-z0-9\- /:,]{4,}",
        r"^\d+\.\d+\.?\s+[A-Z][A-Za-z0-9\- /:,]{4,}",
    ]
    if any(re.match(p, s) for p in patterns):
        return True
    return s in {
        "1 Introduction",
        "1. Introduction",
        "2 Literature Review",
        "3 Methodology",
        "6 CONCLUSION",
    }


def extract_pdf_facts(pdf: Path) -> dict[str, Any]:
    reader = PdfReader(str(pdf))
    headings: list[dict[str, Any]] = []
    figure_refs = 0
    table_refs = 0
    equation_cues = 0
    seen: set[str] = set()

    for page_idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        figure_refs += len(re.findall(r"\b(Fig\.|Figure)\s*\d+", text))
        table_refs += len(re.findall(r"\b(Table)\s*[IVX0-9]+", text))
        equation_cues += len(re.findall(r"\([0-9]{1,2}\)", text))
        for raw in text.splitlines():
            h = normalize_heading(raw)
            key = h.lower()
            if is_probable_heading(h) and key not in seen:
                headings.append({"heading": h, "page": page_idx})
                seen.add(key)

    def pick_anchor(keywords: tuple[str, ...], fallback_index: int) -> dict[str, Any]:
        for item in headings:
            h = item["heading"].lower()
            if any(k in h for k in keywords):
                return item
        if headings:
            return headings[min(fallback_index, len(headings) - 1)]
        return {"heading": "Title / Abstract", "page": 1}

    anchors = [
        pick_anchor(("introduction", "abstract"), 0),
        pick_anchor(("method", "framework", "problem", "formulation", "algorithm"), 1),
        pick_anchor(("simulation", "experiment", "result", "evaluation", "conclusion"), 2),
    ]

    return {
        "pdf_file": pdf.name,
        "page_count": len(reader.pages),
        "section_headings": headings[:18],
        "source_anchors": anchors,
        "figure_reference_count": figure_refs,
        "table_reference_count": table_refs,
        "equation_reference_count": equation_cues,
    }


DETAILS: dict[str, dict[str, Any]] = {
    "P01": {
        "method_family": "Priority-aware resequencing + decentralized optimal control / 优先级重排序与分散最优控制",
        "core_question_zh": "当车辆到达扰动使原始通行序列不再高效或可行时，如何在不牺牲安全约束的前提下快速重排序并生成可执行轨迹？",
        "core_question_en": "How can an intersection manager resequence disturbed arrivals while preserving safety and low-level trajectory feasibility?",
        "innovation_rating": "强相关但中等创新：把 resequencing 明确嵌入 CAV 最优控制闭环，贡献主要在系统架构和事件触发逻辑。",
        "formula_name": "双积分车辆模型与能量型最优控制 / Double-integrator vehicle model with energy-like optimal control",
        "formula": r"\min_{u_i(\cdot),\,t_i^f}\; J_i=\frac{1}{2}\int_{t_i^0}^{t_i^f}u_i(t)^2\,dt,\quad \dot p_i(t)=v_i(t),\quad \dot v_i(t)=u_i(t)",
        "symbols": [
            ("i", "车辆索引", "vehicle index", "把多车协调拆成单车最优控制子问题"),
            ("p_i(t)", "沿路径位置", "path-coordinate position", "描述车辆是否接近/离开冲突区"),
            ("v_i(t)", "速度", "speed", "连接安全间距、通行时间与停止避免"),
            ("u_i(t)", "加速度控制", "acceleration control", "优化变量，平滑性和能耗代理"),
            ("t_i^f", "车辆离开控制区时间", "terminal exit time", "高层排序传给低层控制器的关键接口"),
        ],
        "algorithm_zh": "高层监测车辆进入、延误和可行性破坏；当扰动出现时，按照优先级规则更新局部通行序列，再把目标离开时间传给每辆车的解析/数值最优控制器。低层控制器检查速度、加速度、追尾和横向冲突约束是否可执行。",
        "algorithm_en": "The upper layer detects event-triggered infeasibility, resequences vehicles under priority rules, and sends target exit times to decentralized optimal controllers that enforce motion and safety constraints.",
        "stability_zh": "实时性来自局部事件触发与低维车辆模型；安全性依赖硬约束而非学习策略。它不证明全局最优，但把全局重排问题约束在小窗口内，适合在线运行。",
        "stability_en": "Real-time behavior comes from event-triggered local resequencing and low-dimensional dynamics; safety is constraint-based, while global optimality is intentionally relaxed.",
        "assumptions": [
            "所有车辆为联网自动驾驶车辆 (connected automated vehicles, CAVs)，且路径已知。",
            "车辆动力学可由简化双积分模型 (double-integrator model) 充分描述。",
            "通信、定位和控制执行误差较小，扰动可被及时探测。",
        ],
        "baselines": "通常与固定先来先服务/不重排序 (FCFS / no resequencing) 策略比较，重点观察扰动后恢复效率。",
        "metrics": "通行时间 (travel time)、延误 (delay)、停止次数 (number of stops)、控制能量代理 (control effort) 和安全约束违反。",
        "ablation": "论文更像机制验证而非完整消融；最应补充的是关闭优先级、关闭事件触发和扩大重排窗口的对比。",
        "limitations": [
            "对全 CAV 环境依赖强，混合交通中人类驾驶车辆 (HDVs) 会破坏可行性假设。",
            "优先级规则可能引入公平性问题，长期低优先级车流需要饥饿避免机制。",
            "简化动力学忽略执行器延迟、轮胎约束和感知误差累积。",
        ],
        "extensions": [
            "把固定优先级扩展为学习型优先级函数 (learned priority function)，并加入公平性正则。",
            "将重排序窗口映射为 JSSP machine queue，用图神经网络 (GNN) 预测候选交换收益。",
            "在低层加入鲁棒 MPC 或 CBF 安全过滤器，处理通信延迟和轨迹预测误差。",
        ],
        "interactive": InteractiveSpec("重排序窗口大小", "Resequencing window size", 2, 12, 5, "veh", "窗口增大通常降低延误但提高计算量，并可能增加局部公平性风险。", "A larger window usually reduces delay but increases computation and fairness risk."),
    },
    "P02": {
        "method_family": "Conflict graph + optimal passing order / 冲突图与最优通行顺序",
        "core_question_zh": "如何把无信号交叉口中复杂的相交、跟驰、合流和分流关系转化为可求解的图排序问题？",
        "core_question_en": "How can heterogeneous vehicle conflicts at an unsignalized intersection be encoded as graph relations that yield a conflict-free passing order?",
        "innovation_rating": "较强：图建模把交通冲突类型显式化，便于和 JSSP 的机器冲突/工序约束建立同构关系。",
        "formula_name": "冲突图与排序目标 / Conflict graph and sequencing objective",
        "formula": r"G=(V,E_d,E_u),\quad \min_{\pi}\; C_{\max}(\pi)=\max_{i\in V} t_i^{out}\quad \text{s.t.}\; (i,j)\in E_d\Rightarrow i\prec_\pi j",
        "symbols": [
            ("V", "车辆节点集合", "vehicle-node set", "每辆车对应一个调度实体"),
            ("E_d", "有向冲突/可达边", "directed conflict/reachability edges", "表达必须先后通过的约束"),
            ("E_u", "无向共存/冲突边", "undirected coexistence/conflict edges", "表达是否可同批通过或需分组"),
            ("pi", "通行序列", "passing permutation", "调度算法的核心决策变量"),
            ("C_max", "最大清空时间", "makespan / evacuation time", "衡量路口整体效率"),
        ],
        "algorithm_zh": "先依据几何轨迹和时间可达性构建冲突有向图与共存无向图；再用改进深度优先生成树和最小团覆盖等图算法求通行组与顺序；最后由分布式控制保证每辆车按序到达冲突区。",
        "algorithm_en": "The method builds directed and undirected graph relations from trajectory conflicts, solves groups and orders with graph algorithms, and executes the resulting order via distributed vehicle control.",
        "stability_zh": "图约束先把不安全组合排除，控制层只需执行已筛选的顺序。实时性取决于图规模和团覆盖求解，但比直接连续优化全车轨迹更结构化。",
        "stability_en": "Safety is front-loaded into graph constraints; tractability improves because the continuous-control layer receives a filtered sequence rather than solving all interactions jointly.",
        "assumptions": [
            "车辆轨迹模板和冲突点可提前计算。",
            "车辆遵守分配的通行顺序，通信近似理想。",
            "主要聚焦纵向控制，横向变道不是核心问题。",
        ],
        "baselines": "常见基准包括 FCFS、交通灯控制、无协同控制和其他图排序策略。",
        "metrics": "平均延误 (average delay)、总清空时间 (evacuation time)、吞吐量 (throughput)、燃油/能耗代理和停车次数。",
        "ablation": "图关系本身有可解释性，但仍需更系统地拆分：仅有向图、仅无向图、不同团覆盖策略和不同交通流密度下的鲁棒性。",
        "limitations": [
            "图构造依赖精确几何和预测，异常驾驶会导致边集失真。",
            "团覆盖/排序在大规模密集车流下可能成为瓶颈。",
            "模型偏重全 CAV 场景，对低渗透率混合交通支持不足。",
        ],
        "extensions": [
            "把图边类型作为异构图 (heterogeneous graph) 特征，训练 GNN 调度器。",
            "将最小团覆盖与 JSSP disjunctive graph 融合，建立可证明安全的调度层。",
            "引入不确定边权，做分布鲁棒通行排序 (distributionally robust sequencing)。",
        ],
        "interactive": InteractiveSpec("冲突边密度", "Conflict-edge density", 0.1, 0.9, 0.45, "", "边密度升高会减少可并行通行组，通常增大清空时间。", "Higher edge density reduces parallel passing groups and increases evacuation time."),
    },
    "P03": {
        "method_family": "Lane assignment + arrival scheduling / 车道分配与到达调度",
        "core_question_zh": "当车辆可以变道或选择目标车道时，如何联合决定路径/车道与无冲突到达时间？",
        "core_question_en": "How should target-lane assignment and conflict-free arrival scheduling be coupled when vehicles may change lanes before the intersection?",
        "innovation_rating": "中等：在 P02 图排序基础上加入横向决策，扩展性有价值，但理论新颖性主要来自组合而非新算法。",
        "formula_name": "联合车道分配与到达时间优化 / Joint lane assignment and arrival scheduling",
        "formula": r"\min_{l_i,t_i}\; \sum_{i\in V}\left(\alpha\,d_i(l_i)+\beta\,|t_i-t_i^{des}|\right)\quad \text{s.t.}\; (i,j)\in E(l)\Rightarrow |t_i-t_j|\ge \tau_{ij}",
        "symbols": [
            ("l_i", "目标车道", "target lane", "横向规划决策变量"),
            ("t_i", "车辆到达冲突区时间", "arrival time at conflict zone", "纵向调度决策变量"),
            ("d_i(l_i)", "变道代价", "lane-changing cost", "衡量横向操作复杂度"),
            ("E(l)", "由车道选择诱导的冲突边集", "lane-induced conflict edges", "说明横向选择会改变调度约束"),
            ("tau_ij", "安全时间间隔", "safety headway", "保证冲突车辆时间分离"),
        ],
        "algorithm_zh": "框架先求多车目标分配与路径规划，再基于最终路径构建冲突图并求到达时间。这样横向变道改变冲突关系，纵向调度再处理被改变后的路口资源竞争。",
        "algorithm_en": "The framework first assigns target lanes/paths, then constructs a conflict graph for those paths and computes a conflict-free arrival schedule.",
        "stability_zh": "分阶段设计提高实时性，但牺牲联合最优性；如果第一阶段车道选择失误，第二阶段只能在较差冲突结构上补救。",
        "stability_en": "The two-stage decomposition is tractable but not globally optimal; poor lane assignment can constrain the downstream scheduler.",
        "assumptions": [
            "车辆可执行规划出的变道动作，周围交通允许形成编队。",
            "车道级地图和目标车道需求已知。",
            "变道安全约束可以被简化成可规划的路径/队形约束。",
        ],
        "baselines": "固定车道策略、无变道调度、FCFS 和基于图的到达调度。",
        "metrics": "平均延误、总行程时间、完成变道比例、冲突避免成功率和交通量敏感性。",
        "ablation": "最关键消融是去掉 lane-changing stage，对比是否真的改善调度；还应测试高密度下变道失败的退化策略。",
        "limitations": [
            "文本与同作者早期图调度工作高度相关，独立贡献需谨慎引用。",
            "横向控制细节和人类驾驶干扰不足。",
            "两阶段解耦可能错过更优的路径-时间联合解。",
        ],
        "extensions": [
            "用双层优化 (bi-level optimization) 同时学习车道选择和 JSSP 排序。",
            "为变道失败设计可恢复调度 (recoverable scheduling)，让路口管理器在线回滚目标车道。",
            "把车道选择看成 route-template selection，扩展当前固定路线假设。",
        ],
        "interactive": InteractiveSpec("可变道车辆比例", "Lane-change-enabled ratio", 0, 1, 0.35, "", "比例增加会提高调度自由度，但过高时变道冲突和局部扰动也会增加。", "More lane-change freedom improves scheduling flexibility but can add lateral conflicts."),
    },
    "P04": {
        "method_family": "TD3 deep reinforcement learning for coordination / TD3 深度强化学习协同控制",
        "core_question_zh": "能否用连续动作深度强化学习直接学习无信号交叉口的实时协同轨迹控制策略？",
        "core_question_en": "Can continuous-control deep reinforcement learning learn real-time cooperative trajectories for unsignalized intersections?",
        "innovation_rating": "较强应用创新：将 TD3 用于统一协同轨迹优化并强调毫秒级推理，但可验证安全仍是短板。",
        "formula_name": "MDP 目标与 TD3 策略优化 / MDP objective and TD3 policy optimization",
        "formula": r"\max_{\pi_\theta}\; \mathbb{E}\left[\sum_{t=0}^{T}\gamma^t r(s_t,a_t)\right],\quad a_t=\pi_\theta(s_t),\quad y=r+\gamma\min_{k=1,2}Q_{\phi_k}(s',\pi_{\bar\theta}(s'))",
        "symbols": [
            ("s_t", "协同状态", "cooperative state", "包含车辆位置、速度和交互信息"),
            ("a_t", "连续控制动作", "continuous action", "通常对应加速度或轨迹控制量"),
            ("r", "奖励函数", "reward", "平衡效率、安全和舒适性"),
            ("gamma", "折扣因子", "discount factor", "决定长期收益权重"),
            ("Q_phi", "评论家网络", "critic network", "估计动作价值并抑制过估计"),
        ],
        "algorithm_zh": "将协同控制表述为连续动作 MDP，TD3 使用双评论家取最小值、延迟 actor 更新和目标策略平滑来提升稳定性。在线执行时只需前向传播策略网络，因而推理很快。",
        "algorithm_en": "The cooperative control problem is cast as a continuous-action MDP; TD3 uses clipped double-Q learning, delayed policy updates, and target smoothing for stable training and fast inference.",
        "stability_zh": "训练稳定性来自 TD3 机制而非形式化安全证明；实时性来自神经网络推理。若状态分布偏移，策略可能给出未认证动作。",
        "stability_en": "TD3 improves learning stability, but safety remains empirical unless wrapped by a constraint layer or safety filter.",
        "assumptions": [
            "训练环境覆盖了测试场景的关键交通分布。",
            "中心协调器能获得足够完整的车辆状态。",
            "奖励函数能充分惩罚碰撞、剧烈加减速和低效率。",
        ],
        "baselines": "传统协同控制、非协同策略、FCFS/规则控制和其他深度强化学习控制器。",
        "metrics": "平均通行时间、吞吐量、延误、速度波动、碰撞/冲突次数和在线计算耗时。",
        "ablation": "应检查奖励项、双评论家、目标策略平滑和安全惩罚各自贡献；若缺少这些消融，审稿时会质疑可解释性。",
        "limitations": [
            "学习策略难以给出严格安全证书。",
            "仿真到真实 (sim-to-real) 分布偏移可能显著。",
            "集中式状态采集和控制权切换在工程落地中成本较高。",
        ],
        "extensions": [
            "在 TD3 actor 后接 CBF/MPC safety shield，形成 learn-then-filter 架构。",
            "把 JSSP 调度作为高层离散动作，TD3 只负责连续轨迹平滑。",
            "用离线强化学习或保守 Q 学习降低在线探索风险。",
        ],
        "interactive": InteractiveSpec("安全奖励权重", "Safety reward weight", 0.1, 5.0, 1.2, "", "权重提高通常降低冲突风险，但过高会造成保守减速和吞吐下降。", "Higher safety reward reduces conflicts but may make the policy conservative."),
    },
    "P05": {
        "method_family": "Hybrid RL eco-driving at signalized intersections / 信号交叉口混合强化学习生态驾驶",
        "core_question_zh": "在信号灯、V2I 信息和混合交通干扰下，如何通过混合规则-学习策略降低能耗和时间损失？",
        "core_question_en": "How can a hybrid rule-learning eco-driving policy reduce energy and travel time under SPaT and mixed-traffic constraints?",
        "innovation_rating": "强应用价值：规则管理器增强 RL 安全性，适合作为轨迹平滑器能耗目标的参考。",
        "formula_name": "能耗-效率-安全复合奖励 / Energy-efficiency-safety reward",
        "formula": r"\max_{\pi}\; \mathbb{E}\sum_t \gamma^t r_t,\quad r_t= -w_e E_t-w_d D_t-w_s \mathbb{I}_{unsafe}-w_a |a_t|",
        "symbols": [
            ("E_t", "瞬时能耗", "instantaneous energy use", "生态驾驶优化主目标"),
            ("D_t", "延误/时间损失", "delay or time loss", "避免单纯省能导致低速拖行"),
            ("I_unsafe", "不安全事件指示", "unsafe-event indicator", "对碰撞或近碰撞施加强惩罚"),
            ("a_t", "加速度动作", "acceleration action", "连接舒适性和平滑性"),
            ("w_e,w_d,w_s,w_a", "奖励权重", "reward weights", "决定策略偏好"),
        ],
        "algorithm_zh": "系统用规则型驾驶管理器处理安全和交通规则，用强化学习在允许动作空间中选择纵向/横向生态驾驶动作；V2I 和视觉特征帮助策略预见信号相位与周围车辆。",
        "algorithm_en": "A rule-based driving manager constrains behavior, while RL chooses eco-driving actions using SPaT/V2I and perception features.",
        "stability_zh": "规则层提高可控性和可解释性，但策略性能仍依赖训练分布与奖励权重。相比纯 RL，它更适合工程系统中的安全外壳。",
        "stability_en": "The rule layer improves interpretability and reduces unsafe exploration, making the hybrid policy more deployable than a purely learned controller.",
        "assumptions": [
            "可获得信号相位与配时 (SPaT) 或可靠 V2I 信息。",
            "规则管理器覆盖主要危险场景。",
            "能耗模型与仿真平台对真实车辆足够近似。",
        ],
        "baselines": "模型式生态驾驶、普通 RL、人工驾驶/IDM、固定速度或信号响应策略。",
        "metrics": "能耗降低百分比、行程时间、停车次数、舒适性指标和碰撞/违规事件。",
        "ablation": "需要分别去掉规则管理器、V2I 特征、视觉特征和横向动作，才能说明混合结构的真实贡献。",
        "limitations": [
            "信号化场景与无信号 AIM 调度问题不同。",
            "Unity 仿真能否代表真实车辆能耗仍需校准。",
            "奖励权重敏感，跨路口迁移可能不稳定。",
        ],
        "extensions": [
            "把能耗奖励移植到 JSSP smoother，作为低层轨迹成本。",
            "用多目标 RL 生成 Pareto 前沿，而不是固定奖励权重。",
            "在 SUMO/真实轨迹数据上校准能耗模型，提高可发表可信度。",
        ],
        "interactive": InteractiveSpec("能耗权重", "Energy weight", 0.1, 4.0, 1.0, "", "能耗权重越高，轨迹越平滑，但可能牺牲通行时间。", "Higher energy weight smooths trajectories but can increase travel time."),
    },
    "P06": {
        "method_family": "Parameterized reinforcement learning / 参数化强化学习",
        "core_question_zh": "如何同时处理离散驾驶决策和连续控制参数，使电动网联车在信号交叉口实现节能通行？",
        "core_question_en": "How can discrete maneuver choices and continuous control parameters be learned jointly for EV eco-driving at signalized intersections?",
        "innovation_rating": "中等偏强：参数化动作空间贴合驾驶决策结构，对混合离散-连续调度有启发。",
        "formula_name": "参数化动作 MDP / Parameterized-action MDP",
        "formula": r"a_t=(d_t,\xi_t),\quad d_t\in\mathcal{D},\;\xi_t\in\mathbb{R}^{m(d_t)},\quad Q(s_t,d_t,\xi_t)\approx \mathbb{E}[R_t]",
        "symbols": [
            ("d_t", "离散驾驶决策", "discrete driving decision", "如保持、变道、跟驰模式"),
            ("xi_t", "连续动作参数", "continuous action parameter", "如目标速度或加速度幅值"),
            ("D", "离散动作集合", "discrete action set", "描述可选机动"),
            ("Q", "动作价值函数", "action-value function", "评价离散-连续组合收益"),
            ("R_t", "回报", "return", "累积能耗、效率和安全目标"),
        ],
        "algorithm_zh": "参数化 RL 把驾驶行为拆成离散模式和对应连续参数，结合模型式跟驰/变道规则处理周围 HDV，再用学习策略选择节能动作。该结构很适合未来把高层调度选择和低层连续轨迹合并。",
        "algorithm_en": "Parameterized RL separates maneuver selection from continuous parameter control, combining learned decisions with model-based car-following and lane-changing constraints.",
        "stability_zh": "模型式规则给安全留出底线，学习器主要优化效率和能耗；但混合动作空间训练难度较高，参数边界设计会影响收敛。",
        "stability_en": "Model-based constraints provide a safety floor, while the learner optimizes energy and efficiency; convergence depends strongly on action parameterization.",
        "assumptions": [
            "周围车辆行为可由跟驰/变道模型近似。",
            "电动车能耗模型可靠，且可用于仿真奖励。",
            "信号灯信息和车辆状态可观测。",
        ],
        "baselines": "传统生态驾驶、普通 DQN/DDPG、规则驾驶、无参数化 RL 和 IDM。",
        "metrics": "电耗、平均速度、延误、停车次数、舒适性和混合交通影响。",
        "ablation": "应比较参数化 RL 与纯离散、纯连续动作策略；还应测试参数边界和模型式安全规则的贡献。",
        "limitations": [
            "信号交叉口和电动车设定使结论不完全适用于无信号 CAV 调度。",
            "参数化动作设计依赖专家经验。",
            "混合交通中 HDV 模型错误可能传播到策略学习。",
        ],
        "extensions": [
            "把 JSSP 的车辆排序作为离散动作，把目标时间/速度作为连续参数。",
            "加入不确定 HDV 模型集合，做鲁棒参数化 RL。",
            "用分层策略把 lane choice、arrival time 和 speed profile 分别建模。",
        ],
        "interactive": InteractiveSpec("CAV渗透率", "CAV penetration rate", 0.05, 1.0, 0.5, "", "渗透率提高通常增强节能协同，但低渗透率下收益受 HDV 约束明显。", "Higher penetration improves eco-coordination, while low penetration is constrained by HDVs."),
    },
    "P07": {
        "method_family": "Pontryagin minimum principle eco-driving / PMP 生态驾驶最优控制",
        "core_question_zh": "在无信号交叉口协作中，如何用解析最优控制生成节能、少停顿的速度曲线？",
        "core_question_en": "How can Pontryagin-style optimal control generate energy-efficient speed profiles for cooperative CAVs at an unsignalized intersection?",
        "innovation_rating": "理论清晰但范围较窄：对 smoother 目标函数很有价值，对高层调度贡献较少。",
        "formula_name": "PMP 速度规划问题 / PMP speed-profile optimal control",
        "formula": r"\min_{u(t)}\int_{t_0}^{t_f}\left(\alpha P(v(t),u(t))+\beta u(t)^2\right)dt,\quad H=L+\lambda_p v+\lambda_v u",
        "symbols": [
            ("P(v,u)", "动力/能耗模型", "power or energy model", "刻画电动车能量消耗"),
            ("u(t)", "加速度", "acceleration", "连续控制变量"),
            ("H", "哈密顿量", "Hamiltonian", "PMP 的必要条件核心"),
            ("lambda_p,lambda_v", "协态变量", "costate variables", "连接状态约束和最优控制"),
            ("alpha,beta", "能耗与平滑权重", "energy and smoothness weights", "决定节能与舒适的折中"),
        ],
        "algorithm_zh": "论文把路口协作转为有限时域速度曲线优化，用 PMP 推导最优性必要条件，并比较协作与非协作策略。其价值在于给出可解释的低层速度平滑目标。",
        "algorithm_en": "The paper formulates cooperative eco-driving as a finite-horizon speed-profile problem and uses PMP conditions to derive interpretable optimal-control behavior.",
        "stability_zh": "解析最优控制比黑盒学习更可解释，但对边界条件和冲突场景分类敏感；实时性取决于求解 shooting/边值问题的效率。",
        "stability_en": "The optimal-control structure is interpretable, but solution quality depends on boundary conditions and conflict-case classification.",
        "assumptions": [
            "车辆动力学和能耗模型可精确获得。",
            "冲突关系可以预先分类并转成边界/时间约束。",
            "场景规模相对有限。",
        ],
        "baselines": "IDM、非协作生态驾驶、固定速度或普通跟驰策略。",
        "metrics": "能耗、速度平滑性、旅行时间、停车次数和安全间隔满足情况。",
        "ablation": "不是典型模块化学习论文，消融较少；更需要权重敏感性和不同协作等级比较。",
        "limitations": [
            "高层排序与多车组合爆炸处理不足。",
            "PMP 推导在复杂约束下可能需要数值求解，工程实现不总是简单。",
            "对混合交通和不确定性覆盖有限。",
        ],
        "extensions": [
            "把 PMP 低层解作为 JSSP 调度候选动作的可行性 oracle。",
            "用神经网络学习 PMP 解的近似映射，加速在线 smoother。",
            "在成本中加入 jerk 和舒适性约束，构建更完整的轨迹平滑器。",
        ],
        "interactive": InteractiveSpec("平滑权重", "Smoothness weight", 0.1, 5.0, 1.5, "", "平滑权重越大，加速度变化越柔和，但可能增加清空时间。", "A larger smoothness weight softens acceleration but may increase clearing time."),
    },
    "P08": {
        "method_family": "Data-driven predictive control + RLS / 数据驱动预测控制与递归最小二乘",
        "core_question_zh": "在混合交通信号交叉口中，如何在线估计前车行为并使 CAV 在黄灯/红灯附近安全预测控制？",
        "core_question_en": "How can a CAV estimate a preceding HDV online and perform safety-aware predictive control near signal changes?",
        "innovation_rating": "中等：安全问题具体、方法稳健，对混合交通 fallback 很有参考价值。",
        "formula_name": "RLS 估计与有限时域 MPC / RLS estimation and finite-horizon MPC",
        "formula": r"\hat\theta_k=\hat\theta_{k-1}+K_k(y_k-\phi_k^\top\hat\theta_{k-1}),\quad \min_{u_{0:N-1}}\sum_{k=0}^{N}\ell(x_k,u_k,\hat\theta_k)",
        "symbols": [
            ("theta", "HDV 行为参数", "HDV behavior parameters", "在线估计前车模型"),
            ("K_k", "RLS 增益", "RLS gain", "控制新观测对参数的影响"),
            ("phi_k", "回归特征", "regressor features", "由前车状态构成"),
            ("N", "预测时域", "prediction horizon", "MPC 规划长度"),
            ("ell", "阶段代价", "stage cost", "综合安全、舒适和信号响应"),
        ],
        "algorithm_zh": "控制器用 RLS 实时估计前方 HDV 行为，再在有限时域内求解预测控制问题，重点避免黄灯/红灯切换时的追尾风险和过度保守制动。",
        "algorithm_en": "The controller estimates preceding HDV behavior with RLS and solves a finite-horizon predictive-control problem focused on rear-end safety near signal transitions.",
        "stability_zh": "MPC 的滚动优化提供反馈修正，RLS 提供模型自适应；但稳定性依赖可辨识性、预测时域和安全约束设置。",
        "stability_en": "Receding-horizon MPC offers feedback correction and RLS adapts the behavior model, but robustness depends on identifiability and constraint design.",
        "assumptions": [
            "前车行为可由低维参数模型描述。",
            "CAV 可可靠观测前车状态。",
            "主要风险是纵向追尾，而非多方向冲突区碰撞。",
        ],
        "baselines": "固定参数 MPC、普通跟驰模型、无估计控制器和保守刹车策略。",
        "metrics": "最小车间距、碰撞风险、速度/加速度平滑性、延误和信号违规。",
        "ablation": "关键是去掉 RLS 自适应、改变预测时域、改变安全约束强度，观察鲁棒性。",
        "limitations": [
            "场景局限于信号交叉口纵向跟驰。",
            "RLS 对异常驾驶和非线性行为变化可能响应不足。",
            "未解决交叉冲突、合流和多车调度。",
        ],
        "extensions": [
            "把 RLS/贝叶斯预测接入无信号 JSSP smoother，为 HDV 建立不确定处理时间。",
            "用分布鲁棒 MPC 替代点估计 MPC。",
            "将追尾 CBF 与横向冲突 CBF 统一成多约束 safety layer。",
        ],
        "interactive": InteractiveSpec("预测时域", "Prediction horizon", 2, 12, 6, "s", "时域越长越能提前制动，但计算量和模型误差暴露也增加。", "A longer horizon anticipates braking but increases computation and model-error exposure."),
    },
    "P09": {
        "method_family": "Overtaking-enabled two-stage eco-approach / 允许超车的两阶段生态接近控制",
        "core_question_zh": "在信号交叉口中，放松 FIFO 队列并允许超车，能否同时降低能耗和延误？",
        "core_question_en": "Can relaxing FIFO with overtaking-enabled lane optimization reduce both energy use and delay at signalized intersections?",
        "innovation_rating": "较强工程洞察：明确挑战 FIFO 保守性，对 JSSP 重排序动机非常有用。",
        "formula_name": "车道 DP 与速度 PMP 的两阶段目标 / Two-stage lane-DP and speed-PMP objective",
        "formula": r"\min_{\ell_{0:H},\,u(t)}\; J=\sum_{k=0}^{H} c_{\ell}(x_k,\ell_k)+\int_{t_0}^{t_f} c_v(v(t),u(t))\,dt",
        "symbols": [
            ("ell_k", "第 k 步车道选择", "lane choice at step k", "动态规划阶段决策"),
            ("c_ell", "车道/超车代价", "lane/overtaking cost", "平衡超车收益与扰动"),
            ("u(t)", "速度控制", "speed-control input", "连续速度优化变量"),
            ("c_v", "速度轨迹代价", "speed-profile cost", "包含能耗、时间和平滑性"),
            ("H", "滚动规划长度", "receding-horizon length", "在线计算窗口"),
        ],
        "algorithm_zh": "第一阶段用动态规划选择车道和超车策略，打破传统 FIFO；第二阶段用 PMP/最优控制生成速度曲线。滚动时域使策略能对前车扰动重新规划。",
        "algorithm_en": "A receding-horizon controller first solves lane/overtaking choices with dynamic programming and then optimizes the speed profile with optimal-control tools.",
        "stability_zh": "两阶段设计把组合车道决策和连续速度控制分开，实时性较好；但阶段间耦合不足时，车道选择可能导致后续速度优化不可行。",
        "stability_en": "The decomposition improves tractability, but lane decisions can create downstream feasibility issues if speed constraints are not anticipated.",
        "assumptions": [
            "车辆具备安全超车和变道能力。",
            "信号相位和前车扰动可预测。",
            "车道变化不会引入未建模的横向风险。",
        ],
        "baselines": "常速接近、普通生态接近、FIFO 策略和不允许超车的控制器。",
        "metrics": "驾驶成本、能耗、延误、停车次数、超车次数和计算耗时。",
        "ablation": "需比较禁用超车、禁用 DP 车道优化和不同滚动时域长度。",
        "limitations": [
            "信号场景与无信号 AIM 不完全一致。",
            "超车可行性强依赖道路几何和混合交通行为。",
            "DP 状态空间随车道数和车辆数增长。",
        ],
        "extensions": [
            "把“允许超车”转化为 JSSP 中可交换相邻作业的局部搜索。",
            "在无信号交叉口中研究 FIFO relaxation 的安全边界。",
            "联合学习车道选择和排序，避免两阶段失配。",
        ],
        "interactive": InteractiveSpec("FIFO放松强度", "FIFO relaxation strength", 0, 1, 0.4, "", "放松越强，潜在效率越高，但规则复杂度和可解释性风险增加。", "Stronger FIFO relaxation can improve efficiency but raises rule complexity."),
    },
    "P10": {
        "method_family": "Real-world cooperative maneuver planning evaluation / 真实道路协同机动规划评估",
        "core_question_zh": "协同交叉口管理方法在混合交通仿真与真实原型车测试中是否仍能减少停车和通行时间？",
        "core_question_en": "Do cooperative intersection-management approaches reduce stops and crossing time in both mixed-traffic simulation and real prototype drives?",
        "innovation_rating": "强验证价值：真实道路评估稀缺，是论文实验设计和指标选择的优质参考。",
        "formula_name": "评估指标聚合 / Evaluation-metric aggregation",
        "formula": r"S=\frac{1}{M}\sum_{m=1}^{M} n_m^{stop},\quad T=\frac{1}{M}\sum_{m=1}^{M}(t_m^{out}-t_m^{in}),\quad K=\max_m \kappa_m",
        "symbols": [
            ("S", "平均停车次数", "average number of stops", "衡量 stop avoidance 的直接指标"),
            ("T", "平均穿越时间", "average crossing time", "衡量效率"),
            ("K", "最大关键性", "maximum criticality", "表示最危险场景风险"),
            ("M", "评估运行次数", "number of evaluation runs", "仿真或真实试验样本量"),
            ("kappa_m", "关键性指标", "criticality measure", "安全评估变量"),
        ],
        "algorithm_zh": "论文不是提出单一新控制算法，而是比较多场景预测和图强化学习等协同机动规划模块，在混合交通仿真与真实车辆中评估停车、时间和关键性。",
        "algorithm_en": "Rather than only proposing a controller, the paper evaluates cooperative maneuver-planning modules in simulation and real-world prototype drives.",
        "stability_zh": "贡献在验证闭环：真实车辆实验暴露通信、定位、感知和人类交通干扰。它为仿真论文提供“哪些指标必须走向真实”的标尺。",
        "stability_en": "Its value is validation realism: real drives reveal communication, localization, perception, and mixed-traffic issues hidden in pure simulation.",
        "assumptions": [
            "原型系统中的通信与感知可支持协同机动规划。",
            "真实测试场景代表性足以支持初步结论。",
            "关键性指标可近似反映真实安全风险。",
        ],
        "baselines": "不同协同机动规划模块、非协同驾驶、仿真基线和真实驾驶对照。",
        "metrics": "穿越时间、停车次数、关键性/风险、成功率和真实系统运行稳定性。",
        "ablation": "作为评估论文，模块消融不一定充分；最需要的是同一交通需求下的模块替换、传感器/通信降级和 HDV 行为差异测试。",
        "limitations": [
            "样本规模和场景覆盖通常小于大规模仿真。",
            "不是 JSSP 建模论文，理论调度贡献有限。",
            "真实测试条件可能较温和，极端场景不足。",
        ],
        "extensions": [
            "把你的 JSSP scheduler 输出转化为相同停车/穿越时间/关键性指标，形成可对标实验。",
            "设计 sim-to-real gap 表格：仿真中通过的策略在真实系统中哪些环节会失效。",
            "加入通信延迟、定位噪声和 HDV 插入，复现实验鲁棒性。",
        ],
        "interactive": InteractiveSpec("通信延迟", "Communication latency", 0, 500, 80, "ms", "延迟上升会降低协同收益，并增加保守安全缓冲。", "Higher latency reduces coordination benefit and increases safety buffers."),
    },
    "P11": {
        "method_family": "Spatial-domain robust MPC / 空间域鲁棒模型预测控制",
        "core_question_zh": "在路径和速度存在不确定性时，如何把交叉口多类型冲突统一成可实时求解的空间域约束？",
        "core_question_en": "How can crossing, following, merging, and diverging conflicts be unified as real-time spatial-domain constraints under motion uncertainty?",
        "innovation_rating": "很强：空间域建模和统一线性碰撞约束对低层 smoother 安全可行性极有价值。",
        "formula_name": "空间域动力学与鲁棒碰撞约束 / Spatial-domain dynamics and robust collision constraints",
        "formula": r"\frac{dt_i}{ds}=\frac{1}{v_i(s)},\quad \min_{u_i(s)}\sum_i\int \left(w_t\frac{1}{v_i(s)}+w_u u_i(s)^2\right)ds,\quad h_{ij}(s,\Delta)\ge d_{safe}",
        "symbols": [
            ("s", "空间路径坐标", "spatial path coordinate", "把时间规划转成沿路径规划"),
            ("v_i(s)", "空间域速度", "speed over path coordinate", "决定到达时间和安全间隔"),
            ("h_ij", "车辆 i,j 的冲突间隔函数", "conflict-separation function", "统一多种冲突类型"),
            ("Delta", "运动不确定性", "motion uncertainty", "路径/速度误差集合"),
            ("d_safe", "安全距离阈值", "safe-distance threshold", "鲁棒约束下界"),
        ],
        "algorithm_zh": "论文把轨迹规划从时间域转为空间域，针对 crossing/following/merging/diverging 构造统一线性化安全约束，再用集中式 MPC 和实时迭代求解，以较小最优性损失换取计算速度。",
        "algorithm_en": "The method transforms coordination into a spatial-domain nonlinear program, linearizes unified collision-avoidance constraints, and solves it with real-time MPC iterations.",
        "stability_zh": "鲁棒性来自显式不确定集合与安全约束，实时性来自空间域简化和 RTI。相比纯学习策略，这类 smoother 更容易给审稿人安全信心。",
        "stability_en": "Robustness comes from explicit uncertainty sets and safety constraints; RTI makes the spatial-domain MPC viable online.",
        "assumptions": [
            "车辆路径可用空间坐标参数化。",
            "不确定性集合边界可估计且不严重失真。",
            "集中式求解器可在控制周期内完成。",
        ],
        "baselines": "时间域 MPC、非鲁棒控制、保守安全间隔策略和不同 RTI 近似。",
        "metrics": "求解时间、最优性损失、碰撞约束余量、通行时间、速度平滑性和不确定性敏感性。",
        "ablation": "很适合做鲁棒半径、RTI 次数、统一约束 vs 分类型约束的消融。",
        "limitations": [
            "优化问题仍可能在大规模车辆数下变重。",
            "不确定集合若估计过小会失去安全性，过大则过于保守。",
            "高层排序/优先级选择不是主要贡献。",
        ],
        "extensions": [
            "将 JSSP 调度输出作为 MPC 的目标时间或优先级约束。",
            "用学习模型预测不确定集合大小，实现自适应鲁棒性。",
            "把空间域安全约束封装成调度动作可行性检查器。",
        ],
        "interactive": InteractiveSpec("不确定性半径", "Uncertainty radius", 0.0, 3.0, 0.8, "m", "半径越大，安全裕度越高但轨迹越保守、延误越大。", "A larger uncertainty radius improves safety margin but increases conservatism."),
    },
    "P12": {
        "method_family": "Uncertainty-aware RL + high-order CBF / 不确定性感知强化学习与高阶控制屏障函数",
        "core_question_zh": "如何让 RL 在无信号交叉口中既保持灵活决策，又在不确定性升高时由 HOCBF 强制保证安全？",
        "core_question_en": "How can RL remain flexible while a high-order CBF safety filter intervenes under uncertainty at unsignalized intersections?",
        "innovation_rating": "较强：把 ensemble distributional RL 的不确定性与 HOCBF 过滤结合，适合作为学习调度器安全外壳。",
        "formula_name": "HOCBF 安全过滤 / High-order CBF safety filter",
        "formula": r"u^\star=\arg\min_u \|u-u_{RL}\|^2\quad \text{s.t.}\quad L_f^m h(x)+L_gL_f^{m-1}h(x)u+\alpha(\psi_{m-1}(x))\ge \rho(\sigma)",
        "symbols": [
            ("u_RL", "强化学习建议动作", "RL-proposed action", "效率导向但未必安全"),
            ("h(x)", "安全函数", "safety barrier function", "h>=0 表示安全集合"),
            ("L_f,L_g", "李导数", "Lie derivatives", "刻画动力学对安全函数的影响"),
            ("sigma", "策略/状态不确定性", "policy/state uncertainty", "调节安全收紧程度"),
            ("rho(sigma)", "不确定性安全裕度", "uncertainty-dependent safety margin", "不确定性越高约束越保守"),
        ],
        "algorithm_zh": "先用风险感知 ensemble distributional RL 估计动作价值和不确定性，再通过 HOCBF 二次规划把 RL 动作投影到安全集合中。不确定性越大，屏障约束越保守。",
        "algorithm_en": "An uncertainty-aware ensemble/distributional RL policy proposes actions, and a HOCBF quadratic program filters them into the safe set with uncertainty-dependent tightening.",
        "stability_zh": "HOCBF 提供形式化安全条件，但效率取决于 RL 策略；若安全约束不可行，需要 fallback 或软约束设计。",
        "stability_en": "The HOCBF layer can certify forward invariance under assumptions, but infeasible safety constraints require fallback handling.",
        "assumptions": [
            "安全函数可正确表达交叉口危险集合。",
            "车辆动力学和相对状态可观测。",
            "不确定性估计与真实风险有足够相关性。",
        ],
        "baselines": "普通 RL、安全 RL、固定 CBF、无不确定性调节的 HOCBF 和规则控制。",
        "metrics": "碰撞率、成功率、平均时间、干预次数、不确定性校准和约束可行性。",
        "ablation": "必须比较无 HOCBF、固定 HOCBF、无 ensemble 不确定性、不同安全裕度函数。",
        "limitations": [
            "单车/局部自动驾驶视角多于集中式多车调度。",
            "HOCBF 对动力学模型准确性敏感。",
            "QP 频繁干预可能导致行为抖动或效率下降。",
        ],
        "extensions": [
            "把 JSSP scheduler 的动作作为 RL proposal，再用 HOCBF/MPC 投影到安全集合。",
            "研究 CBF 约束不可行时的优先级回退和重调度。",
            "用 conformal prediction 校准不确定性裕度，增强审稿可信度。",
        ],
        "interactive": InteractiveSpec("安全裕度系数", "Safety margin coefficient", 0.0, 4.0, 1.3, "", "系数越大，CBF 介入更早；安全性提升但效率下降。", "A larger margin triggers earlier intervention, improving safety but reducing efficiency."),
    },
    "P13": {
        "method_family": "Systematic survey of CAV control / CAV 控制技术系统综述",
        "core_question_zh": "CAV 控制从状态估计、轨迹跟踪到协同控制有哪些主线方法，它们如何支撑交叉口协同研究？",
        "core_question_en": "What are the main CAV control families from state estimation to trajectory tracking and cooperative control, and how do they frame intersection research?",
        "innovation_rating": "综述价值强但原创方法弱：适合作为背景和分类框架引用，不应当作为核心算法依据。",
        "formula_name": "通用车辆控制闭环 / Generic vehicle-control loop",
        "formula": r"\dot x=f(x,u,w),\quad y=g(x)+\eta,\quad u=\kappa(\hat x,r),\quad e=r-y",
        "symbols": [
            ("x", "车辆状态", "vehicle state", "控制系统内部变量"),
            ("u", "控制输入", "control input", "转向、加速度或制动力"),
            ("w", "外部扰动", "external disturbance", "道路、交通和模型误差"),
            ("hat x", "估计状态", "estimated state", "状态估计模块输出"),
            ("r", "参考轨迹", "reference trajectory", "轨迹规划/调度层给定目标"),
        ],
        "algorithm_zh": "作为综述，它按估计、跟踪、路径规划、协同控制等层次整理方法。对本项目最有价值的是把 comfort、safety、energy、efficiency 放入同一个 CAV 控制目标谱系。",
        "algorithm_en": "As a survey, it organizes estimation, tracking, planning, and cooperative-control techniques, framing safety, comfort, energy, and efficiency as connected CAV objectives.",
        "stability_zh": "综述不提供单个算法的收敛证明，但能帮助你定位不同方法的理论依据，如鲁棒控制、MPC、学习控制和协同控制。",
        "stability_en": "It does not certify one algorithm, but it maps the theoretical families used to justify robust control, MPC, learning control, and cooperative control.",
        "assumptions": [
            "文献覆盖广但不可避免存在选择偏差。",
            "不同控制任务和应用场景的指标不可直接比较。",
            "综述结论需要回到具体论文验证。",
        ],
        "baselines": "不适用原始实验；基准是分类完整性、代表性文献覆盖和趋势判断。",
        "metrics": "综述质量、分类清晰度、引用覆盖、应用关联度和未来方向启发。",
        "ablation": "综述没有消融；阅读时应做你自己的 taxonomy cross-check：是否遗漏 intersection scheduling、formal safety、mixed traffic。",
        "limitations": [
            "范围太广，交叉口轨迹平滑不是焦点。",
            "综述时效性随新 RL/CBF/GNN 文献快速下降。",
            "缺少统一实验平台比较。",
        ],
        "extensions": [
            "把综述分类裁剪成你的 thesis taxonomy：scheduler、smoother、safety filter、evaluation。",
            "建立一张 CAV 控制方法与 JSSP/RL/AIM 的映射表。",
            "用它支持引言中 safety-comfort-energy-efficiency 多目标论证。",
        ],
        "interactive": InteractiveSpec("方法成熟度", "Method maturity", 0, 1, 0.65, "", "成熟度越高可验证性越强，但探索性和性能上限可能较低。", "Higher maturity improves certifiability but may reduce exploratory performance."),
    },
    "P14": {
        "method_family": "Distributed MARL for AIM / 分布式多智能体强化学习交叉口管理",
        "core_question_zh": "没有中心服务器时，多车能否通过分布式 MARL 学会安全高效地穿越交叉口？",
        "core_question_en": "Can vehicles learn decentralized intersection traversal policies through MARL without a central coordinator?",
        "innovation_rating": "中等：分布式 AIM 方向重要，但 workshop 论文更适合作为对比路线而非核心证据。",
        "formula_name": "去中心化 Markov game 与 DDQN 损失 / Decentralized Markov game and DDQN loss",
        "formula": r"L_i(\theta_i)=\mathbb{E}\left[\left(r_i+\gamma Q_{\bar\theta_i}(o_i',\arg\max_a Q_{\theta_i}(o_i',a))-Q_{\theta_i}(o_i,a_i)\right)^2\right]",
        "symbols": [
            ("o_i", "智能体 i 的局部观测", "local observation of agent i", "分布式策略的信息输入"),
            ("a_i", "智能体动作", "agent action", "车辆局部决策"),
            ("r_i", "局部奖励", "local reward", "安全与效率反馈"),
            ("Q_theta", "DQN 价值网络", "DQN value network", "估计离散动作价值"),
            ("gamma", "折扣因子", "discount factor", "长期协同收益权重"),
        ],
        "algorithm_zh": "每辆车基于局部/环视观测做决策，使用 dueling double DQN 和 prioritized scenario replay 提升训练效率。它代表与集中式 JSSP 调度相反的技术路线。",
        "algorithm_en": "Each vehicle acts from local observations using dueling double DQN and prioritized scenario replay, forming a decentralized alternative to centralized scheduling.",
        "stability_zh": "MARL 的难点是非平稳性、信用分配和安全验证。分布式策略可扩展，但缺少中心协调时冲突消解更依赖奖励塑形和训练覆盖。",
        "stability_en": "MARL faces non-stationarity, credit assignment, and safety-certification challenges; scalability improves, but conflict resolution becomes empirical.",
        "assumptions": [
            "局部观测足以推断危险交互。",
            "仿真训练覆盖足够多场景。",
            "车辆之间无需高可靠中心通信。",
        ],
        "baselines": "SMARTS 基准策略、规则控制、单智能体/普通 DQN 和集中式方法。",
        "metrics": "成功率、碰撞率、平均速度、通行效率、奖励和训练稳定性。",
        "ablation": "应检验 dueling、double Q、prioritized replay 和观测范围的贡献。",
        "limitations": [
            "安全主要靠仿真经验，形式化约束不足。",
            "极端密集交通和低可观测性下可能不稳定。",
            "论文级别偏 workshop，实验深度有限。",
        ],
        "extensions": [
            "把 MARL 作为 centralized JSSP 的对照组，强调可证明调度的优势。",
            "加入图通信或注意力机制，缓解局部观测不足。",
            "用安全层过滤每个智能体动作，比较 decentralized shield 与 centralized shield。",
        ],
        "interactive": InteractiveSpec("观测半径", "Observation radius", 10, 120, 50, "m", "半径越大信息越充分，但通信/感知负担增加。", "A larger observation radius improves information but increases sensing/communication load."),
    },
    "P15": {
        "method_family": "Distributed hierarchical adversarial learning / 分布式层次化对抗学习",
        "core_question_zh": "如何用层次化长期/短期判别机制改进多智能体交叉口交互策略学习？",
        "core_question_en": "How can hierarchical long-term and short-term adversarial discrimination improve multi-agent interaction learning for AIM?",
        "innovation_rating": "中等偏强：层次化对抗学习有新意，但安全和可解释性仍弱于约束优化方法。",
        "formula_name": "层次对抗学习目标 / Hierarchical adversarial-learning objective",
        "formula": r"\min_{\pi}\max_{D_L,D_S}\; \mathbb{E}_{\tau\sim\pi_E}[\log D(\tau)]+\mathbb{E}_{\tau\sim\pi}[\log(1-D(\tau))]-\lambda J_{RL}(\pi)",
        "symbols": [
            ("pi", "多智能体策略", "multi-agent policy", "学习车辆交互行为"),
            ("D_L", "长期判别器", "long-term discriminator", "评价轨迹级行为质量"),
            ("D_S", "短期判别器", "short-term discriminator", "评价局部交互动作"),
            ("tau", "轨迹片段", "trajectory segment", "对抗学习样本"),
            ("J_RL", "强化学习收益", "RL return", "保留任务奖励优化目标"),
        ],
        "algorithm_zh": "D-HAL 通过长期和短期判别器引导策略学习，让智能体既模仿/区分整体交互轨迹，又修正局部短时动作。层次化目标试图改善多智能体交互中的稀疏奖励和非平稳性。",
        "algorithm_en": "D-HAL uses long-term and short-term discriminators to shape multi-agent policies, improving interaction learning under sparse rewards and non-stationarity.",
        "stability_zh": "对抗训练可能提升样本效率，但也会带来训练不稳定；安全仍主要通过奖励或环境终止惩罚表达，缺少硬约束。",
        "stability_en": "Adversarial training can improve sample efficiency but may be unstable; safety is still mostly reward-based unless paired with constraints.",
        "assumptions": [
            "专家轨迹或高质量行为分布可用于判别学习。",
            "长期/短期判别目标与真实交通安全效率一致。",
            "仿真环境足以覆盖多智能体交互复杂性。",
        ],
        "baselines": "普通 MARL、模仿学习、无层次判别器版本、无对抗损失版本。",
        "metrics": "碰撞率、平均延误、通行效率、成功率、奖励曲线和训练样本效率。",
        "ablation": "必须拆分长期判别器、短期判别器、对抗损失和 RL 任务损失；否则难以证明层次结构必要。",
        "limitations": [
            "对抗训练难调参，复现实验成本高。",
            "策略可解释性弱，审稿人会追问安全证书。",
            "分布式学习结果可能依赖仿真器和奖励设置。",
        ],
        "extensions": [
            "用 JSSP 求解器生成专家排序轨迹，训练 imitation/adversarial scheduler。",
            "把判别器输出作为调度质量估计，而不是直接控制车辆。",
            "在对抗学习外加 CBF/MPC 安全约束，分离效率学习与安全保证。",
        ],
        "interactive": InteractiveSpec("对抗损失权重", "Adversarial loss weight", 0, 3, 0.9, "", "权重适中可提升交互拟合，过高会牺牲任务奖励稳定性。", "Moderate weight improves interaction shaping; too much can destabilize RL."),
    },
}


def synthesize_note(paper: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    d = DETAILS[paper["id"]]
    concepts = [
        ("自动交叉口管理", "Autonomous Intersection Management", "把信号控制替换为车辆级调度与控制。"),
        ("轨迹平滑", "Trajectory Smoothing", "减少急加减速、停车和能耗峰值。"),
        ("安全约束", "Safety Constraints", "把碰撞风险写成距离、时间间隔或屏障函数。"),
        (d["method_family"].split(" / ")[0], d["method_family"].split(" / ")[-1], "该论文的核心方法族。"),
    ]

    section_map = []
    for idx, h in enumerate(facts["section_headings"][:8], start=1):
        heading = h["heading"]
        lower = heading.lower()
        if "intro" in lower:
            zh = "定位问题背景、研究缺口和为什么现有保守/非协同方法不足。"
            en = "Frames the motivation, research gap, and limits of conservative or non-cooperative methods."
        elif any(k in lower for k in ("problem", "formulation", "model", "system")):
            zh = "把交通交互转写为状态、约束、目标或图结构，是精读时最应复现的部分。"
            en = "Defines states, constraints, objectives, or graph structures; this is the section to reproduce carefully."
        elif any(k in lower for k in ("method", "framework", "algorithm", "control")):
            zh = "给出算法流程和求解机制，应重点追踪输入、输出和安全接口。"
            en = "Gives the algorithmic mechanism; track inputs, outputs, and safety interfaces."
        elif any(k in lower for k in ("simulation", "experiment", "result", "evaluation")):
            zh = "检验方法是否真的改善效率、安全或能耗；要关注基准是否公平。"
            en = "Tests efficiency, safety, or energy claims; inspect whether baselines are fair."
        elif "conclu" in lower:
            zh = "总结贡献和未来方向，也常暴露作者承认的边界条件。"
            en = "Summarizes contributions and often reveals author-recognized boundaries."
        else:
            zh = "作为局部论证段落阅读，关注它如何服务主问题。"
            en = "Read as a local argument and ask how it supports the main question."
        section_map.append({"page": h["page"], "heading": heading, "zh": zh, "en": en})

    family_lower = d["method_family"].lower()
    figure_table_cues = [
        {
            "zh": "系统框架图",
            "en": "system framework diagram",
            "reading": "先确认输入、决策层、控制层和安全约束之间的数据流。",
        },
        {
            "zh": "实验指标对比图表",
            "en": "experimental metric comparison plots/tables",
            "reading": "重点看平均值之外的密度变化、失败场景、计算时间和方差。",
        },
    ]
    if any(k in family_lower for k in ("graph", "jssp", "resequencing", "scheduling", "lane")):
        figure_table_cues.insert(
            1,
            {
                "zh": "冲突关系图 / 通行顺序图",
                "en": "conflict-relation or passing-order graph",
                "reading": "把节点、边类型和先后约束翻译成 JSSP 的作业、机器和析取约束。",
            },
        )
    elif any(k in family_lower for k in ("rl", "reinforcement", "marl", "adversarial")):
        figure_table_cues.insert(
            1,
            {
                "zh": "策略网络/训练流程图",
                "en": "policy-network or training-pipeline diagram",
                "reading": "检查状态、动作、奖励、经验回放和安全惩罚是否闭环一致。",
            },
        )
    elif any(k in family_lower for k in ("mpc", "control", "pmp", "cbf")):
        figure_table_cues.insert(
            1,
            {
                "zh": "控制框架/轨迹曲线图",
                "en": "control-framework or trajectory-profile plots",
                "reading": "关注约束激活位置、速度/加速度曲线和安全裕度是否平滑。",
            },
        )
    else:
        figure_table_cues.insert(
            1,
            {
                "zh": "方法分类图",
                "en": "method-taxonomy diagram",
                "reading": "把综述分类映射到你的 scheduler、smoother、safety filter 和 evaluation 四层框架。",
            },
        )

    return {
        "id": paper["id"],
        "bibkey": paper["bibkey"],
        "title": paper["title"],
        "authors": paper["authors"],
        "year": paper["year"],
        "venue": paper["venue"],
        "doi": paper.get("doi", ""),
        "source_url": paper.get("source_url", ""),
        "pdf_url": paper.get("pdf_url", ""),
        "theme": paper["theme"],
        "relevance": paper["relevance"],
        "method_family": d["method_family"],
        "source_facts": facts,
        "concepts": concepts,
        "section_map": section_map,
        "overview": {
            "background_zh": f"这篇论文位于“{paper['theme']}”方向。对你的 JSSP-based Intersection Management 课题，它回答的是高层调度、低层轨迹平滑、安全过滤或真实验证中的一个关键子问题：如何让车辆在路口少停、少冲突、少能耗，同时保持在线可执行。",
            "background_en": f"The paper belongs to the theme of {paper['theme']}. For a JSSP-based intersection-management thesis, it illuminates one of the key layers: scheduling, smoothing, safety filtering, or real-world validation.",
            "pain_zh": paper["limitations"],
            "pain_en": "The main pain point is that efficient intersection coordination must handle combinatorial interactions, continuous vehicle dynamics, and safety constraints under online computation limits.",
            "core_question_zh": d["core_question_zh"],
            "core_question_en": d["core_question_en"],
            "contributions": [
                f"方法贡献 (method contribution)：{paper['method']}",
                f"安全/避碰贡献 (safety contribution)：{paper['collision_avoidance']}",
                f"平滑/停止避免贡献 (smoothing contribution)：{paper['stop_avoidance']}",
                f"创新力度评判 (reviewer judgement)：{d['innovation_rating']}",
            ],
        },
        "methodology": {
            "model_name": d["formula_name"],
            "formula": d["formula"],
            "symbols": d["symbols"],
            "algorithm_zh": d["algorithm_zh"],
            "algorithm_en": d["algorithm_en"],
            "stability_zh": d["stability_zh"],
            "stability_en": d["stability_en"],
            "assumptions": d["assumptions"],
        },
        "experiments": {
            "validation": paper["validation"],
            "baselines": d["baselines"],
            "metrics": d["metrics"],
            "ablation": d["ablation"],
            "figure_table_cues": figure_table_cues,
            "reviewer_reading": "阅读实验时不要只看平均值；应检查交通密度、车流方向、随机种子、失败案例和计算耗时。For doctoral reading, inspect density regimes, demand patterns, random seeds, failure cases, and computation time rather than only mean improvements.",
        },
        "critique": {
            "limitations": d["limitations"],
            "extensions": d["extensions"],
            "project_use": paper["support"],
        },
        "visualization": {
            "interactive": d["interactive"].__dict__,
            "html_structure": [
                "顶部固定 metadata bar：题名、作者、年份、主题、PDF 页数。",
                "左侧目录/section navigator，右侧为五大精读模块。",
                "公式卡片使用 <pre> 或 LaTeX block，紧跟符号表。",
                "审稿人批注用 reviewer-note block，博士拓展用 research-idea list。",
                "交互参数用 input[type=range] + canvas 曲线，打印 PDF 时隐藏交互控件但保留解释。",
            ],
        },
    }


def write_json(note: dict[str, Any], out_dir: Path, slug: str) -> None:
    safe = json.loads(json.dumps(note, ensure_ascii=False))
    out = out_dir / f"{slug}_notes.json"
    out.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")


def html_list(items: list[str], cls: str = "") -> str:
    klass = f' class="{cls}"' if cls else ""
    return "<ul{}>{}</ul>".format(klass, "".join(f"<li>{html.escape(str(i))}</li>" for i in items))


def render_html(note: dict[str, Any], rel_index: str = "../../index.html") -> str:
    spec = note["visualization"]["interactive"]
    anchors = note["source_facts"]["source_anchors"]
    sections = note["section_map"]
    concepts_rows = "".join(
        f"<tr><td>{html.escape(c[0])}</td><td>{html.escape(c[1])}</td><td>{html.escape(c[2])}</td></tr>"
        for c in note["concepts"]
    )
    symbol_rows = "".join(
        f"<tr><td><code>{html.escape(s[0])}</code></td><td>{html.escape(s[1])}</td><td>{html.escape(s[2])}</td><td>{html.escape(s[3])}</td></tr>"
        for s in note["methodology"]["symbols"]
    )
    anchor_rows = "".join(
        f"<tr><td>p.{a['page']}</td><td>{html.escape(a['heading'])}</td></tr>"
        for a in anchors
    )
    section_cards = "".join(
        f"<article><b>p.{s['page']} · {html.escape(s['heading'])}</b><p class='zh'>{html.escape(s['zh'])}</p><p class='en'>{html.escape(s['en'])}</p></article>"
        for s in sections
    )
    figure_rows = "".join(
        f"<tr><td>{html.escape(c['zh'])}</td><td>{html.escape(c['en'])}</td><td>{html.escape(c['reading'])}</td></tr>"
        for c in note["experiments"]["figure_table_cues"]
    )
    return f"""<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(note['id'])} Deep Reading Notes</title>
  <style>
    :root {{ --ink:#1d2733; --muted:#657386; --line:#d9e1ea; --soft:#f6f8fb; --accent:#1f6f61; --warn:#8a4b0f; --blue:#1f5f8b; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB",sans-serif; color:var(--ink); background:#fff; }}
    header.hero {{ padding:28px 34px 18px; border-bottom:1px solid var(--line); background:#f3f6fa; }}
    h1 {{ margin:0 0 8px; font-size:28px; line-height:1.25; letter-spacing:0; }}
    h2 {{ margin:0 0 10px; font-size:22px; }}
    h3 {{ margin:18px 0 8px; font-size:17px; color:var(--accent); }}
    p {{ margin:7px 0; }}
    a {{ color:var(--blue); }}
    .meta {{ color:var(--muted); display:flex; gap:10px; flex-wrap:wrap; }}
    .toolbar {{ position:sticky; top:0; z-index:2; display:flex; gap:8px; align-items:center; padding:10px 34px; border-bottom:1px solid var(--line); background:rgba(255,255,255,.96); }}
    button, .back {{ border:1px solid var(--line); border-radius:6px; background:white; padding:7px 10px; color:var(--ink); text-decoration:none; cursor:pointer; }}
    main {{ display:grid; grid-template-columns:260px minmax(0,1fr); gap:28px; padding:24px 34px 60px; }}
    nav {{ position:sticky; top:58px; align-self:start; border-right:1px solid var(--line); padding-right:18px; }}
    nav a {{ display:block; padding:7px 0; color:var(--ink); text-decoration:none; }}
    section.panel {{ border-bottom:1px solid var(--line); padding:0 0 22px; margin-bottom:20px; }}
    .grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }}
    .card, details, .reviewer-note {{ border:1px solid var(--line); border-radius:8px; padding:14px; background:var(--soft); }}
    .reviewer-note {{ border-left:4px solid var(--warn); background:#fffaf3; }}
    table {{ width:100%; border-collapse:collapse; margin:10px 0; }}
    th, td {{ border:1px solid var(--line); padding:8px; vertical-align:top; }}
    th {{ background:#eef3f7; text-align:left; }}
    .formula {{ overflow:auto; padding:12px; background:#111827; color:#f8fafc; border-radius:8px; white-space:pre-wrap; }}
    .section-map {{ display:grid; gap:10px; }}
    .section-map article {{ border:1px solid var(--line); border-radius:8px; padding:12px; }}
    .viz {{ display:grid; grid-template-columns:minmax(220px,340px) minmax(0,1fr); gap:16px; align-items:start; }}
    canvas {{ width:100%; height:240px; border:1px solid var(--line); border-radius:8px; background:white; }}
    input[type=range] {{ width:100%; }}
    body.zh-only .en {{ display:none; }}
    body.en-only .zh {{ display:none; }}
    @media (max-width: 860px) {{ main {{ grid-template-columns:1fr; }} nav {{ position:static; border-right:0; border-bottom:1px solid var(--line); padding-bottom:10px; }} .grid,.viz {{ grid-template-columns:1fr; }} }}
    @media print {{ .toolbar, nav, .interactive-only {{ display:none; }} main {{ display:block; padding:12px 18px; }} header.hero {{ padding:16px 18px; }} body {{ font-size:11px; }} section.panel {{ break-inside:avoid; }} a {{ color:var(--ink); text-decoration:none; }} }}
  </style>
</head>
<body>
  <header class="hero">
    <h1>{html.escape(note['id'])}. {html.escape(note['title'])}</h1>
    <div class="meta">
      <span>{html.escape(note['authors'])}</span>
      <span>{note['year']}</span>
      <span>{html.escape(note['venue'])}</span>
      <span>PDF pages: {note['source_facts']['page_count']}</span>
      <span>Relevance: {note['relevance']}/100</span>
    </div>
  </header>
  <div class="toolbar interactive-only">
    <a class="back" href="{rel_index}">Index</a>
    <button onclick="document.body.className=''">双语 / Bilingual</button>
    <button onclick="document.body.className='zh-only'">中文</button>
    <button onclick="document.body.className='en-only'">English</button>
    <button onclick="window.print()">Print / Export PDF</button>
  </div>
  <main>
    <nav>
      <a href="#overview">1. 全景速览</a>
      <a href="#method">2. 理论方法</a>
      <a href="#experiment">3. 实验评判</a>
      <a href="#critique">4. 批判与拓展</a>
      <a href="#viz">5. 交互蓝图</a>
      <a href="#anchors">来源锚点</a>
    </nav>
    <div>
      <section id="overview" class="panel">
        <h2>1. 论文全景速览与核心贡献 / High-Level Overview & Core Contributions</h2>
        <div class="grid">
          <div class="card"><h3>研究背景与痛点 / Background & Pain Points</h3><p class="zh">{html.escape(note['overview']['background_zh'])}</p><p class="en">{html.escape(note['overview']['background_en'])}</p><p>{html.escape(note['overview']['pain_zh'])}</p></div>
          <div class="card"><h3>核心科学问题 / Core Scientific Question</h3><p class="zh">{html.escape(note['overview']['core_question_zh'])}</p><p class="en">{html.escape(note['overview']['core_question_en'])}</p></div>
        </div>
        <h3>科学贡献 / Scientific Contributions</h3>
        {html_list(note['overview']['contributions'])}
        <h3>核心概念对照 / Core Concepts</h3>
        <table><tr><th>中文概念</th><th>English Concept</th><th>Role / 学术作用</th></tr>{concepts_rows}</table>
      </section>
      <section id="method" class="panel">
        <h2>2. 理论方法论深度解构 / Deep Dive into Methodology & Theoretical Framework</h2>
        <h3>问题数学建模 / Mathematical Formulation</h3>
        <p><b>{html.escape(note['methodology']['model_name'])}</b></p>
        <div class="formula">$$
{html.escape(note['methodology']['formula'])}
$$</div>
        <table><tr><th>Symbol / 符号</th><th>含义</th><th>Meaning</th><th>Role / 建模作用</th></tr>{symbol_rows}</table>
        <h3>核心算法架构 / Core Algorithm Layout</h3>
        <p class="zh">{html.escape(note['methodology']['algorithm_zh'])}</p>
        <p class="en">{html.escape(note['methodology']['algorithm_en'])}</p>
        <div class="reviewer-note"><b>收敛性、稳定性或实时性 / Convergence, Stability, Real-Time Feasibility</b><p class="zh">{html.escape(note['methodology']['stability_zh'])}</p><p class="en">{html.escape(note['methodology']['stability_en'])}</p></div>
        <h3>潜在假设与边界条件 / Assumptions & Boundary Conditions</h3>
        {html_list(note['methodology']['assumptions'])}
      </section>
      <section id="experiment" class="panel">
        <h2>3. 实验验证与结果评判 / Experimental Validation & Result Evaluation</h2>
        <div class="grid">
          <div class="card"><h3>基准对比与环境 / Baselines & Environment</h3><p>{html.escape(note['experiments']['baselines'])}</p><p>{html.escape(note['experiments']['validation'])}</p></div>
          <div class="card"><h3>核心指标 / Metrics</h3><p>{html.escape(note['experiments']['metrics'])}</p></div>
          <div class="card"><h3>消融实验 / Ablation</h3><p>{html.escape(note['experiments']['ablation'])}</p></div>
          <div class="card"><h3>博士阅读提醒 / Reading Reminder</h3><p>{html.escape(note['experiments']['reviewer_reading'])}</p></div>
        </div>
        <h3>图表阅读线索 / Figure and Table Reading Cues</h3>
        <p>PDF extraction detected approximately {note['source_facts']['figure_reference_count']} figure references and {note['source_facts']['table_reference_count']} table references. Exact captions remain in the original PDF; the bilingual cues below tell you what to inspect first.</p>
        <table><tr><th>图表名称</th><th>Figure/Table Name</th><th>Reading focus / 阅读重点</th></tr>{figure_rows}</table>
      </section>
      <section id="critique" class="panel">
        <h2>4. 审稿人视角：批判性思考与未来方向 / Critical Thinking & Future Directions</h2>
        <div class="grid">
          <div><h3>论文局限性 / Limitations & Weaknesses</h3>{html_list(note['critique']['limitations'])}</div>
          <div><h3>博士课题拓展点 / Research Extensions for PhD</h3>{html_list(note['critique']['extensions'], 'research-idea')}</div>
        </div>
        <div class="reviewer-note"><b>如何服务当前课题 / Use in This Project</b><p>{html.escape(note['critique']['project_use'])}</p></div>
      </section>
      <section id="viz" class="panel">
        <h2>5. 交互式可视化与 PDF 排版蓝图 / Interactive Visualization & PDF Layout Blueprint</h2>
        <div class="viz">
          <div class="card">
            <h3>动态参数探索 / Parameter Exploration</h3>
            <label>{html.escape(spec['label_zh'])} / {html.escape(spec['label_en'])}: <b id="paramValue"></b> {html.escape(spec['unit'])}</label>
            <input id="param" type="range" min="{spec['min_value']}" max="{spec['max_value']}" value="{spec['default']}" step="0.01">
            <p class="zh">{html.escape(spec['response_zh'])}</p>
            <p class="en">{html.escape(spec['response_en'])}</p>
          </div>
          <canvas id="chart" width="720" height="320"></canvas>
        </div>
        <h3>HTML 结构化布局建议 / HTML Structuring</h3>
        {html_list(note['visualization']['html_structure'])}
      </section>
      <section id="anchors" class="panel">
        <h2>来源锚点与逐节阅读路径 / Source Anchors & Section-by-Section Reading Map</h2>
        <p>以下锚点来自本地 PDF 抽取，用于回到原文复核；笔记不保存论文全文。</p>
        <table><tr><th>Page</th><th>Extracted heading</th></tr>{anchor_rows}</table>
        <div class="section-map">{section_cards}</div>
      </section>
    </div>
  </main>
  <script>
    const min = {spec['min_value']}, max = {spec['max_value']};
    const slider = document.getElementById('param');
    const value = document.getElementById('paramValue');
    const canvas = document.getElementById('chart');
    const ctx = canvas.getContext('2d');
    function response(x) {{
      const z = (x - min) / (max - min || 1);
      const delay = Math.min(1, 0.18 + 0.82 * Math.pow(z, 1.25));
      const safety = Math.max(0, Math.min(1, 0.15 + 0.75 * (1 - Math.exp(-2.2 * z))));
      const compute = Math.min(1, 0.10 + 0.88 * z * z);
      return {{delay, safety, compute}};
    }}
    function draw() {{
      const x = parseFloat(slider.value);
      value.textContent = x.toFixed(2);
      ctx.clearRect(0,0,canvas.width,canvas.height);
      ctx.strokeStyle = '#d9e1ea'; ctx.lineWidth = 1;
      for (let i=0;i<6;i++) {{ const y=40+i*45; ctx.beginPath(); ctx.moveTo(50,y); ctx.lineTo(690,y); ctx.stroke(); }}
      const series = [
        ['Efficiency pressure / 效率压力', '#1f5f8b', 'delay'],
        ['Safety margin / 安全裕度', '#1f6f61', 'safety'],
        ['Compute load / 计算负载', '#8a4b0f', 'compute']
      ];
      for (const [label,color,key] of series) {{
        ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.beginPath();
        for (let i=0;i<=120;i++) {{
          const xx = min + (max-min)*i/120;
          const yy = response(xx)[key];
          const px = 50 + i/120*640;
          const py = 270 - yy*210;
          if (i===0) ctx.moveTo(px,py); else ctx.lineTo(px,py);
        }}
        ctx.stroke();
      }}
      const px = 50 + ((x-min)/(max-min||1))*640;
      ctx.strokeStyle = '#111827'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(px,35); ctx.lineTo(px,285); ctx.stroke();
      ctx.font = '15px -apple-system, sans-serif'; ctx.fillStyle = '#1d2733';
      series.forEach((s,i)=>{{ ctx.fillStyle=s[1]; ctx.fillRect(58,20+i*22,12,12); ctx.fillStyle='#1d2733'; ctx.fillText(s[0],78,31+i*22); }});
    }}
    slider.addEventListener('input', draw);
    draw();
  </script>
</body>
</html>
"""


def render_tex(note: dict[str, Any]) -> str:
    def itemize(items: list[str]) -> str:
        return "\\begin{itemize}\n" + "\n".join(f"\\item {tex_escape(i)}" for i in items) + "\n\\end{itemize}\n"

    symbols = "\n".join(
        f"{tex_escape(s[0])} & {tex_escape(s[1])} & {tex_escape(s[2])} & {tex_escape(s[3])} \\\\"
        for s in note["methodology"]["symbols"]
    )
    concepts = "\n".join(
        f"{tex_escape(c[0])} & {tex_escape(c[1])} & {tex_escape(c[2])} \\\\"
        for c in note["concepts"]
    )
    anchors = "\n".join(
        f"p.{a['page']} & {tex_escape(a['heading'])} \\\\"
        for a in note["source_facts"]["source_anchors"]
    )
    figure_rows = "\n".join(
        f"{tex_escape(c['zh'])} & {tex_escape(c['en'])} & {tex_escape(c['reading'])} \\\\"
        for c in note["experiments"]["figure_table_cues"]
    )
    section_map = "\n".join(
        f"\\paragraph{{p.{s['page']} {tex_escape(s['heading'])}}}{tex_escape(s['zh'])} / {tex_escape(s['en'])}\n"
        for s in note["section_map"]
    )
    spec = note["visualization"]["interactive"]
    return rf"""\documentclass[UTF8,a4paper,11pt,fontset=fandol]{{ctexart}}
\usepackage{{geometry}}
\geometry{{margin=2.2cm}}
\usepackage{{amsmath,amssymb,longtable,booktabs,array,hyperref,xcolor,enumitem}}
\hypersetup{{colorlinks=true,linkcolor=blue,urlcolor=blue}}
\setlist[itemize]{{leftmargin=1.3em,itemsep=0.2em}}
\definecolor{{notegray}}{{RGB}}{{246,248,251}}
\title{{{tex_escape(note['id'])}. {tex_escape(note['title'])}\\中英双语博士精读笔记}}
\author{{{tex_escape(note['authors'])}}}
\date{{{tex_escape(str(note['year']))} · {tex_escape(note['venue'])}}}
\begin{{document}}
\maketitle

\noindent\textbf{{Theme / 主题：}} {tex_escape(note['theme'])}\\
\textbf{{Method family / 方法族：}} {tex_escape(note['method_family'])}\\
\textbf{{PDF pages / 页数：}} {note['source_facts']['page_count']} \quad
\textbf{{Relevance / 相关度：}} {note['relevance']}/100\\
\textbf{{Source / 来源：}} \url{{{note['source_url']}}}

\section{{论文全景速览与核心贡献 / High-Level Overview \& Core Contributions}}
\subsection{{研究背景与痛点 / Background \& Pain Points}}
{tex_escape(note['overview']['background_zh'])}

{tex_escape(note['overview']['background_en'])}

\textbf{{Pain point / 痛点：}} {tex_escape(note['overview']['pain_zh'])}

\subsection{{核心科学问题 / Core Scientific Question}}
{tex_escape(note['overview']['core_question_zh'])}

{tex_escape(note['overview']['core_question_en'])}

\subsection{{科学贡献 / Scientific Contributions}}
{itemize(note['overview']['contributions'])}

\subsection{{核心概念对照 / Core Concepts}}
\begin{{longtable}}{{p{{0.24\linewidth}}p{{0.28\linewidth}}p{{0.40\linewidth}}}}
\toprule
中文概念 & English Concept & Role / 学术作用\\
\midrule
{concepts}
\bottomrule
\end{{longtable}}

\section{{理论方法论深度解构 / Methodology \& Theoretical Framework}}
\subsection{{问题数学建模 / Mathematical Formulation}}
\textbf{{{tex_escape(note['methodology']['model_name'])}}}
\[
{note['methodology']['formula']}
\]
\begin{{longtable}}{{p{{0.16\linewidth}}p{{0.25\linewidth}}p{{0.25\linewidth}}p{{0.25\linewidth}}}}
\toprule
Symbol / 符号 & 含义 & Meaning & Role / 建模作用\\
\midrule
{symbols}
\bottomrule
\end{{longtable}}

\subsection{{核心算法架构 / Core Algorithm Layout}}
{tex_escape(note['methodology']['algorithm_zh'])}

{tex_escape(note['methodology']['algorithm_en'])}

\subsection{{收敛性、稳定性或实时性 / Convergence, Stability, Real-Time Feasibility}}
{tex_escape(note['methodology']['stability_zh'])}

{tex_escape(note['methodology']['stability_en'])}

\subsection{{潜在假设与边界条件 / Assumptions \& Boundary Conditions}}
{itemize(note['methodology']['assumptions'])}

\section{{实验验证与结果评判 / Experimental Validation \& Result Evaluation}}
\textbf{{Baselines \& Environment / 基准与环境：}} {tex_escape(note['experiments']['baselines'])}

\textbf{{Validation / 验证：}} {tex_escape(note['experiments']['validation'])}

\textbf{{Metrics / 指标：}} {tex_escape(note['experiments']['metrics'])}

\textbf{{Ablation / 消融：}} {tex_escape(note['experiments']['ablation'])}

\textbf{{Reviewer reading / 审稿式阅读提醒：}} {tex_escape(note['experiments']['reviewer_reading'])}

\subsection{{图表阅读线索 / Figure and Table Reading Cues}}
PDF extraction detected approximately {note['source_facts']['figure_reference_count']} figure references and {note['source_facts']['table_reference_count']} table references. Exact captions remain in the original PDF; the bilingual cues below tell you what to inspect first.

\begin{{longtable}}{{p{{0.24\linewidth}}p{{0.30\linewidth}}p{{0.36\linewidth}}}}
\toprule
图表名称 & Figure/Table Name & Reading focus / 阅读重点\\
\midrule
{figure_rows}
\bottomrule
\end{{longtable}}

\section{{审稿人视角：批判性思考与未来方向 / Critical Thinking \& Future Directions}}
\subsection{{论文局限性 / Limitations \& Weaknesses}}
{itemize(note['critique']['limitations'])}

\subsection{{博士课题拓展点 / Research Extensions for PhD}}
{itemize(note['critique']['extensions'])}

\subsection{{如何服务当前课题 / Use in This Project}}
{tex_escape(note['critique']['project_use'])}

\section{{交互式可视化与 PDF 排版蓝图 / Interactive Visualization \& PDF Layout Blueprint}}
\textbf{{动态参数 / Parameter：}} {tex_escape(spec['label_zh'])} / {tex_escape(spec['label_en'])}, range [{spec['min_value']}, {spec['max_value']}] {tex_escape(spec['unit'])}.

{tex_escape(spec['response_zh'])}

{tex_escape(spec['response_en'])}

\subsection{{HTML 结构化布局建议 / HTML Structuring}}
{itemize(note['visualization']['html_structure'])}

\section{{来源锚点与逐节阅读路径 / Source Anchors \& Section-by-Section Reading Map}}
\begin{{longtable}}{{p{{0.14\linewidth}}p{{0.76\linewidth}}}}
\toprule
Page & Extracted heading\\
\midrule
{anchors}
\bottomrule
\end{{longtable}}

{section_map}

\end{{document}}
"""


def write_index(notes: list[dict[str, Any]]) -> None:
    rows = []
    for n in notes:
        slug = slug_for(n)
        rel = f"papers/{slug}/{slug}"
        rows.append(
            f"<tr><td>{html.escape(n['id'])}</td><td>{html.escape(n['title'])}</td><td>{html.escape(n['method_family'])}</td>"
            f"<td>{n['source_facts']['page_count']}</td><td>{n['relevance']}</td>"
            f"<td><a href='{rel}.html'>HTML</a></td><td><a href='{rel}.pdf'>PDF</a></td></tr>"
        )
    index = f"""<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Deep Reading Notes Index</title>
  <style>
    body {{ margin:0; font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif; color:#1d2733; }}
    header {{ padding:28px 34px; background:#f3f6fa; border-bottom:1px solid #d9e1ea; }}
    main {{ padding:24px 34px 50px; }}
    h1 {{ margin:0 0 8px; font-size:30px; }}
    table {{ width:100%; border-collapse:collapse; }}
    th,td {{ border:1px solid #d9e1ea; padding:9px; vertical-align:top; }}
    th {{ background:#eef3f7; text-align:left; }}
    a {{ color:#1f5f8b; }}
    .hint {{ color:#657386; max-width:980px; }}
    @media print {{ body {{ font-size:11px; }} header,main {{ padding:16px 20px; }} }}
  </style>
</head>
<body>
  <header>
    <h1>P01-P15 双语博士精读笔记 / Bilingual Deep Reading Notes</h1>
    <p class="hint">每篇论文都有独立 HTML、PDF、TeX 和结构化 JSON。HTML 支持目录跳转、语言切换、打印导出和参数曲线交互。</p>
  </header>
  <main>
    <table>
      <tr><th>ID</th><th>Paper</th><th>Method family / 方法族</th><th>PDF pages</th><th>Score</th><th>HTML</th><th>PDF</th></tr>
      {''.join(rows)}
    </table>
  </main>
</body>
</html>
"""
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "index.html").write_text(index, encoding="utf-8")


def compile_tex(tex_path: Path) -> bool:
    latexmk = shutil.which("latexmk")
    if not latexmk:
        return False
    proc = subprocess.run(
        [
            latexmk,
            "-xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex_path.name,
        ],
        cwd=tex_path.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode != 0:
        (tex_path.parent / "latexmk_failure.log").write_text(proc.stdout, encoding="utf-8")
        return False
    failure_log = tex_path.parent / "latexmk_failure.log"
    if failure_log.exists():
        failure_log.unlink()
    for suffix in (
        ".aux",
        ".fdb_latexmk",
        ".fls",
        ".log",
        ".out",
        ".xdv",
        ".toc",
        ".lof",
        ".lot",
    ):
        artifact = tex_path.with_suffix(suffix)
        if artifact.exists():
            artifact.unlink()
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile", action="store_true", help="Compile each generated TeX file with latexmk -xelatex.")
    args = parser.parse_args()

    papers = json.loads(PAPERS_JSON.read_text(encoding="utf-8"))
    notes: list[dict[str, Any]] = []
    for paper in papers:
        if paper["id"] not in DETAILS:
            continue
        slug = slug_for(paper)
        pdf = find_pdf(paper)
        facts = extract_pdf_facts(pdf)
        note = synthesize_note(paper, facts)
        notes.append(note)
        out_dir = OUTPUT_ROOT / "papers" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json(note, out_dir, slug)
        (out_dir / f"{slug}.html").write_text(render_html(note), encoding="utf-8")
        tex_path = out_dir / f"{slug}.tex"
        tex_path.write_text(render_tex(note), encoding="utf-8")
        if args.compile:
            ok = compile_tex(tex_path)
            print(f"{paper['id']} {slug}: {'compiled' if ok else 'compile failed'}")
        else:
            print(f"{paper['id']} {slug}: generated")
    write_index(notes)
    manifest = {
        "output_root": str(OUTPUT_ROOT.relative_to(ROOT)),
        "paper_count": len(notes),
        "html_count": len(list((OUTPUT_ROOT / "papers").glob("*/*.html"))),
        "tex_count": len(list((OUTPUT_ROOT / "papers").glob("*/*.tex"))),
        "pdf_count": len(list((OUTPUT_ROOT / "papers").glob("*/*.pdf"))),
        "notes": [
            {
                "id": n["id"],
                "bibkey": n["bibkey"],
                "title": n["title"],
                "html": f"papers/{slug_for(n)}/{slug_for(n)}.html",
                "pdf": f"papers/{slug_for(n)}/{slug_for(n)}.pdf",
                "json": f"papers/{slug_for(n)}/{slug_for(n)}_notes.json",
            }
            for n in notes
        ],
    }
    (OUTPUT_ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Index: {OUTPUT_ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
