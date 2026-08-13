# AGENTS.md — 融合开发体系工程实现

## 关键认知

**PLA和14个DA都是独立的AI Agent，不是Python类、函数或模块。**

- 每个Agent由 `AGENT.md` 定义（系统提示词 + 输入输出契约 + 可用工具 + 约束）
- Agent之间通过 **文件消息通道** 通信（`queue/outbox/` ↔ `queue/inbox/`）
- PLA是五层闭环控制器，DA是领域能力执行器
- DA内部可以调用工程资源工具（GCC, PlantUML, LLM API, Git等）

## 架构

```
PLA Agent (agents/pla/AGENT.md)
  L1 感知 → L2 决策 → L3 执行 → L4 校正 → L5 稳态
    │                    │
    │  写Task Context    │  读Execution Result
    ↓                    ↑
queue/outbox/da-XX/  queue/inbox/da-XX/
    ↓                    ↑
  DA Agent            DA Agent
  (agents/da-XX/AGENT.md)
    │
    ↓ 工具调用
  工程资源 (tools/registry.py)
```

## 三层架构

```
生命周期控制层 (PLA Agent) — 五层闭环，编排14个DA
        ↓ Task Context (JSON文件)
领域能力层 (14 DA Agent) — 按能力类别分工执行
        ↓ 执行请求 (工具调用)
工程资源层 (CLI/API/Human) — 具体工具和服务
```

## 融合开发策略

本体系实现两条互补的研发路径，PLA根据活动类型和DAL级别动态选择：

### 模型驱动路径
从SysML/UML模型出发，通过模型转换和代码生成得到实现。适用于架构设计、详细设计和代码生成等结构化活动。优势是精确性、可追踪性和确定性。

### LLM驱动路径
利用大语言模型的推理能力进行需求分析、文档生成、测试用例生成等知识密集型活动。适用于需求理解、歧义识别、场景分析等需要语义理解的活动。

### 融合策略
PLA对每个研发活动进行路径决策：活动类型→路径静态映射 + DAL自适应动态路由。对于关键活动（如HLR生成），两条路径并行执行后相互校验；对于DAL A/B级别，默认强制走模型优先路径；对于DAL D/E级别，允许LLM优先以提升效率。

## 闭环收敛机制

PLA的L1-L4层形成"调整-确认-收敛"闭环：

1. **L1感知**：持续收集DA执行状态，检测偏差信号（质量缺口、约束冲突、覆盖缺失、执行失败）
2. **L4校正**：分析偏差，生成五种校正策略：
   - 增加DA节点（补充缺失能力）
   - 移除DA节点（消除冗余执行）
   - 重排DA顺序（调整执行先后）
   - 调整参数（修改输入/约束）
   - 调整条件（修改分支/判断逻辑）
3. **L2重编排**：接收校正信号，生成新的Task Plan（DAG版本号递增）
4. 循环执行直到收敛或触发人工闸门

## 三股信息流

| 流 | 方向 | 内容 |
|----|------|------|
| 指令流 ↓ | L2→L3→DA | 任务指令、上下文、约束条件 |
| 证据流 ↑ | DA→L1→L2+L5 | 执行产物、过程数据、日志 |
| 偏差流 ↔ | DA→L1→L4→L2 | 异常信号、校正请求 |

## 14个DA Agent

DA按能力分为五类：

| 类别 | 说明 | 包含DA |
|------|------|--------|
| 理解分析类 | 读入制品，提取结构化信息 | DA-01, DA-07 |
| 内容生成类 | 基于输入生成新制品 | DA-02, DA-05, DA-08, DA-09 |
| 模型处理类 | 构建和检查SysML/UML模型 | DA-03, DA-04 |
| 校验分析类 | 检查制品的正确性和一致性 | DA-06, DA-11 |
| 关系/证据类 | 维护追溯链和证据包 | DA-12, DA-13, DA-14 |

| # | DA名称 | 能力类别 | Agent文件 |
|---|--------|---------|----------|
| DA-01 | 需求分析 | 理解分析类 | agents/da-01/AGENT.md |
| DA-02 | 需求分解 | 内容生成类 | agents/da-02/AGENT.md |
| DA-03 | 模型构建 | 模型处理类 | agents/da-03/AGENT.md |
| DA-04 | 模型检查 | 校验分析类 | agents/da-04/AGENT.md |
| DA-05 | 代码生成 | 内容生成类 | agents/da-05/AGENT.md |
| DA-06 | 代码检查 | 校验分析类 | agents/da-06/AGENT.md |
| DA-07 | 测试场景分析 | 理解分析类 | agents/da-07/AGENT.md |
| DA-08 | 测试用例生成 | 内容生成类 | agents/da-08/AGENT.md |
| DA-09 | 测试规程生成 | 内容生成类 | agents/da-09/AGENT.md |
| DA-10 | 测试执行 | 工具执行类 | agents/da-10/AGENT.md |
| DA-11 | 验证分析 | 校验分析类 | agents/da-11/AGENT.md |
| DA-12 | 追溯关系维护 | 关系处理类 | agents/da-12/AGENT.md |
| DA-13 | 评审材料整理 | 证据处理类 | agents/da-13/AGENT.md |
| DA-14 | 适航证据整理 | 证据处理类 | agents/da-14/AGENT.md |

## DAL自适应策略

PLA根据DAL级别调整开发行为的严格程度：

| DAL | 路径选择 | 验证粒度 | 人工介入 |
|-----|---------|---------|---------|
| A/B | 确定性工具优先 | 全记录，逐项确认 | 逐节点独立评审 |
| C | 确定性为主，LLM受限 | 标准记录，抽查 | 抽查评审 |
| D/E | 允许LLM优先 | 简化，自动确认 | 仅异常触发 |

## 人工闸门

PLA在Task DAG中嵌入5类可控暂停点：

1. **初始计划授权** — DAL A/B必须，DAL C可选
2. **DA路径选择** — LLM路径 + DAL ≥ C 时触发
3. **验证确认** — 测试缺口或偏差超限时触发
4. **变更影响评估** — 跨层影响检测到时触发
5. **证据归档签批** — L5完成证据包时触发

人工闸门不阻塞自动化主线——继续处理其他独立的并行任务。

## 研发活动类型

PLA支持的研发活动及对应的路径映射：

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

## 通信协议

### PLA → DA (Task Context)

PLA的L2决策层确定目标DA和任务参数，L3封装后派发。`task_id`/`task_name`/`task_description` 均流入评审材料和适航证据提取流程。

```json
{
  "task_id": "sr_to_hlr-T02",
  "task_name": "需求分解",
  "da_name": "req-decomp",
  "activity_type": "sr_to_hlr",
  "description": "Decompose SR into candidate HLR",
  "inputs": {"sr": "sr1/requirements/sr.md"},
  "expected_outputs": ["sr1/requirements/hlr.md"],
  "constraints": {"dal_level": "C", "development_path": "fusion"},
  "human_gate_after": true,
  "human_gate_type": "initial_plan"
}
```

字段说明:
- `task_id` — 唯一标识，格式 `{activity_type}-T{序号}`
- `task_name` — 人可读名称（中文），用于评审清单和证据索引
- `da_name` — 目标DA，由PLA L2决策
- `description` — 任务详细描述
- `inputs` — 输入制品路径映射
- `expected_outputs` — 期望输出文件列表
- `constraints` — DAL级别和开发路径约束
- `human_gate_*` — 人工闸门配置

### DA → PLA (Execution Result)
```json
{
  "task_id": "...",
  "status": "completed",
  "artifacts": ["sr1/requirements/hlr.md"],
  "process_data": {"reasoning": "...", "decisions": [...]},
  "requires_human_review": true
}
```

## 工程资源

工程资源分为三类接入方式。DA需要什么类别的工具在其AGENT.md的"工具需求"中声明，具体使用哪个工具由项目配置指定。

| 接入方式 | 可用工具 | 说明 |
|---------|---------|------|
| CLI | GCC, PlantUML, Git, Make 等 | 命令行工具（含提供CLI接口的桌面端工具），可按项目扩展 |
| API | LLM推理, ReqIF导入, docx解析, 基线同步 等 | 服务化资源（LLM + 存量系统集成API） |
| Human | 评审闸门 | PLA调度人工评审节点 |

### 工具分配机制

```
DA AGENT.md (工具需求)    项目 config.yaml (工具分配)
─────────────────────    ─────────────────────────
"需要建模工具"      →     model-build: [plantuml, llm_api]
"需要编译器"        →     code-gen:    [gcc, llm_api]
```

全局默认映射在 `environment/config.yaml` 的 `da_tools` 段。
项目可在 `projects/{id}/config.yaml` 中覆盖任意DA的工具分配。
未覆盖的DA沿用全局默认。

例如：某项目规范禁止UML，要求IDEF0——
```yaml
# projects/sr2/config.yaml
da_tools:
  model-build:  [idef0, llm_api]
  model-check:  [idef0, llm_api]
```
只需在工具注册表中添加 `idef0` 工具定义，无需修改任何DA的AGENT.md。

## 项目初始化

**初始化是人工/驱动Agent的职责，不是PLA/DA的运行时行为。**

使用 `scripts/init_project.py` 从 `examples/` 模板创建项目，按 DAL 裁切约束文件：

```bash
python3 scripts/init_project.py <project_id> <dal_level>

# 示例
python3 scripts/init_project.py sr1 D   # DAL D: 6 目标
python3 scripts/init_project.py sr2 A   # DAL A: 26 目标
```

**裁切规则**（`scripts/init_project.py` → `_filter_do178c()`）：
- 只保留 `applicable_DAL` 包含目标 DAL 的条目
- DAL D (25 obj) vs DAL A (66 obj) — 项目配置不应包含不适用的目标
- `company.yaml` 和 `do331.yaml` 全量保留（公司规范不分 DAL，DO-331 触发条件由代码判断）

**裁切后的效果**（以 `do178c.yaml` 为例）：

| 约束表 | DAL D | DAL A |
|--------|-------|-------|
| hlr_verification | A3-1, A3-2, A3-6 (3) | A3-1~A3-7 (7) |
| llr_verification | — (0) | A4-1, A4-2, A4-5~A4-7 (5) |
| coding_verification | — (0) | A5-1, A5-2, A5-4~A5-6 (5) |
| testing | A6-1, A6-2, A6-5 (3) | A6-1~A6-5 (5) |
| structural_coverage | — (0) | A7-5~A7-8 (4) |

**DA 模型分配**：
- PLA 使用 `~/.hermes/config.yaml` 中的 `delegation.model`
- DA 使用 `projects/{id}/.pla/environment/config.yaml` 中的 `da_models` 段
- 解析顺序: `da_models.overrides[da_name]` → `da_models.default`
- 详细配置参考 `~/workspace/ref/Agents' Model Default Configuration.md`

## SR-1 贯穿案例

SR-1: 三设备(EQA/EQB/EQC)输入综合计算
完整路径: SR → HLR → LLR → 模型 → C代码 → 编译 → 测试 → 证据

## Agent 操作约束 (fusion 工作区专用)

> **角色消歧（重要）**：本文件由「驱动 Agent」（面向用户的 CLI Agent，我）视角编写。当进程被 spawn 时，其角色由 spawn prompt 决定：
> - prompt 含「你作为PLA」→ 该进程**就是 PLA**，直接执行 L1~L5 闭环，**不得**再 spawn 另一个 PLA
> - prompt 含「你作为DA-XX」→ 该进程**就是 DA-XX**，只执行本任务
> - 无角色前缀的进程才是驱动 Agent，才负责 spawn PLA
> 读到本节内容 ≠ 你是驱动 Agent。你的角色由 spawn 指令决定，不由本文件决定。

### 驱动 Agent (我) 的约束

1. 只给 PLA 传递输入（评审结论、SR、项目规范），不指导 PLA 如何执行（L2 是 PLA 的职责）
2. 不做本该 PLA/DA 做的事——评审打包是 DA-13 的活，HLR 修正是 DA-02 的活
3. 不碰 `~/.hermes/config.yaml`
4. PLA 用 terminal spawn（非 delegate_task），DA 由 PLA spawn
4a. **Spawn prompt 最小化原则**: 驱动→PLA 和 PLA→DA 的 spawn prompt 应极简，只指向指令文档。指令文档（如 `instructions/sr_to_hlr.md`）包含完整上下文、上游结论、步骤指引。L2 生成 Task DAG 骨架，L3 在 dispatch 时动态生成每个 task 的执行文档（写入 `queue/outbox/{da}/task_{id}.json`），融入上游 DA 的产出结论，而非 spawn prompt 中预写死所有细节。
5. 人工闸门 = 用户裁决，只中继不替代
6. 评审-响应-再审闭环：评审结论→PLA L2 决策响应→再审→循环至关闭。过程证据独立于结果制品

### 项目交付规范

1. 评审材料为 ZIP 包（独立文件，非合并 md），含 SR 源/输出制品/RTM/过程证据/澄清文件 + 00_index 清单
2. HLR 仅含需求条目 + 门控总结 + 约束汇总（§1-3），追溯表/AMB 消解/DO-178C 声明/设计理由不属需求文档
3. 澄清过程每次产生原始记录 + 结构化文件两份，HLR 引用不内联
4. 人工闸门结论只指导输出完善性/一致性，不指导研发过程行为
5. 产出物 L5 如实记录，中间过程记录概要（不过于摘要）

### 验证管理

- 每轮全量验证 → `validation-runs/run-NNN/bugs/` 独立管理
- 项目初始化 = `scripts/init_project.py`（合法 YAML + 按 DAL 裁切）
- DA 模型参考 `~/workspace/ref/Agents' Model Default Configuration.md`
- 基线冻结需人工授权
