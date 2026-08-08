# 配置模板示例

本目录包含融合开发体系的全量配置模板——展示了所有可配置项、每个字段的语义说明和使用场景。

**所有文件已完整注释 (YAML `#` 注释)。直接复制到对应位置，取消注释所需项目即可使用。**

## 目录

```
examples/
├── README.md                           # 本文件
├── environment/                        # 工程环境配置模板
│   ├── config.yaml                     #   基础设施配置 (DA Pool / 资源池 / 闸门 / 通道 / 收敛控制)
│   └── constraints/                    #   标准规范约束模板
│       ├── do178c.yaml                 #     DO-178C Annex A 完整目标表 + Section 11 数据项
│       ├── do331.yaml                  #     DO-331 基于模型开发补充 (含 Annex MB.A-1~7)
│       └── company.yaml                #     公司级规范 (模型策略 / 编码标准 / 评审 / 测试 / 编译器策略)
├── queue/                              # 消息队列结构模板
│   ├── outbox/                         #   PLA → DA 任务输出目录
│   └── inbox/                          #   DA → PLA 结果输入目录
├── evidence/                           # 证据模板
│   ├── checklist_template.md           #   检查清单模板
│   ├── task_plan_template.md           #   任务计划模板
│   └── trace_matrix_template.md        #   追溯矩阵模板
└── projects/
    └── config.yaml                     #   项目级配置模板 (DAL / 路径约束 / 目标 / 工具 / 资源 / 里程碑)
```

## 使用方式

### 新增项目

```bash
# 1. 从模板初始化 .pla/ 运行时环境
cp -r examples/environment projects/sr2/.pla/environment

# 2. 从模板复制项目配置
cp examples/projects/config.yaml projects/sr2/config.yaml

# 3. 编辑 projects/sr2/config.yaml
#    - 修改 project.id / name / dal_level
#    - 根据需要取消注释 do178c_applicable 目标
#    - 配置 da_tools (如需覆盖全局默认)

# 4. 创建项目目录结构
mkdir -p projects/sr2/{requirements,models,src,tests,evidence}
```

### 修改工程环境

```bash
# 工程环境配置在各项目的 .pla/ 目录下。
# 每个项目有独立的 .pla/environment/，从 examples/ 初始化后独立维护。

# 修改 SR-1 的环境配置:
# 编辑 projects/sr1/.pla/environment/config.yaml

# 新项目初始化:
cp -r examples/environment projects/sr2/.pla/environment
```

### 修改标准约束

```bash
# 约束模板展示完整的目标表。按需调整后复制到项目 .pla/ 目录:
cp examples/environment/constraints/do178c.yaml projects/sr2/.pla/environment/constraints/do178c.yaml
cp examples/environment/constraints/company.yaml projects/sr2/.pla/environment/constraints/company.yaml
```

## 配置层次与优先级

配置分为三层，下层可覆盖上层:

```
工程环境级 (projects/{id}/.pla/environment/config.yaml)
  └── 定义: DA Pool / 全局工具映射 / 闸门定义 / 通道配置
       ↓
公司规范级 (projects/{id}/.pla/environment/constraints/company.yaml)
  └── 定义: 模型策略 / 编码标准 / 评审策略 / 工具鉴定
       ↓ 项目可覆盖
项目级 (projects/{id}/config.yaml)
  └── 定义: DAL级别 / 路径约束 / 适用目标 / DA工具覆盖 / 工程资源
```

**优先级: 项目约束 > 公司约束 > DAL默认**

## 模板与活跃配置的对应关系

| 模板文件 | SR-1活跃配置位置 | 说明 |
|---------|-----------------|------|
| `examples/environment/config.yaml` | `projects/sr1/.pla/environment/config.yaml` | 工程环境基础设施 |
| `examples/environment/constraints/do178c.yaml` | `projects/sr1/.pla/environment/constraints/do178c.yaml` | DO-178C目标表 |
| `examples/environment/constraints/do331.yaml` | `projects/sr1/.pla/environment/constraints/do331.yaml` | 模型开发补充 |
| `examples/environment/constraints/company.yaml` | `projects/sr1/.pla/environment/constraints/company.yaml` | 公司级规范 |
| `examples/projects/config.yaml` | `projects/sr1/config.yaml` | 项目配置 |
| `examples/evidence/*.md` | `projects/sr1/evidence/` | 证据模板 (初始化时复制使用) |
