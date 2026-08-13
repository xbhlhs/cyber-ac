# 融合开发体系 — 工程实现

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Standard](https://img.shields.io/badge/standard-DO--178C-red.svg)](examples/environment/constraints/do178c.yaml)

> 面向机载软件的多Agent协同研发环境——PLA五层闭环控制器 + 16个DA领域能力执行器，通过文件消息通道通信。

**验证对象**：机载软件研发过程管理 | **实现语言**：C (机载软件本体), Python (基础设施)
**编译器**：GCC (host) | **标准**：DO-178C

---

## 目录

- [概述](#概述)
- [核心架构](#核心架构)
- [目录结构](#目录结构)
- [PLA五层闭环](#pla五层闭环)
- [16个DA Agent](#16个da-agent)
- [Agent spawn 模式](#agent-spawn-模式)
- [融合开发策略](#融合开发策略)
- [DAL自适应](#dal自适应)
- [快速开始](#快速开始)
- [SR-1 贯穿案例](#sr-1-贯穿案例)
- [新增项目](#新增项目)
- [许可证](#许可证)

---

## 概述

融合开发体系将**模型驱动开发**（SysML/UML → 代码生成）和**LLM驱动开发**（需求分析 → 文档生成）两条路径有机结合。PLA (Process Lifecycle Agent) 根据活动类型和DAL级别动态选择路径，通过五层闭环控制保证过程质量和制品一致性。

### 为什么是文件消息通道

| 特性 | 说明 |
|------|------|
| **解耦** | PLA和DA可以独立启动、运行、调试 |
| **可追溯** | 每条消息是持久化的JSON文件，天然形成审计日志 |
| **适航合规** | DO-178C要求过程可审计——文件通道天然满足 |
| **离线协作** | 人类可在闸门处插入决策，修改队列文件后DA继续 |

### 关键认知

**PLA和16个DA都是独立的AI Agent，不是Python类、函数或模块。**

- 每个Agent由 `AGENT.md` 定义（系统提示词 + 输入输出契约 + 可用工具 + 约束）
- Agent之间通过文件消息通道通信（`queue/outbox/` ↔ `queue/inbox/`）
- DA内部可以调用工程资源工具（GCC, PlantUML, LLM API, Git等）

---

## 核心架构

```
生命周期控制层 (PLA Agent) — 五层闭环编排
     L1感知 → L2决策 → L3执行 → L4校正 → L5稳态
        ↓ Task Context (JSON文件)
领域能力层 (16个DA Agent) — 按能力类别分工
    理解分析 → 内容生成 → 模型处理 → 校验分析 → 关系证据
        ↓ 执行请求 (工具调用)
工程资源层 — 具体工具和服务
    CLI (GCC/PlantUML/Git/Make) | API (LLM推理/ReqIF导入) | Human (评审闸门)
```

### 三股信息流

| 流 | 方向 | 内容 |
|----|------|------|
| 指令流 ↓ | L2 → L3 → DA | 任务指令、上下文、约束条件 |
| 证据流 ↑ | DA → L1 → L2 + L5 | 执行产物、过程数据、日志 |
| 偏差流 ↔ | DA → L1 → L4 → L2 | 异常信号、校正请求 |

---

## 目录结构

```
fusion/
├── agents/                     # Agent定义 (AGENT.md提示词, 非Python类)
│   ├── pla/                    #   PLA — 五层闭环控制器
│   │   ├── AGENT.md            #     系统提示词与契约
│   │   ├── perception.py       #     L1感知层实现
│   │   ├── planner.py          #     L2决策层实现
│   │   ├── baseline.py         #     制品基线控制
│   │   └── da_tracker.py       #     DA运行时状态追踪
│   ├── da-01/AGENT.md          #   DA-01 需求分析 (理解分析类)
│   ├── da-02/AGENT.md          #   DA-02 需求分解 (内容生成类)
│   ├── da-03/AGENT.md          #   DA-03 模型构建 (模型处理类)
│   ├── da-04/AGENT.md          #   DA-04 模型检查 (校验分析类)
│   ├── da-05/AGENT.md          #   DA-05 代码生成 (内容生成类)
│   ├── da-06/AGENT.md          #   DA-06 代码检查 (校验分析类)
│   ├── da-07/AGENT.md          #   DA-07 测试场景分析 (理解分析类)
│   ├── da-08/AGENT.md          #   DA-08 测试用例生成 (内容生成类)
│   ├── da-09/AGENT.md          #   DA-09 测试规程生成 (内容生成类)
│   ├── da-10/AGENT.md          #   DA-10 测试执行 (工具执行类)
│   ├── da-11/AGENT.md          #   DA-11 验证分析 (校验分析类)
│   ├── da-12/AGENT.md          #   DA-12 追溯关系维护 (关系处理类)
│   ├── da-13/AGENT.md          #   DA-13 评审材料整理 (证据处理类)
│   ├── da-14/AGENT.md          #   DA-14 适航证据整理 (证据处理类)
│   ├── da-15/AGENT.md          #   DA-15 设计 (理解分析+内容生成类)
│   └── da-16/AGENT.md          #   DA-16 设计检查 (校验分析类)
├── runtime/                    # 通信基础设施 (纯通信层，不含PLA智能)
│   ├── protocol.py             #   Task Context / Execution Result 协议定义
│   ├── channel.py              #   文件消息通道实现
│   ├── orchestrator.py         #   PLA-DA纯通信编排器
│   ├── task_plan.py            #   TaskPlan / TaskItem / CheckItem 数据结构
│   └── result_validator.py     #   DA结果格式验证器
├── tools/                      # 工程资源工具
│   ├── registry.py             #   工具注册表 + DA工具/模型分配
│   ├── gcc.py                  #   GCC编译器包装器
│   └── git.py                  #   Git版本管理包装器
├── scripts/                    # 项目初始化脚本
│   └── init_project.py         #   按DAL裁切约束的项目初始化
├── examples/                   # 配置模板示例 (全量注释版)
│   ├── environment/           #   工程环境配置模板
│   │   ├── config.yaml        #     基础设施配置
│   │   └── constraints/       #     标准规范约束模板
│   │       ├── do178c.yaml    #       DO-178C完整目标表
│   │       ├── do331.yaml     #       DO-331 MBE补充
│   │       └── company.yaml   #       公司级规范
│   ├── queue/                 #   消息队列结构模板
│   ├── evidence/              #   证据模板
│   └── projects/config.yaml   #   项目配置模板
├── projects/                   # 项目目录 (每个SR一个子目录，不入库)
│   └── {project_id}/          #   例: sr1-formal
│       ├── config.yaml        #   项目特定约束 (DAL, 适用目标, 里程碑)
│       ├── project_specs.md   #   项目规范 (评审/打包/建模要求)
│       ├── .pla/               #   PLA运行时目录 (环境/队列/基线, 非制品)
│       │   ├── environment/   #     工程环境 (从 examples/ 初始化)
│       │   ├── queue/         #     运行时消息队列 (inbox/outbox)
│       │   ├── agents/        #     DA专属AGENTS.md软链
│       │   └── .baseline.json #     基线状态库
│       ├── requirements/      #   SR / HLR / LLR 需求文档
│       ├── designs/           #   设计方案 (DA-15产出)
│       ├── models/            #   UML模型
│       ├── src/               #   C源代码
│       ├── tests/             #   测试用例和规程
│       └── evidence/          #   过程证据和追溯矩阵
├── AGENTS.md                   # 工作区上下文规则
├── LICENSE                     # Apache 2.0
└── README.md                   # 本文件
```

---

## PLA五层闭环

PLA的L1-L4层形成“调整—确认—收敛”闭环：

| 层 | 名称 | 职责 |
|----|------|------|
| **L1** | 感知层 | 读取SR和项目配置，持续收集DA执行状态，检测偏差信号（质量缺口、约束冲突、覆盖缺失、执行失败） |
| **L2** | 决策层 | 动态生成Task DAG，选择开发路径（模型/LLM/融合），注入DAL约束，识别人工闸门节点 |
| **L3** | 执行层 | 封装Task Context → 写队列 → DA读取执行 → 读结果，不判断正确性 |
| **L4** | 校正层 | 分析L1偏差信号，生成五种校正策略（增/删/重排/调参/调条件），反馈L2重编排 |
| **L5** | 稳态层 | 持续收集过程数据和执行记录，维护证据覆盖矩阵，归档适航证据 |

### 闭环收敛机制

```
L1感知 ──偏差信号──→ L4校正 ──校正策略──→ L2重编排
   ↑                                         │
   └──────────── 新Task Plan (DAG版本号+1) ←──┘
```

循环执行直到收敛或触发人工闸门。**收敛是PLA层间信息流驱动，不是Python while循环。**

### 关键约束

- **跨阶段基线约束**：传递给 DA 的输入中，来自上一阶段的制品必须已基线化。同阶段 DAG 内的上下游任务可流转中间产物。防止幻觉传播（如虚构 HLR ID 污染下游文档）。
- **增量修改优先**：评审后优先定点修改（patch），非推倒重来。不采纳评审意见是合法响应，但须附理由。
- **L4 优先自动闭环**：DA 检查发现的 WARNING 级问题应自动修复后再提交人工闸门。
- **评审材料含响应记录**：每次提交评审的 ZIP 必须含上一轮评审意见及本次响应。

### 校正策略 (L4 → L2)

1. **增加DA节点** — 补充缺失能力
2. **移除DA节点** — 消除冗余执行
3. **重排DA顺序** — 调整执行先后
4. **调整参数** — 修改输入/约束
5. **调整条件** — 修改分支/判断逻辑

---

## 16个DA Agent

DA按能力分为六类：

| 类别 | 说明 | 包含DA |
|------|------|--------|
| 理解分析类 | 读入制品，提取结构化信息 | DA-01, DA-07 |
| 内容生成类 | 基于输入生成新制品 | DA-02, DA-05, DA-08, DA-09 |
| 模型处理类 | 构建和检查SysML/UML模型 | DA-03, DA-04 |
| 校验分析类 | 检查制品的正确性和一致性 | DA-06, DA-11, DA-16 |
| 设计类 | 设计方案分析 + 设计文档撰写 | DA-15 |
| 关系/证据类 | 维护追溯链和证据包 | DA-12, DA-13, DA-14 |

| # | DA名称 | 能力类别 | Agent文件 | 核心职责 |
|---|--------|---------|----------|---------|
| DA-01 | 需求分析 | 理解分析类 | agents/da-01/AGENT.md | SR → 结构化分析 → 标记歧义。不分解、不脑补 |
| DA-02 | 需求分解 | 内容生成类 | agents/da-02/AGENT.md | SR→HLR 或 HLR→LLR (每次一层，不跨层) |
| DA-03 | 模型构建 | 模型处理类 | agents/da-03/AGENT.md | 阶段感知建模: S0-S3 SysML(.sysml), S4-S6 UML(.puml) |
| DA-04 | 模型检查 | 校验分析类 | agents/da-04/AGENT.md | 验证模型语法和一致性 |
| DA-05 | 代码生成 | 内容生成类 | agents/da-05/AGENT.md | UML详细设计模型 → C代码 |
| DA-06 | 代码检查 | 校验分析类 | agents/da-06/AGENT.md | GCC编译 + 标准合规检查 |
| DA-07 | 测试场景分析 | 理解分析类 | agents/da-07/AGENT.md | 用户视角场景识别（全正确/一路失效/两路失效/全失效） |
| DA-08 | 测试用例生成 | 内容生成类 | agents/da-08/AGENT.md | 场景 → 用例（数据+过程+预期输出） |
| DA-09 | 测试规程生成 | 内容生成类 | agents/da-09/AGENT.md | 用例 → 可执行规程（统一规则+每例step） |
| DA-10 | 测试执行 | 工具执行类 | agents/da-10/AGENT.md | 编译 → 运行 → 写结果。只执行，不分析 |
| DA-11 | 验证分析 | 校验分析类 | agents/da-11/AGENT.md | 分析测试结果，验证DA-10输出质量 |
| DA-12 | 追溯关系维护 | 关系处理类 | agents/da-12/AGENT.md | 从已有制品构建追溯矩阵。不生成新内容 |
| DA-13 | 评审材料整理 | 证据处理类 | agents/da-13/AGENT.md | 收集制品 → 整理评审材料 → PDF + ZIP |
| DA-14 | 适航证据整理 | 证据处理类 | agents/da-14/AGENT.md | 打包适航证据 |
| DA-15 | 设计 | 理解分析+内容生成类 | agents/da-15/AGENT.md | 设计方案分析(n个模型规划) + 设计文档撰写(图文整合) |
| DA-16 | 设计检查 | 校验分析类 | agents/da-16/AGENT.md | 设计对偶检查：方案↔产出、需求覆盖、一致性 |

### 设计层对偶

设计阶段形成与模型层对称的两层对偶：

```
设计层:  DA-15 (设计)   → 生成设计文档
         DA-16 (设计检查) → 对偶检查

模型层:  DA-03 (模型构建) → 生成模型
         DA-04 (模型检查) → 语法检查
```

DA-15 分两阶段：先分析（输出 n 个模型规划，供 PLA 创建 2n 个 DA-03/04 任务），后撰写（把模型+文字整合成设计文档）。无建模场景（DAL D text_only）下 DA-15 直接产出纯文本文档，DA-16 仍执行对偶检查。

### DA工具分配

DA不在AGENT.md中硬编码工具名，而是声明**工具需求**（能力类别）。具体工具由项目配置指定：

```
DA AGENT.md (工具需求)    项目 config.yaml (工具分配)
─────────────────────    ─────────────────────────
“需要建模工具”      →     model-build: [plantuml, llm_api]
“需要编译器”        →     code-gen:    [gcc, llm_api]
```

全局默认映射在 `projects/{id}/.pla/environment/config.yaml`，项目可在 `projects/{id}/config.yaml` 中覆盖。

---

## Agent spawn 模式

PLA 和 DA 都是独立 Hermes 进程，通过 `terminal(hermes chat -q ...)` spawn，**不是** `delegate_task`。

### 角色消歧

进程角色由 spawn prompt 决定，不由工作区 AGENTS.md 决定：
- prompt 含「你作为PLA」→ 该进程**就是 PLA**，执行 L1~L5 闭环，**不得**再 spawn 另一个 PLA
- prompt 含「你作为DA-XX」→ 该进程**就是 DA-XX**，只执行本任务

### 专属 AGENTS.md 加载

每个 DA 在项目 `.pla/agents/{da-name}/AGENTS.md` 有软链指向 `agents/{da-name}/AGENT.md`。spawn 时通过 `cd &&` 让 Hermes 从该目录加载专属系统提示词：

```bash
# DA spawn (读 DA-XX 专属 AGENTS.md)
cd projects/{id}/.pla/agents/da-03 && hermes chat -q "$(cat /tmp/goal.txt)" --provider P --model M -s fusion-development

# PLA spawn (读工作区根 AGENTS.md，获取完整工程上下文)
hermes chat -q "你作为PLA，读 projects/{id}/instructions/xxx.md ..." --provider P --model M -s fusion-development
```

### Spawn prompt 最小化

驱动→PLA 和 PLA→DA 的 spawn prompt 应极简，只指向指令文档。指令文档（`projects/{id}/instructions/*.md`）包含完整上下文、上游结论、步骤指引。L2 生成 Task DAG 骨架，L3 在 dispatch 时动态生成每个 task 的执行文档（写入 `queue/outbox/{da}/task_{id}.json`），融入上游 DA 的产出结论。

---

## 融合开发策略

本体系实现两条互补的研发路径，PLA根据活动类型和DAL级别动态选择：

| 路径 | 方法 | 适用活动 | 优势 |
|------|------|---------|------|
| **模型驱动** | SysML/UML → 模型转换 → 代码生成 | 架构设计、详细设计、代码生成 | 精确性、可追踪性、确定性 |
| **LLM驱动** | 大语言模型推理 | 需求分析、文档生成、测试用例生成 | 需求理解、歧义识别、场景分析 |

### 路径决策

PLA对每个研发活动进行路径决策：**活动类型 → 路径静态映射 + DAL自适应动态路由**。

- 关键活动（如HLR生成）：两条路径并行执行后相互校验
- DAL A/B级别：强制模型优先
- DAL D/E级别：允许LLM优先

---

## DAL自适应

PLA根据DAL级别自动调整开发行为：

| DAL | 路径选择 | 验证粒度 | 人工介入 | 典型应用 |
|-----|---------|---------|---------|---------|
| **A** | 确定性工具优先 | 全记录，逐项确认 | 逐节点独立评审 | 飞控系统 |
| **B** | 确定性工具优先 | 全记录，逐项确认 | 逐节点独立评审 | 导航系统 |
| **C** | 确定性为主，LLM受限 | 标准记录，抽查 | 抽查评审 | 通信系统 |
| **D** | 允许LLM优先 | 简化，自动确认 | 仅异常触发 | 显示系统 |
| **E** | LLM优先 | 简化，自动确认 | 仅异常触发 | 非关键功能 |

### DO-178C 目标数 (按DAL)

| DAL | HLR验证 | LLR验证 | 编码验证 | 测试 | 结构覆盖 |
|-----|--------|--------|--------|------|---------|
| D | 3 | 0 | 0 | 3 | 0 |
| C | 6 | 5 | 5 | 5 | 2 |
| A/B | 7 | 7 | 6 | 5 | 4 |

### 人工闸门

PLA在Task DAG中嵌入5类可控暂停点。闸门不阻塞自动化主线——继续处理其他独立的并行任务。

| 闸门 | 触发条件 |
|------|---------|
| 初始计划授权 | DAL A/B必须，DAL C可选 |
| DA路径选择 | LLM路径 + DAL ≥ C |
| 验证确认 | 测试缺口或偏差超限 |
| 变更影响评估 | 跨层影响检测到 |
| 证据归档签批 | L5完成证据包 |

---

## 研发活动类型

| 活动类型 | 说明 | 默认路径 | 涉及DA |
|---------|------|---------|--------|
| sr_analysis | 系统需求分析 | LLM优先 | DA-01 |
| sr_to_hlr | SR→HLR分解 | 融合 | DA-01, DA-02, DA-12 |
| hlr_to_llr | HLR→LLR分解 | 融合 | DA-02, DA-12 |
| architecture_model | 架构建模 | 模型优先 | DA-03, DA-04 |
| detailed_design | 详细设计 | 融合 | DA-15, DA-03, DA-04, DA-16, DA-12 |
| code_generation | 代码生成 | 模型驱动 | DA-05, DA-06, DA-12 |
| test_case_gen | 测试用例生成 | 融合 | DA-07, DA-08, DA-09, DA-12 |
| test_execution | 测试执行 | 模型驱动 | DA-10, DA-11, DA-12 |
| verification | 验证分析 | 融合 | DA-11, DA-12 |
| review_prep | 评审材料准备 | 融合 | DA-13 |
| evidence_pack | 适航证据打包 | 融合 | DA-14 |

---

## 快速开始

### 前置条件

- Python 3.10+（唯一外部依赖 PyYAML）
- GCC (本地编译)
- pandoc + weasyprint (md→PDF，评审材料用，可选)
- PlantUML (UML/SysML 模型渲染)

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 克隆仓库
git clone git@github.com:xbhlhs/cyber-ac.git
cd fusion
```

### 项目初始化

```bash
# 从 examples/ 模板创建项目，按 DAL 裁切 DO-178C 约束
python3 scripts/init_project.py <project_id> <dal_level>

# 示例
python3 scripts/init_project.py sr1 D   # DAL D: 6 目标
```

初始化后需将 `config.yaml`（全注释模板）改写为激活配置（项目信息、路径约束、DO-178C 目标、人工闸门、里程碑），并编写 `project_specs.md` 声明项目规范。

### 运行PLA编排

PLA Agent 通过文件通道与 DA Agent 通信：

```bash
# 驱动 Agent spawn PLA (工作区根目录)
hermes chat -q "你作为PLA，读 projects/sr1/instructions/sr_to_hlr.md，按文档要求完成 SR→HLR 分解。" \
  --provider deepseek --model deepseek-v4-pro -s fusion-development
```

PLA 内部 L1~L5 闭环，L3 逐个 spawn DA：

```bash
# DA spawn (PLA L3 内部执行，读 DA 专属 AGENTS.md)
cd projects/sr1/.pla/agents/da-02 && hermes chat -q "$(cat /tmp/da_goal.txt)" \
  --provider deepseek --model deepseek-v4-pro -s fusion-development
```

### 通信协议

**PLA → DA (Task Context)**：

```json
{
  "task_id": "sr_to_hlr-T02",
  "task_name": "需求分解",
  "da_name": "req-decomp",
  "activity_type": "sr_to_hlr",
  "description": "Decompose SR into candidate HLR",
  "inputs": {"sr": "projects/sr1/requirements/sr.md"},
  "expected_outputs": ["projects/sr1/requirements/hlr.md"],
  "constraints": {"dal_level": "D", "development_path": "fusion"},
  "human_gate_after": true,
  "human_gate_type": "verification_confirm"
}
```

**DA → PLA (Execution Result)**：

```json
{
  "task_id": "...",
  "status": "completed",
  "artifacts": ["projects/sr1/requirements/hlr.md"],
  "objective_compliance": [{"objective_id": "A3-1", "status": "COMPLIED"}],
  "unresolved": []
}
```

---

## SR-1 贯穿案例

SR-1 是匿名化需求卡片，贯穿 SR → HLR → LLR → UML设计 → C代码 → 编译 → 测试 → 证据 的全生命周期路径：

| 属性 | 值 |
|------|-----|
| **功能** | FUN1数据对比输出（EQA设备软件：周期采集+有效性检查+一致性比较+条件输出） |
| **DAL级别** | D (6个DO-178C目标: A3-1/2/6 + A6-1/2/5) |
| **编译器** | GCC (host, 无目标机，模拟集成测试) |
| **语言标准** | C11, 无动态内存分配 |
| **结构** | FUN1系统模块内含 EQA/EQB/EQC，EQA为采集+对比角色 |
| **信号** | LA/LB (UINT_32), LC (BIT_2)，采样初加工信号 |

> 注意：SR-1 项目目录（`projects/sr1-formal/`）为运行案例，不入库。相关制品和过程证据按需归档。

---

## 新增项目

```bash
# 1. 初始化项目 (按 DAL 裁切约束)
python3 scripts/init_project.py sr2 C

# 2. 激活项目配置 (编辑 projects/sr2/config.yaml)
#    项目信息、路径约束、DO-178C目标、人工闸门、里程碑

# 3. 编写项目规范 (projects/sr2/project_specs.md)
#    阶段冻结评审、建模要求、评审打包、澄清流程等

# 4. 编写系统需求 projects/sr2/requirements/sr.md

# 5. 编写阶段指令 projects/sr2/instructions/sr_to_hlr.md

# 6. 驱动 Agent spawn PLA 启动编排
hermes chat -q "你作为PLA，读 projects/sr2/instructions/sr_to_hlr.md ..." -s fusion-development
```

---

## 许可证

本项目采用 [Apache License 2.0](LICENSE)。
