# 追溯矩阵模板

> 项目：{project_id}
> 更新日期：{updated_at}

## 追溯关系

| 上游 | 下游 | 关系类型 | 说明 |
|------|------|---------|------|
| SR-1 | HLR-1.1 | refines | SR 细化 |
| SR-1 | HLR-1.2 | refines | SR 细化 |
| HLR-1.1 | LLR-1.1.1 | refines | HLR 细化 |
| LLR-1.1.1 | sr1.c:func_x() | implements | 代码实现 |
| LLR-1.1.1 | test_case_01 | verifies | 测试验证 |
| SR-1 | test_case_01 | verifies | 需求验证 |

## 追溯完整性检查

| 需求 ID | 有 HLR | 有 LLR | 有模型 | 有代码 | 有测试 | 状态 |
|---------|--------|--------|--------|--------|--------|------|
| SR-1 | — | — | — | — | — | — |
