# 融合开发体系 — 工程实现

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Standard](https://img.shields.io/badge/standard-DO--178C-red.svg)](projects/sr1/.pla/environment/constraints/do178c.yaml)

> 面向机载软件的多Agent协同研发环境——PLA五层闭环控制器 + 14个DA领域能力执行器，通过文件消息通道通信。

**验证对象**：机载软件研发过程管理 | **实现语言**：C (机载软件本体), Python (基础设施)
**编译器**：GCC (host) + arm-none-eabi-gcc (Cortex-M4) | **标准**：DO-178C

---

## 目录

- [概述](#概述)
- [核心架构](#核心架构)
- [目录结构](#目录结构)
- [PLA五层闭环](#pla五层闭环)
- [14个DA Agent](#14个da-agent)
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

**PLA和14个DA都是独立的AI Agent，不是Python类、函数或模块。**

- 每个Agent由 `AGENT.md` 定义（系统提示词 + 输入输出契约 + 可用工具 + 约束）
- Agent之间通过文件消息通道通信（`queue/outbox/` ↔ `queue/inbox/`）
- DA内部可以调用工程资源工具（GCC, PlantUML, LLM API, Git等）

---

## 核心架构

```
生命周期控制层 (PLA Agent) — 五层闭环编排
     L1感知 → L2决策 → L3执行 → L4校正 → L5稳态
        ↓ Task Context (JSON文件)
领域能力层 (14个DA Agent) — 按能力类别分工
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
│   │   └── baseline.py         #     制品基线控制
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
│   └── da-14/AGENT.md          #   DA-14 适航证据整理 (证据处理类)
├── runtime/                    # 通信基础设施 (纯通信层，不含PLA智能)
│   ├── protocol.py             #   Task Context / Execution Result 协议定义
│   ├── channel.py              #   文件消息通道实现
│   ├── orchestrator.py         #   PLA-DA纯通信编排器
│   ├── task_plan.py            #   TaskPlan / TaskItem / CheckItem 数据结构
│   └── result_validator.py     #   DA结果格式验证器
├── tools/                      # 工程资源工具
│   ├── registry.py             #   工具注册表 + DA工具分配
│   ├── gcc.py                  #   GCC编译器包装器
│   ├── sysml.py                #   PlantUML渲染包装器
│   └── git.py                  #   Git版本管理包装器
├── examples/                   # 配置模板示例 (全量注释版)
│   ├── README.md              #   模板使用说明
│   ├── environment/           #   工程环境配置模板
│   │   ├── config.yaml        #     基础设施配置
│   │   └── constraints/       #     标准规范约束模板
│   │       ├── do178c.yaml    #       DO-178C完整目标表
│   │       ├── do331.yaml     #       DO-331 MBE补充
│   │       └── company.yaml   #       公司级规范
│   ├── queue/                 #   消息队列结构模板
│   │   ├── outbox/
│   │   └── inbox/
│   ├── evidence/              #   证据模板 (checklist, task plan, trace matrix)
│   └── projects/
│       └── config.yaml        #     项目配置模板
├── scripts/                    # 运行脚本 (run_pla.py, run_da.py)
├── projects/                   # 项目目录 (每个SR一个子目录)
│   └── sr1/                   #   SR-1 贯穿案例
│       ├── config.yaml        #   项目特定约束 (DAL D, 适用目标)
│       ├── Makefile            #   构建系统 (双编译器: Host + Cortex-M4)
│       ├── .pla/               #   PLA运行时目录 (环境/队列/调度, 非制品)
│       │   ├── README.md
│       │   ├── environment/   #     工程环境 (从 examples/ 初始化)
│       │   └── queue/         #     运行时消息队列
│       ├── requirements/      #   SR / HLR / LLR 需求文档
│       ├── models/            #   SysML模型
│       ├── src/               #   C源代码 (main.c, sr1.c, sr1.h)
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

### 校正策略 (L4 → L2)

1. **增加DA节点** — 补充缺失能力
2. **移除DA节点** — 消除冗余执行
3. **重排DA顺序** — 调整执行先后
4. **调整参数** — 修改输入/约束
5. **调整条件** — 修改分支/判断逻辑

---

## 14个DA Agent

DA按能力分为五类：

| 类别 | 说明 | 包含DA |
|------|------|--------|
| 理解分析类 | 读入制品，提取结构化信息 | DA-01, DA-07 |
| 内容生成类 | 基于输入生成新制品 | DA-02, DA-05, DA-08, DA-09 |
| 模型处理类 | 构建和检查SysML/UML模型 | DA-03, DA-04 |
| 校验分析类 | 检查制品的正确性和一致性 | DA-06, DA-11 |
| 关系/证据类 | 维护追溯链和证据包 | DA-12, DA-13, DA-14 |

| # | DA名称 | 能力类别 | Agent文件 | 核心职责 |
|---|--------|---------|----------|---------|
| DA-01 | 需求分析 | 理解分析类 | agents/da-01/AGENT.md | SR → 结构化分析 → 标记歧义。不分解、不脑补 |
| DA-02 | 需求分解 | 内容生成类 | agents/da-02/AGENT.md | SR→HLR 或 HLR→LLR (每次一层，不跨层) |
| DA-03 | 模型构建 | 模型处理类 | agents/da-03/AGENT.md | 阶段感知建模: S0-S3 SysML(.sysml), S4-S6 UML(.puml) |
| DA-04 | 模型检查 | 校验分析类 | agents/da-04/AGENT.md | 验证模型语法和一致性 |
| DA-05 | 代码生成 | 内容生成类 | agents/da-05/AGENT.md | UML详细设计模型 → C代码 |
| DA-06 | 代码检查 | 校验分析类 | agents/da-06/AGENT.md | GCC编译 + 标准合规检查 |
| DA-07 | 测试场景分析 | 理解分析类 | agents/da-07/AGENT.md | 从需求识别验证场景 |
| DA-08 | 测试用例生成 | 内容生成类 | agents/da-08/AGENT.md | 场景 → 测试用例 (表格式，DO-178C可追溯) |
| DA-09 | 测试规程生成 | 内容生成类 | agents/da-09/AGENT.md | 用例 → 可执行的分步规程 |
| DA-10 | 测试执行 | 工具执行类 | agents/da-10/AGENT.md | 编译 → 运行 → 写结果。只执行，不分析 |
| DA-11 | 验证分析 | 校验分析类 | agents/da-11/AGENT.md | 分析测试结果，验证DA-10输出质量 |
| DA-12 | 追溯关系维护 | 关系处理类 | agents/da-12/AGENT.md | 从已有制品构建追溯矩阵。不生成新内容 |
| DA-13 | 评审材料整理 | 证据处理类 | agents/da-13/AGENT.md | 收集制品 → 整理评审材料 |
| DA-14 | 适航证据整理 | 证据处理类 | agents/da-14/AGENT.md | 打包适航证据 |

### DA工具分配

DA不在AGENT.md中硬编码工具名，而是声明**工具需求**（能力类别）。具体工具由项目配置指定：

```
DA AGENT.md (工具需求)    项目 config.yaml (工具分配)
─────────────────────    ─────────────────────────
“需要建模工具”      →     model-build: [plantuml, llm_api]
“需要编译器”        →     code-gen:    [gcc, llm_api]
```

全局默认映射在 `projects/{id}/.pla/environment/config.yaml`，项目可在 `projects/{id}/config.yaml` 中覆盖。例如：

```yaml
# projects/sr2/config.yaml — 项目规范禁止UML，改用IDEF0
da_tools:
  model-build:  [idef0, llm_api]
  model-check:  [idef0, llm_api]
```

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
| detailed_design | 详细设计 | 融合 | DA-03, DA-04 |
| code_generation | 代码生成 | 模型驱动 | DA-05, DA-06, DA-12 |
| test_case_gen | 测试用例生成 | 融合 | DA-07, DA-08, DA-09, DA-12 |
| test_execution | 测试执行 | 模型驱动 | DA-10 |
| verification | 验证分析 | 融合 | DA-11, DA-12 |
| review_prep | 评审材料准备 | 融合 | DA-13 |
| evidence_pack | 适航证据打包 | 融合 | DA-14 |

---

## 快速开始

### 前置条件

- Python 3.10+
- GCC (本地编译)
- arm-none-eabi-gcc 13+ (嵌入式交叉编译，可选)

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 克隆仓库
git clone git@github.com:xbhlhs/cyber-ac.git
cd fusion

# 本地编译 + 运行 (快速开发迭代)
make -C projects/sr1

# 双编译器验证 (Host GCC + Cortex-M4 arm-none-eabi-gcc)
make -C projects/sr1 all

# 查看嵌入式汇编代码
make -C projects/sr1 embedded-asm

# 清理构建产物
make -C projects/sr1 clean
```

### 运行PLA编排

PLA Agent作为编排者，通过文件通道与DA Agent通信：

```bash
# PLA发起一次研发活动 (如需求分解)
python -m runtime.orchestrator --activity sr_to_hlr --dal D
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
  "constraints": {"dal_level": "C", "development_path": "fusion"},
  "human_gate_after": true,
  "human_gate_type": "initial_plan"
}
```

**DA → PLA (Execution Result)**：

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

## SR-1 贯穿案例

SR-1是一个机载软件功能模块的完整研发案例，贯穿 SR → HLR → LLR → C代码 → 编译 → 测试 → 证据 的全生命周期路径：

| 属性 | 值 |
|------|-----|
| **功能** | 三设备(EQA/EQB/EQC)输入综合计算 |
| **DAL级别** | D (25个DO-178C目标) |
| **编译器** | GCC (本地) + arm-none-eabi-gcc (Cortex-M4) |
| **语言标准** | C11, 无动态内存分配 |
| **制品** | 1 SR + 9 HLR + 10 LLR + 3 C文件 + 11测试用例 |
| **证据** | 追溯矩阵、代码检查报告、测试结果、验证分析 |

---

## 新增项目

```bash
# 1. 创建项目目录
mkdir -p projects/sr2/{requirements,models,src,tests,evidence}

# 2. 初始化 .pla/ 运行时环境 (从模板复制工程配置)
cp -r examples/environment projects/sr2/.pla/environment

# 3. 编写项目配置
cat > projects/sr2/config.yaml << 'EOF'
project:
  id: "SR-2"
  name: "YOUR_FUNCTION"
  dal_level: "C"
project_path_constraints:
  model_policy: "as_dal"
EOF

# 4. 编写系统需求
# projects/sr2/requirements/sr.md

# 5. 启动PLA编排
python -m runtime.orchestrator --project sr2 --activity sr_to_hlr --dal C
```

---

## 许可证

本项目采用 [Apache License 2.0](LICENSE)。
