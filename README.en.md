# Fusion Development System — Engineering Implementation

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Standard](https://img.shields.io/badge/standard-DO--178C-red.svg)](projects/sr1/.pla/environment/constraints/do178c.yaml)

> A multi-agent collaborative development environment for airborne software — PLA (Process Lifecycle Agent) as a five-layer closed-loop controller orchestrating 14 DA (Domain Agent) agents through file-based message channels.

**Validation target**: Airborne software development process management
**Languages**: C (airborne software), Python (infrastructure)
**Compilers**: GCC (host) + arm-none-eabi-gcc (Cortex-M4) | **Standard**: DO-178C

---

## Table of Contents

- [Overview](#overview)
- [Core Architecture](#core-architecture)
- [Directory Structure](#directory-structure)
- [PLA Five-Layer Closed Loop](#pla-five-layer-closed-loop)
- [14 Domain Agents](#14-domain-agents)
- [Fusion Development Strategy](#fusion-development-strategy)
- [DAL-Adaptive Strategy](#dal-adaptive-strategy)
- [Quick Start](#quick-start)
- [SR-1 Walkthrough Case](#sr-1-walkthrough-case)
- [Adding a New Project](#adding-a-new-project)
- [License](#license)

---

## Overview

The Fusion Development System integrates two complementary development paths:

| Path | Method | Best for |
|------|--------|----------|
| **Model-Driven** | SysML/UML → model transformation → code generation | Architecture design, detailed design, code generation |
| **LLM-Driven** | Large language model reasoning | Requirements analysis, document generation, test case generation |

The PLA dynamically selects the path per activity based on activity type and DAL level, enforced through a five-layer closed-loop control that guarantees process quality and artifact consistency.

### Why File-Based Message Channels

| Property | Benefit |
|----------|---------|
| **Decoupling** | PLA and DAs start, run, and debug independently |
| **Traceability** | Every message is a persistent JSON file — a natural audit log |
| **Airworthiness compliance** | DO-178C requires auditable processes — file channels satisfy this natively |
| **Offline collaboration** | Humans inject decisions at gates; DAs continue after queue file edits |

### Key Insight

**PLA and all 14 DAs are independent AI Agents — not Python classes, functions, or modules.**

- Each Agent is defined by an `AGENT.md` (system prompt + I/O contract + available tools + constraints)
- Agents communicate via file-based message channels (`queue/outbox/` ↔ `queue/inbox/`)
- DAs call engineering resource tools internally (GCC, PlantUML, LLM API, Git, etc.)

---

## Core Architecture

```
Lifecycle Control Layer (PLA Agent) — 5-layer orchestration
     L1 Perceive → L2 Decide → L3 Execute → L4 Correct → L5 Steady State
        ↓ Task Context (JSON files)
Domain Capability Layer (14 DA Agents) — organized by capability category
    Understanding → Generation → Modeling → Verification → Traceability/Evidence
        ↓ Execution requests (tool calls)
Engineering Resource Layer — concrete tools and services
    CLI (GCC/PlantUML/Git/Make) | API (LLM inference/ReqIF import) | Human (review gates)
```

### Three Information Flows

| Flow | Direction | Content |
|------|-----------|---------|
| Command Flow ↓ | L2 → L3 → DA | Task instructions, context, constraints |
| Evidence Flow ↑ | DA → L1 → L2 + L5 | Execution artifacts, process data, logs |
| Deviation Flow ↔ | DA → L1 → L4 → L2 | Anomaly signals, correction requests |

---

## Directory Structure

```
fusion/
├── agents/                     # Agent definitions (AGENT.md prompts, not Python classes)
│   ├── pla/                    #   PLA — five-layer closed-loop controller
│   │   ├── AGENT.md            #     System prompt and contract
│   │   ├── perception.py       #     L1 perception layer
│   │   ├── planner.py          #     L2 decision layer
│   │   └── baseline.py         #     Artifact baseline control
│   ├── da-01/AGENT.md          #   DA-01 Requirements Analysis (Understanding)
│   ├── da-02/AGENT.md          #   DA-02 Requirements Decomposition (Generation)
│   ├── da-03/AGENT.md          #   DA-03 Model Building (Modeling)
│   ├── da-04/AGENT.md          #   DA-04 Model Checking (Verification)
│   ├── da-05/AGENT.md          #   DA-05 Code Generation (Generation)
│   ├── da-06/AGENT.md          #   DA-06 Code Checking (Verification)
│   ├── da-07/AGENT.md          #   DA-07 Test Scenario Analysis (Understanding)
│   ├── da-08/AGENT.md          #   DA-08 Test Case Generation (Generation)
│   ├── da-09/AGENT.md          #   DA-09 Test Procedure Generation (Generation)
│   ├── da-10/AGENT.md          #   DA-10 Test Execution (Tool Execution)
│   ├── da-11/AGENT.md          #   DA-11 Verification Analysis (Verification)
│   ├── da-12/AGENT.md          #   DA-12 Traceability Maintenance (Relationship)
│   ├── da-13/AGENT.md          #   DA-13 Review Materials (Evidence)
│   └── da-14/AGENT.md          #   DA-14 Airworthiness Evidence (Evidence)
├── runtime/                    # Communication infrastructure (pure transport, no PLA intelligence)
│   ├── protocol.py             #   Task Context / Execution Result protocol
│   ├── channel.py              #   File-based message channel
│   ├── orchestrator.py         #   PLA-DA communication orchestrator
│   ├── task_plan.py            #   TaskPlan / TaskItem / CheckItem data structures
│   └── result_validator.py     #   DA result format validator
├── tools/                      # Engineering resource tools
│   ├── registry.py             #   Tool registry + DA tool assignment
│   ├── gcc.py                  #   GCC compiler wrapper
│   └── git.py                  #   Git version control wrapper
├── examples/                   # Configuration templates (fully annotated)
│   ├── README.md              #   Template usage guide
│   ├── environment/           #   Environment config templates
│   │   ├── config.yaml        #     Infrastructure configuration
│   │   └── constraints/       #     Standards constraints templates
│   │       ├── do178c.yaml    #       DO-178C full objective table
│   │       ├── do331.yaml     #       DO-331 MBE supplement
│   │       └── company.yaml   #       Company-level standards
│   ├── queue/                 #   Message queue structure template
│   │   ├── outbox/
│   │   └── inbox/
│   ├── evidence/              #   Evidence templates (checklist, task plan, trace matrix)
│   └── projects/
│       └── config.yaml        #     Project configuration template
├── projects/                   # Project directories (one per SR)
│   └── sr1/                   #   SR-1 walkthrough case
│       ├── config.yaml        #   Project-specific constraints (DAL D, applicable objectives)
│       ├── Makefile            #   Build system (dual compiler: Host + Cortex-M4)
│       ├── .pla/               #   PLA runtime directory (env/queue/dispatch, non-artifact)
│       │   ├── README.md
│       │   ├── environment/   #     Engineering env (initialized from examples/)
│       │   └── queue/         #     Runtime message queues
│       ├── requirements/      #   SR / HLR / LLR requirements documents
│       ├── models/            #   SysML models
│       ├── src/               #   C source code (main.c, sr1.c, sr1.h)
│       ├── tests/             #   Test cases and procedures
│       └── evidence/          #   Process evidence and traceability matrices
├── AGENTS.md                   # Workspace context rules
├── LICENSE                     # Apache 2.0
└── README.md                   # This file (Chinese)
```

---

## PLA Five-Layer Closed Loop

Layers L1–L4 form an "Adjust–Confirm–Converge" cycle:

| Layer | Name | Responsibility |
|-------|------|----------------|
| **L1** | Perception | Read SR and project config; continuously collect DA execution state; detect deviation signals (quality gaps, constraint conflicts, coverage gaps, execution failures) |
| **L2** | Decision | Dynamically generate Task DAG; select development path (model/LLM/fusion); inject DAL constraints; flag human gate nodes |
| **L3** | Execution | Package Task Context → write to queue → DA reads and executes → read result. Does NOT judge correctness |
| **L4** | Correction | Analyze L1 deviation signals; generate five correction strategies (add/remove/reorder/adjust params/adjust conditions); feed back to L2 for re-orchestration |
| **L5** | Steady State | Continuously collect process data and execution records; maintain evidence coverage matrix; archive as airworthiness evidence |

### Convergence Mechanism

```
L1 Perceive ──deviation signal──→ L4 Correct ──correction strategy──→ L2 Re-orchestrate
   ↑                                                                       │
   └────────────────── New Task Plan (DAG version+1) ←─────────────────────┘
```

Iteration continues until convergence or a human gate is triggered. **Convergence is driven by PLA inter-layer information flow, not a Python while loop.**

### Correction Strategies (L4 → L2)

1. **Add DA node** — supplement missing capability
2. **Remove DA node** — eliminate redundant execution
3. **Reorder DAs** — adjust execution sequence
4. **Adjust parameters** — modify inputs/constraints
5. **Adjust conditions** — modify branching/decision logic

---

## 14 Domain Agents

DAs are organized into five capability categories:

| Category | Description | DAs |
|----------|-------------|-----|
| Understanding | Read artifacts, extract structured information | DA-01, DA-07 |
| Generation | Generate new artifacts from inputs | DA-02, DA-05, DA-08, DA-09 |
| Modeling | Build and check SysML/UML models | DA-03, DA-04 |
| Verification | Check artifact correctness and consistency | DA-06, DA-11 |
| Relationship/Evidence | Maintain traceability chains and evidence packages | DA-12, DA-13, DA-14 |

| # | DA Name | Category | Agent File | Core Responsibility |
|---|---------|----------|-----------|---------------------|
| DA-01 | Requirements Analysis | Understanding | agents/da-01/AGENT.md | SR → structured analysis → flag ambiguities. Never decomposes or invents |
| DA-02 | Requirements Decomposition | Generation | agents/da-02/AGENT.md | SR→HLR or HLR→LLR (one level per activity, no cross-layer jumps) |
| DA-03 | Model Building | Modeling | agents/da-03/AGENT.md | Stage-aware: S0-S3 SysML(.sysml), S4-S6 UML(.puml) |
| DA-04 | Model Checking | Verification | agents/da-04/AGENT.md | Verify model syntax and consistency |
| DA-05 | Code Generation | Generation | agents/da-05/AGENT.md | UML detailed design model → C code |
| DA-06 | Code Checking | Verification | agents/da-06/AGENT.md | GCC compilation + standards compliance checks |
| DA-07 | Test Scenario Analysis | Understanding | agents/da-07/AGENT.md | Identify verification scenarios from requirements |
| DA-08 | Test Case Generation | Generation | agents/da-08/AGENT.md | Scenarios → test cases (tabular, DO-178C traceable) |
| DA-09 | Test Procedure Generation | Generation | agents/da-09/AGENT.md | Cases → executable step-by-step procedures |
| DA-10 | Test Execution | Tool Execution | agents/da-10/AGENT.md | Compile → run → write results. Executes only, does not analyze |
| DA-11 | Verification Analysis | Verification | agents/da-11/AGENT.md | Analyze test results, verify DA-10 output quality |
| DA-12 | Traceability Maintenance | Relationship | agents/da-12/AGENT.md | Build traceability matrix from existing artifacts. Never generates new content |
| DA-13 | Review Materials | Evidence | agents/da-13/AGENT.md | Collect artifacts → prepare review materials |
| DA-14 | Airworthiness Evidence | Evidence | agents/da-14/AGENT.md | Package airworthiness evidence |

### DA Tool Assignment

DAs declare **tool requirements** (capability categories) in AGENT.md, never specific tool names. Actual tool-to-DA mapping lives in project configuration:

```
DA AGENT.md (tool requirement)    Project config.yaml (tool assignment)
─────────────────────────────    ──────────────────────────────────
"needs modeling tool"      →     model-build: [plantuml, llm_api]
"needs compiler"           →     code-gen:    [gcc, llm_api]
```

Global defaults are in `projects/{id}/.pla/environment/config.yaml`. Projects override via `projects/{id}/config.yaml`. Example:

```yaml
# projects/sr2/config.yaml — project standard bans UML, uses IDEF0
da_tools:
  model-build:  [idef0, llm_api]
  model-check:  [idef0, llm_api]
```

This requires only adding `idef0` to the tool registry — no DA AGENT.md files need modification.

---

## Fusion Development Strategy

The PLA dynamically selects the development path per activity:

### Path Decision

**Activity type → static path mapping + DAL-adaptive dynamic routing**

- Critical activities (e.g., HLR generation): both paths run in parallel, cross-validate
- DAL A/B: model-driven path enforced
- DAL D/E: LLM-driven path permitted

| Activity Type | Description | Default Path | DAs Involved |
|---------------|-------------|-------------|--------------|
| sr_analysis | System requirements analysis | LLM-preferred | DA-01 |
| sr_to_hlr | SR→HLR decomposition | Fusion | DA-01, DA-02, DA-12 |
| hlr_to_llr | HLR→LLR decomposition | Fusion | DA-02, DA-12 |
| architecture_model | Architecture modeling | Model-preferred | DA-03, DA-04 |
| detailed_design | Detailed design | Fusion | DA-03, DA-04 |
| code_generation | Code generation | Model-driven | DA-05, DA-06, DA-12 |
| test_case_gen | Test case generation | Fusion | DA-07, DA-08, DA-09, DA-12 |
| test_execution | Test execution | Model-driven | DA-10 |
| verification | Verification analysis | Fusion | DA-11, DA-12 |
| review_prep | Review materials prep | Fusion | DA-13 |
| evidence_pack | Evidence packaging | Fusion | DA-14 |

---

## DAL-Adaptive Strategy

The PLA adjusts development rigor based on DAL level:

| DAL | Path Selection | Verification Granularity | Human Intervention | Typical Use |
|-----|---------------|-------------------------|-------------------|-------------|
| **A** | Deterministic tools only | Full record, per-item confirmation | Per-node independent review | Flight controls |
| **B** | Deterministic tools only | Full record, per-item confirmation | Per-node independent review | Navigation systems |
| **C** | Deterministic primary, LLM limited | Standard record, spot-check | Spot-check review | Communication systems |
| **D** | LLM allowed | Simplified, auto-confirm | Exception-triggered only | Display systems |
| **E** | LLM preferred | Simplified, auto-confirm | Exception-triggered only | Non-critical functions |

### Human Gates

The PLA embeds 5 types of controlled pause points in the Task DAG. Gates do not block the automation mainline — independent parallel tasks continue.

| Gate | Trigger |
|------|---------|
| Initial Plan Authorization | DAL A/B required, DAL C optional |
| DA Path Selection | LLM path + DAL ≥ C |
| Verification Confirmation | Test gaps or deviation threshold exceeded |
| Change Impact Assessment | Cross-layer impact detected |
| Evidence Archive Sign-off | L5 evidence package ready |

---

## Quick Start

### Prerequisites

- Python 3.10+
- GCC (host compilation)
- arm-none-eabi-gcc 13+ (embedded cross-compilation, optional)

### Build and Run SR-1

```bash
# Install Python dependencies
pip install -r requirements.txt

# Clone the repository
git clone git@github.com:xbhlhs/cyber-ac.git
cd fusion

# Local build + run (fast development iteration)
make -C projects/sr1

# Dual compiler verification (Host GCC + Cortex-M4 arm-none-eabi-gcc)
make -C projects/sr1 all

# View embedded assembly
make -C projects/sr1 embedded-asm

# Clean build artifacts
make -C projects/sr1 clean
```

### Run PLA Orchestration

The PLA Agent orchestrates DAs through file-based message channels:

```bash
# PLA initiates a development activity (e.g., requirements decomposition)
python -m runtime.orchestrator --activity sr_to_hlr --dal D
```

### Communication Protocol

**PLA → DA (Task Context)**:

```json
{
  "task_id": "sr_to_hlr-T02",
  "task_name": "Requirements Decomposition",
  "da_name": "req-decomp",
  "activity_type": "sr_to_hlr",
  "description": "Decompose SR into candidate HLR",
  "inputs": {"sr": "projects/sr1/requirements/sr.md"},
  "expected_outputs": ["projects/sr1/requirements/hlr.md"],
  "constraints": {"dal_level": "C", "development_path": "fusion"},
  "human_gate_after": true,
  "human_gate_type": "initial_plan"
}
```

**DA → PLA (Execution Result)**:

```json
{
  "task_id": "...",
  "status": "completed",
  "artifacts": ["projects/sr1/requirements/hlr.md"],
  "process_data": {"reasoning": "...", "decisions": ["..."]},
  "requires_human_review": true
}
```

---

## SR-1 Walkthrough Case

SR-1 is a complete airborne software module development case spanning the full lifecycle: SR → HLR → LLR → C code → Compilation → Testing → Evidence.

| Property | Value |
|----------|-------|
| **Function** | Three-device (EQA/EQB/EQC) input synthesis computation |
| **DAL Level** | D (25 DO-178C objectives) |
| **Compilers** | GCC (host) + arm-none-eabi-gcc (Cortex-M4) |
| **Language standard** | C11, no dynamic memory allocation |
| **Artifacts** | 1 SR + 9 HLR + 10 LLR + 3 C files + 11 test cases |
| **Evidence** | Traceability matrix, code check report, test results, verification analysis |

---

## Adding a New Project

```bash
# 1. Create project directory
mkdir -p projects/sr2/{requirements,models,src,tests,evidence}

# 2. Initialize .pla/ runtime environment (copy from templates)
cp -r examples/environment projects/sr2/.pla/environment

# 3. Write project configuration
cat > projects/sr2/config.yaml << 'EOF'
project:
  id: "SR-2"
  name: "YOUR_FUNCTION"
  dal_level: "C"
project_path_constraints:
  model_policy: "as_dal"
EOF

# 4. Write system requirements
# projects/sr2/requirements/sr.md

# 5. Start PLA orchestration
python -m runtime.orchestrator --project sr2 --activity sr_to_hlr --dal C
```

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).
