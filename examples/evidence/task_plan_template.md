# 任务计划模板

> 项目：{project_id}
> 创建时间：{created_at}
> 状态：{status}

## 任务列表

| ID | 阶段 | 任务名称 | 负责 Agent | 依赖 | 输入 | 输出 | 状态 |
|----|------|---------|-----------|------|------|------|------|
| T01 | 需求 | SR 输入与任务初始化 | PLA | — | SR | TaskPlan, Checklist | — |
| T02 | 需求 | SR→HLR | Requirements | T01 | SR | HLR | — |
| T03 | 需求 | HLR→LLR | Requirements | T02 | HLR | LLR | — |
| T04 | 设计 | SysML 模型构建 | Model | T03 | LLR | BDD, IBD, ACT, STM | — |
| T05 | 实现 | C 代码实现 | Code | T04 | LLR | sr1.c, sr1.h | — |
| T06 | 实现 | GCC 编译 | Code | T05 | sr1.c | sr1 (binary) | — |
| T07 | 验证 | 测试用例与执行 | Test | T06 | SR, LLR | test_sr1.c, 测试结果 | — |
| T08 | 验证 | 结果检查与人工评审 | PLA | T07 | 全部制品 | 评审记录 | — |
| T09 | 证据 | 证据归档 | PLA | T08 | 全部制品+记录 | 追溯矩阵, 证据索引 | — |
