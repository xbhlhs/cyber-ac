# 融合开发体系 — 工程实现

> 本工作区实现融合开发体系工程原型——一个面向机载软件的多Agent协同研发环境。
>
> **核心架构**: PLA (Process Lifecycle Agent) — 五层闭环控制器 + 14 DA (Domain Agent) — 领域能力执行器
>
> **关键设计**: PLA和每个DA都是独立的AI Agent，通过文件消息通道通信，不是Python类或函数调用。
>
> 验证对象：机载软件研发过程管理 | 实现语言：C (机载软件本体)
> 编译器：GCC (host) + arm-none-eabi-gcc (Cortex-M4) | 标准：DO-178C

## 概述

融合开发体系将模型驱动开发（SysML/UML→代码生成）和LLM驱动开发（需求分析→文档生成）两条路径有机结合。PLA根据活动类型和DAL级别动态选择路径，通过五层闭环控制保证过程质量和制品一致性。14个DA按能力分类（理解分析、内容生成、模型处理、校验分析、关系/证据处理），各司其职，通过文件消息通道与PLA协同。

### 为什么是文件消息通道

- **解耦**: PLA和DA可以独立启动、独立运行、独立调试
- **可追溯**: 每条消息都是持久化的JSON文件，天然形成审计日志
- **符合适航**: DO-178C要求过程可审计——文件通道天然满足
- **离线协作**: 人类可以在闸门处插入决策，修改队列文件后DA继续

## 目录结构

```
fusion/
├── agents/                     # Agent定义 (AGENT.md提示词, 非Python类)
│   ├── pla/AGENT.md            #   PLA — 五层闭环控制器
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
├── runtime/                    # 通信基础设施
│   ├── protocol.py             #   Task Context / Execution Result 协议
│   ├── channel.py              #   文件消息通道 (queue/outbox ↔ queue/inbox)
│   ├── orchestrator.py         #   PLA-DA纯通信编排器
│   ├── task_plan.py            #   Task Plan / TaskItem / CheckItem 数据结构
│   └── result_validator.py     #   DA结果格式验证器
├── tools/                      # 工程资源工具
│   ├── registry.py             #   工具注册表 + DA工具分配
│   ├── gcc.py                  #   GCC 编译器包装器
│   ├── sysml.py                #   PlantUML 渲染包装器
│   └── git.py                  #   Git 版本管理包装器
├── environment/
│   ├── config.yaml             #   项目工程环境配置 (DA Pool, 资源, 闸门, 通道)
│   └── constraints/            #   标准规范约束
│       ├── do178c.yaml         #   DO-178C Annex A 目标表 + 各层加载映射
│       ├── do331.yaml          #   DO-331 MBE补充
│       └── company.yaml        #   公司级规范 (模型策略, 编码标准)
├── queue/                      # 运行时消息队列
│   ├── outbox/                 #   PLA → DA 任务
│   └── inbox/                  #   DA → PLA 结果
├── projects/                   # 项目目录 (每个SR一个子目录)
│   └── sr1/                   #   SR-1 贯穿案例
│       ├── config.yaml        #   项目特定约束 (DAL D, 适用目标)
│       ├── requirements/      #   SR/HLR/LLR 需求文档
│       ├── models/            #   SysML 模型
│       ├── src/               #   C 源代码 (main.c, sr1.c, sr1.h)
│       ├── tests/             #   测试用例和规程
│       └── evidence/          #   过程证据和追溯矩阵
├── evidence/                   # 全局模板
├── scripts/                    # 运行脚本 (run_pla.py, run_da.py)
├── skills/                     # PLA技能定义
├── Makefile                    # 构建系统 (双编译器)
└── AGENTS.md                   # 工作区上下文规则 (详见)
```

## 架构层次

```
生命周期控制层 (PLA Agent) — 五层闭环编排
     L1感知 → L2决策 → L3执行 → L4校正 → L5稳态
        ↓ Task Context (JSON文件)
领域能力层 (14个DA Agent) — 按能力类别分工
    理解分析 → 内容生成 → 模型处理 → 校验分析 → 关系证据
        ↓ 执行请求 (工具调用)
工程资源层 — 具体工具和服务
    CLI(GCC/PlantUML/Git/Make) | API(LLM) | Human(评审闸门)
```

## PLA五层闭环

| 层 | 名称 | 职责 |
|----|------|------|
| L1 | 感知层 | 读取SR和项目配置，持续收集DA执行状态，检测偏差信号 |
| L2 | 决策层 | 动态生成Task DAG，选择开发路径（模型/LLM/融合），注入DAL约束 |
| L3 | 执行层 | 封装Task Context→写队列→DA读取执行→PLA读结果，不判断正确性 |
| L4 | 校正层 | 分析L1偏差信号，生成五种校正策略，反馈给L2重编排 |
| L5 | 稳态层 | 持续收集过程数据和执行记录，维护证据覆盖矩阵，归档适航证据 |

## DAL自适应

PLA根据DAL级别（A/B/C/D/E）自动调整开发行为：

| DAL | 路径选择 | 模型要求 | 人工介入 | 典型项目 |
|-----|---------|---------|---------|---------|
| A | 确定性工具优先 | 强制 | 逐节点独立评审 | 飞控系统 |
| B | 确定性工具优先 | 强制 | 逐节点独立评审 | 导航系统 |
| C | 确定性为主，LLM受限 | 推荐 | 抽查评审 | 通信系统 |
| D | 允许LLM优先 | 可选 | 异常触发 | 显示系统 |
| E | LLM优先 | 可选 | 异常触发 | 非关键功能 |

## 运行方式

每个Agent是独立的AI进程。PLA Agent作为编排者启动，通过文件通道与DA Agent通信：

```bash
# PLA Agent 发起一次研发活动 (如需求分解)
python -m runtime.orchestrator --activity sr_to_hlr --dal D

# 或手动: PLA写Task Context → DA Agent读取执行 → PLA读结果
# Task Context: queue/outbox/{da-name}/task_{task_id}.json
# Result:       queue/inbox/{da-name}/result_{task_id}.json
```

## 快速开始

```bash
# 编译运行 SR-1 C代码 (独立于Agent体系)
make sr1

# 双编译器验证 (Host + Cortex-M4)
make sr1-all

# 查看汇编代码
make sr1-embedded-asm
```

## SR-1 贯穿案例

SR-1是一个机载软件功能模块的完整研发案例，贯穿SR→HLR→LLR→C代码→编译→测试→证据的全生命周期路径：

- **功能**: 三设备(EQA/EQB/EQC)输入综合计算
- **DAL级别**: D (25个DO-178C目标)
- **编译器**: GCC (本地开发) + arm-none-eabi-gcc (嵌入式目标验证)
- **标准**: C11, 无动态内存分配
- **制品**: 1 SR + 9 HLR + 10 LLR + 3 C文件 + 11测试用例

## 新增项目

```bash
# 1. 创建项目目录
mkdir -p projects/sr2/{requirements,models,src,tests,evidence}

# 2. 编写项目配置
cat > projects/sr2/config.yaml << EOF
project:
  id: "SR-2"
  name: "YOUR_FUNCTION"
  dal_level: "C"
project_path_constraints:
  model_policy: "as_dal"
  ...
EOF

# 3. 编写系统需求
# projects/sr2/requirements/sr.md

# 4. 启动PLA编排
python -m runtime.orchestrator --project sr2 --activity sr_to_hlr --dal C
```
