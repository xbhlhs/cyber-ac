# SR→HLR→LLR→Code 追溯矩阵（Trace Matrix）

> 项目：SR-1（FUN1数据对比输出）｜ DAL：D
> 追溯级别：SR → HLR → LLR → Code（三层；HLR→LLR 层于 hlr_to_llr-T02 扩展，LLR→Code 层于 code_generation-T03 扩展）
> 维护者：DA-12 (trace-maint) ｜ 任务：sr_to_hlr-T03、hlr_to_llr-T02、code_generation-T03 ｜ 更新日期：2026-08-08
> 适用目标：SR→HLR 层——A3-1（HLR 符合系统需求）、A3-2（HLR 准确且一致）、A3-6（HLR 可追溯至系统需求）；HLR→LLR 层——**无适用目标**（DAL D：项目配置 `do178c_applicable.llr_verification = []`，LLR 验证目标 A4-1~A4-8（DO-178C §6.4 表 A-4）仅适用于 DAL A/B/C，本层不声明任何 A4-* 符合性）；LLR→Code 层——**无适用目标**（DAL D：项目配置 `do178c_applicable.code_verification = []`，编码验证目标 A5-1/A5-2/A5-4（DO-178C §6.4.2 表 A-5）仅适用于 DAL A/B/C，本层不声明任何 A5-* 符合性）
> 追溯依据（权威来源，未创建任何新链接）：
> - `projects/sr1/requirements/sr.md`（SR 源）
> - `projects/sr1/requirements/hlr.md`（DA-02 输出，10 条目；各条目 `Source` 字段为权威映射）
> - `projects/sr1/requirements/llr.md`（DA-02 输出 hlr_to_llr-T01 重新生成，11 条目；各条目 `Source` 字段为权威映射）
> - `projects/sr1/evidence/req_analysis.md`（DA-01 分析：AR-01~AR-10 原子规则、§4 可追溯性映射）
> - `projects/sr1/src/sr1.c` + `projects/sr1/src/sr1.h`（DA-05 code_generation-T01 输出；代码内 LLR→Code 追溯注释为权威映射）
> - `projects/sr1/evidence/code_check.md`（DA-06 code_generation-T02 检查报告；§3 LLR→Code 追溯覆盖表 11/11，交叉核对来源）

> **范围声明（DA-12 契约）**：本矩阵仅维护追溯关系，不生成/修改任何制品内容（未触碰 `sr.md`、`req_analysis.md`、`hlr.md`、`llr.md`、`sr1.c`、`sr1.h`、`code_check.md`）。所有链接均取自上述制品的既有声明，未发明任何制品中不存在的追溯关系。

---

## 1. 前向追溯表（SR 条款 → HLR 条目）

映射依据：各 HLR 条目 `Source` 字段 + `hlr.md`「需求分解汇总表」+ `req_analysis.md` §4 可追溯性映射（DA-02 已采纳该建议条目编号）。

| SR 条款 | SR 条款内容摘要 | 覆盖 HLR | 覆盖原子规则 | 追溯依据 |
|---------|---------------|----------|--------------|---------|
| SR-1 §1a | LA 输出条件：该周期 LA 数据有效 | HLR-LA-001 | AR-01 | HLR-LA-001 Source: SR-1 §1a |
| SR-1 §1b | LA 输出条件：LA 与 EQC.LA 对比一致 | HLR-LA-002 | AR-02 | HLR-LA-002 Source: SR-1 §1b |
| SR-1 §1c | 否则不输出 LA（抑制） | HLR-LA-003 | AR-03 | HLR-LA-003 Source: SR-1 §1c |
| SR-1 §2a | LB 输出条件：该周期 LB 数据有效 | HLR-LB-001 | AR-04 | HLR-LB-001 Source: SR-1 §2a |
| SR-1 §2b | LB 输出条件：LB 与 EQC.LB 对比一致 | HLR-LB-002 | AR-05 | HLR-LB-002 Source: SR-1 §2b |
| SR-1 §2c | 否则不输出 LB（抑制） | HLR-LB-003 | AR-06 | HLR-LB-003 Source: SR-1 §2c |
| SR-1 §3 | LC 输出条件：生成的 LC 与 EQB.LC 对比一致 | HLR-LC-001 | AR-07 | HLR-LC-001 Source: SR-1 §3 |
| SR-1 §3 | 对比不一致则不输出 LC（抑制） | HLR-LC-002 | AR-09 | HLR-LC-002 Source: SR-1 §3 |
| SR-1 §3（关键观察） | LC 无有效性概念（人工评审确认的设计意图） | HLR-LC-003 | AR-08 | HLR-LC-003 Source: SR-1 §3（SR-1 关键观察） |
| SR-1 §1/§2/§3（全局） | 每周期条件输出行为模式（满足→输出一次；不满足→抑制） | HLR-COM-001 | AR-10 | HLR-COM-001 Source: SR-1 §1/§2/§3（全局） |
| SR-1 需求分析表 | 功能主体 EQA、外部实体 EQB/EQC、数据对象 LA/LB/LC | 贯穿各条目（Source 与关联关系） | — | hlr.md 汇总表第 11 行 |
| SR-1 数据关联关系表 | LA↔EQC.LA、LB↔EQC.LB、LC↔EQB.LC | HLR-LA-002 / HLR-LB-002 / HLR-LC-001 | AR-02/AR-05/AR-07 | hlr.md 汇总表第 12 行；三条目 Source 均含数据关联关系表 |
| SR-1 规则提取表（R-01~R-05） | 输出依赖关系与允许/禁止输出规则 | 各条目（经 AR-01~AR-10 落地） | AR-01~AR-10 | req_analysis.md §2 原子化（R-01~R-05 → AR-01~AR-10） |

**前向覆盖统计**：SR 条款级 9 项 + 全局行为模式 1 项 + 表格级 3 项 = **13 项 SR 侧条目 → 10 条 HLR 条目**，全部有覆盖，覆盖率 **100%**。

---

## 2. 后向追溯表（HLR 条目 → SR 条款）

映射依据：各 HLR 条目 `Source` 字段（权威映射，逐条核对）。

| HLR 条目 | HLR 名称 | Source（SR 条款） | 覆盖原子规则 | 关联未决项 |
|----------|---------|-------------------|--------------|-----------|
| HLR-LA-001 | LA 周期输出与有效性检查 | SR-1 §1a | AR-01 | AMB-01、AMB-02、AMB-06、AMB-07 |
| HLR-LA-002 | LA 一致性比较 | SR-1 §1b（数据关联关系表：LA ↔ EQC.LA） | AR-02 | AMB-01、AMB-03、AMB-06、AMB-07 |
| HLR-LA-003 | LA 输出抑制 | SR-1 §1c | AR-03 | AMB-02、AMB-03、AMB-05 |
| HLR-LB-001 | LB 周期输出与有效性检查 | SR-1 §2a | AR-04 | AMB-01、AMB-02、AMB-06、AMB-07 |
| HLR-LB-002 | LB 一致性比较 | SR-1 §2b（数据关联关系表：LB ↔ EQC.LB） | AR-05 | AMB-01、AMB-03、AMB-06、AMB-07 |
| HLR-LB-003 | LB 输出抑制 | SR-1 §2c | AR-06 | AMB-02、AMB-03、AMB-05 |
| HLR-LC-001 | LC 一致性比较与周期输出 | SR-1 §3（数据关联关系表：LC ↔ EQB.LC） | AR-07 | AMB-01、AMB-03、AMB-06 |
| HLR-LC-002 | LC 输出抑制 | SR-1 §3 | AR-09 | AMB-03、AMB-05 |
| HLR-LC-003 | LC 无有效性检查（不对称性显式声明） | SR-1 §3（SR-1 关键观察） | AR-08 | AMB-04 |
| HLR-COM-001 | 周期条件输出通用行为 | SR-1 §1/§2/§3（全局） | AR-10 | AMB-01、AMB-05 |

**后向覆盖统计**：**10/10 条 HLR 条目**均有唯一 SR 条款来源，覆盖率 **100%**，孤儿条目 **0**。

---

## 2-b. 前向追溯表（HLR 条目 → LLR 条目）

映射依据：各 LLR 条目 `Source` 字段（权威映射，逐条核对）+ `llr.md`「HLR→LLR 追溯矩阵」（DA-02 hlr_to_llr-T01 输出）。HLR-LC-003 除直接来源 LLR-COM-003 外，还作为设计约束约束 LLR-LC-001/LLR-LC-002（`Source` 注明「并受 HLR-LC-003 约束」）。

| HLR 条目 | HLR 名称 | 覆盖 LLR | 追溯依据 |
|----------|---------|----------|---------|
| HLR-LA-001 | LA 周期输出与有效性检查 | LLR-LA-001 | LLR-LA-001 Source: HLR-LA-001 |
| HLR-LA-002 | LA 一致性比较 | LLR-LA-002 | LLR-LA-002 Source: HLR-LA-002 |
| HLR-LA-003 | LA 输出抑制 | LLR-LA-003 | LLR-LA-003 Source: HLR-LA-003 |
| HLR-LB-001 | LB 周期输出与有效性检查 | LLR-LB-001 | LLR-LB-001 Source: HLR-LB-001 |
| HLR-LB-002 | LB 一致性比较 | LLR-LB-002 | LLR-LB-002 Source: HLR-LB-002 |
| HLR-LB-003 | LB 输出抑制 | LLR-LB-003 | LLR-LB-003 Source: HLR-LB-003 |
| HLR-LC-001 | LC 一致性比较与周期输出 | LLR-LC-001 | LLR-LC-001 Source: HLR-LC-001（并受 HLR-LC-003 约束） |
| HLR-LC-002 | LC 输出抑制 | LLR-LC-002 | LLR-LC-002 Source: HLR-LC-002（并受 HLR-LC-003 约束） |
| HLR-LC-003 | LC 无有效性检查（不对称性显式声明） | LLR-LC-001、LLR-LC-002、LLR-COM-003 | LLR-LC-001/002 Source 约束 + LLR-COM-003 Source: HLR-LC-003 |
| HLR-COM-001 | 周期条件输出通用行为 | LLR-COM-001、LLR-COM-002 | LLR-COM-001/002 Source: HLR-COM-001 |

**前向覆盖统计**：**10/10 条 HLR 条目**均有 ≥1 条 LLR 覆盖（唯一 HLR 来源映射 7 条 + 一对多映射 3 条：HLR-LC-003→3、HLR-COM-001→2），覆盖率 **100%**。

---

## 2-c. 后向追溯表（LLR 条目 → HLR 条目）

映射依据：各 LLR 条目 `Source` 字段（权威映射，逐条核对）。LLR-LC-001/002 的主来源为其对应 HLR-LC 条目，HLR-LC-003 作为约束来源一并记录。

| LLR 条目 | LLR 名称 | Source（HLR 条目） |
|----------|---------|-------------------|
| LLR-LA-001 | LA 每周期有效性评估 | HLR-LA-001 |
| LLR-LA-002 | LA 一致性比较（零动态内存） | HLR-LA-002 |
| LLR-LA-003 | LA 输出门控（有效性 且 一致性） | HLR-LA-003 |
| LLR-LB-001 | LB 每周期有效性评估 | HLR-LB-001 |
| LLR-LB-002 | LB 一致性比较（零动态内存） | HLR-LB-002 |
| LLR-LB-003 | LB 输出门控（有效性 且 一致性） | HLR-LB-003 |
| LLR-LC-001 | LC 一致性比较（无有效性检查） | HLR-LC-001（并受 HLR-LC-003 约束） |
| LLR-LC-002 | LC 输出门控（仅一致性判据） | HLR-LC-002（并受 HLR-LC-003 约束） |
| LLR-COM-001 | 固定周期处理调度 | HLR-COM-001 |
| LLR-COM-002 | 三通道独立评估 | HLR-COM-001 |
| LLR-COM-003 | LC 不对称性保持（设计约束） | HLR-LC-003 |

**后向覆盖统计**：**11/11 条 LLR 条目**均有 HLR 来源（`Source` 字段非空），覆盖率 **100%**，孤儿条目 **0**。

---

## 2-d. 前向追溯表（LLR 条目 → Code 元素）

映射依据：代码内 LLR→Code 追溯注释（`sr1.h` 头文件「LLR→Code 追溯矩阵」块 sr1.h:8-19 + `sr1.c` 文件头「LLR→Code 追溯」块 sr1.c:7-18 + 各函数/结构逐条注释）与 `code_check.md` §3 追溯覆盖表（DA-06 code_generation-T02 逐条核对，11/11 covered）交叉核对。两来源对全部 11 条 LLR 的映射**完全一致**，无分歧项，无需标记「待确认」。行范围按当前代码基线（DA-05 code_generation-T01 再生成版）确定，旧编号（LLR-1.x）不携带。

| LLR 条目 | LLR 名称 | 代码落实点（函数/结构/常量） | 文件:行范围 | 追溯依据（代码注释 / code_check.md） |
|----------|---------|------------------------------|------------|--------------------------------------|
| LLR-LA-001 | LA 每周期有效性评估 | FUN1_IsLaDataValid()；EQA_Data_t.la_valid（周期有效性标志） | sr1.c:89-102；sr1.h:66-72（la_valid 字段 sr1.h:70） | sr1.h:9 追溯块；sr1.c:9/78 注释；code_check.md §3 |
| LLR-LA-002 | LA 一致性比较（零动态内存） | FUN1_CompareLaMatch()；EQC_Data_t.la（EQC.LA 参照值） | sr1.c:139-142；sr1.h:88-91（la 字段 sr1.h:89） | sr1.h:10；sr1.c:10/132；code_check.md §3 |
| LLR-LA-003 | LA 输出门控（有效性 且 一致性） | FUN1_LaOutputAllowed()；EQA_Output_t.la_out_*（输出值+有效标志） | sr1.c:184-187；sr1.h:115-122（la_out_* 字段 sr1.h:116-117） | sr1.h:11；sr1.c:11/176；code_check.md §3 |
| LLR-LB-001 | LB 每周期有效性评估 | FUN1_IsLbDataValid()；EQA_Data_t.lb_valid（周期有效性标志） | sr1.c:112-125；sr1.h:66-72（lb_valid 字段 sr1.h:71） | sr1.h:12；sr1.c:12/105；code_check.md §3 |
| LLR-LB-002 | LB 一致性比较（零动态内存） | FUN1_CompareLbMatch()；EQC_Data_t.lb（EQC.LB 参照值） | sr1.c:151-154；sr1.h:88-91（lb 字段 sr1.h:90） | sr1.h:13；sr1.c:13/145；code_check.md §3 |
| LLR-LB-003 | LB 输出门控（有效性 且 一致性） | FUN1_LbOutputAllowed()；EQA_Output_t.lb_out_* | sr1.c:198-201；sr1.h:115-122（lb_out_* 字段 sr1.h:118-119） | sr1.h:14；sr1.c:14/190；code_check.md §3 |
| LLR-LC-001 | LC 一致性比较（无有效性检查） | FUN1_CompareLcMatch()；EQB_Data_t.lc（EQB.LC 参照值） | sr1.c:166-169；sr1.h:79-81（lc 字段 sr1.h:80） | sr1.h:15；sr1.c:15/157；code_check.md §3 |
| LLR-LC-002 | LC 输出门控（仅一致性判据） | FUN1_LcOutputAllowed()；EQA_Output_t.lc_out_* | sr1.c:212-215；sr1.h:115-122（lc_out_* 字段 sr1.h:120-121） | sr1.h:16；sr1.c:16/204；code_check.md §3 |
| LLR-COM-001 | 固定周期处理调度 | PROCESS_CYCLE_MS 编译期常量；FUN1_ProcessEqaValidOutput()（周期处理主入口） | sr1.h:35；sr1.c:275-354 | sr1.h:17/32-35；sr1.c:8/256；code_check.md §3 |
| LLR-COM-002 | 三通道独立评估 | FUN1_ProcessEqaValidOutput()（三通道独立判定、分别输出/抑制）；EQA_Cache_t（远端数据缓存） | sr1.c:275-354；sr1.h:100-105 | sr1.h:18；sr1.c:17/256；code_check.md §3 |
| LLR-COM-003 | LC 不对称性保持（设计约束） | LC 路径无有效性分支：FUN1_CompareLcMatch() / FUN1_LcOutputAllowed() / FUN1_ProcessEqaValidOutput() Step7-8（无 lc_valid 标志、无有效性评估） | sr1.c:166-169、212-215、333-349；sr1.h:21-23 | sr1.h:19/21-23；sr1.c:18/24/334-336；code_check.md §3 |

**前向覆盖统计**：**11/11 条 LLR 条目**均有 ≥1 个代码元素落实（函数/结构体/常量），覆盖率 **100%**；代码追溯注释与 code_check.md §3（DA-06 逐条核对）完全一致，无「待确认」链接。

---

## 2-e. 后向追溯表（Code 元素 → LLR 条目）

映射依据：代码内逐函数/逐结构/逐常量的 LLR 追溯注释（`sr1.c` 各函数注释头 + `sr1.h` 各结构/常量注释，每个代码元素均显式标注其落实的 LLR 条目），与 `code_check.md` §3 表（DA-06）一致。统计口径：函数 14 个 + 结构体/常量 8 个 = **22 个代码元素**。

| Code 元素（函数/结构体/常量） | 文件:行范围 | 对应 LLR 条目 | 追溯依据（代码注释位置） |
|------------------------------|------------|--------------|------------------------|
| PROCESS_CYCLE_MS（周期常量） | sr1.h:35 | LLR-COM-001 | sr1.h:32-35 |
| Fun1_RangeConfig_t（范围配置结构） | sr1.h:42-47 | LLR-LA-001、LLR-LB-001 | sr1.h:37-41 |
| FUN1_DEFAULT_RANGE（默认范围常量） | sr1.h:50-55 | LLR-LA-001、LLR-LB-001 | sr1.h:49 |
| EQA_Data_t（本周期待输出数据） | sr1.h:66-72 | LLR-LA-001（la_valid）、LLR-LB-001（lb_valid） | sr1.h:59-65 |
| EQB_Data_t（EQB 提供数据） | sr1.h:79-81 | LLR-LC-001（lc） | sr1.h:74-78 |
| EQC_Data_t（EQC 提供数据） | sr1.h:88-91 | LLR-LA-002（la）、LLR-LB-002（lb） | sr1.h:83-87 |
| EQA_Cache_t（EQA 内部缓存） | sr1.h:100-105 | LLR-COM-002、LLR-LC-001（eqb）、LLR-LA-002/LLR-LB-002（eqc） | sr1.h:93-99 |
| EQA_Output_t（输出结构） | sr1.h:115-122 | LLR-LA-003（la_out_*）、LLR-LB-003（lb_out_*）、LLR-LC-002（lc_out_*） | sr1.h:107-114 |
| FUN1_SetRangeDefault | sr1.c:38-43 | LLR-LA-001、LLR-LB-001 | sr1.c:34 |
| FUN1_SetRangeLa | sr1.c:51-57 | LLR-LA-001 | sr1.c:46 |
| FUN1_SetRangeLb | sr1.c:65-71 | LLR-LB-001 | sr1.c:60 |
| FUN1_IsLaDataValid | sr1.c:89-102 | LLR-LA-001 | sr1.c:78 |
| FUN1_IsLbDataValid | sr1.c:112-125 | LLR-LB-001 | sr1.c:105 |
| FUN1_CompareLaMatch | sr1.c:139-142 | LLR-LA-002 | sr1.c:132 |
| FUN1_CompareLbMatch | sr1.c:151-154 | LLR-LB-002 | sr1.c:145 |
| FUN1_CompareLcMatch | sr1.c:166-169 | LLR-LC-001（并体现 LLR-COM-003 无有效性分支） | sr1.c:157、163-164 |
| FUN1_LaOutputAllowed | sr1.c:184-187 | LLR-LA-003 | sr1.c:176 |
| FUN1_LbOutputAllowed | sr1.c:198-201 | LLR-LB-003 | sr1.c:190 |
| FUN1_LcOutputAllowed | sr1.c:212-215 | LLR-LC-002（并体现 LLR-COM-003 无有效性条件） | sr1.c:204、208-210 |
| FUN1_StoreEqbData | sr1.c:228-234 | LLR-LC-001 | sr1.c:222 |
| FUN1_StoreEqcData | sr1.c:243-249 | LLR-LA-002、LLR-LB-002 | sr1.c:237 |
| FUN1_ProcessEqaValidOutput | sr1.c:275-354 | LLR-COM-001、LLR-COM-002（并消费 LLR-LA-001~003 / LLR-LB-001~003 / LLR-LC-001~002；LC 路径体现 LLR-COM-003） | sr1.c:256-273 |

**后向覆盖统计**：**22/22 个代码元素**（14 函数 + 8 结构/常量）均有 ≥1 条 LLR 追溯注释（孤儿 **0**）；每条 LLR 均有对应代码元素承载（与 §2-d 前向表互为镜像，一致）。

---

## 3. DO-178C 适用目标（SR→HLR 层，§6.3.1）

| 目标 ID | 目标内容 | DO-178C 引用 | 本矩阵支撑 | 状态 |
|---------|---------|--------------|-----------|------|
| A3-1 | HLR 符合系统需求 | §6.3.1.a | §1 前向表：每条 SR 条款均有对应 HLR 承载其语义 | 符合性由 HLR 评审（DA-02 输出 + 上游评估）确认；本矩阵提供追溯证据 |
| A3-2 | HLR 准确且一致 | §6.3.1.b | §1/§2 表双向一致：10 条 HLR 与 10 项 SR 条款级来源一一对应，无重复映射、无冲突映射 | 符合性由 HLR 评审确认；本矩阵提供一致性证据 |
| A3-6 | HLR 可追溯至系统需求 | §6.3.1.f | §1 前向表（13 SR 侧条目 → 10 HLR）+ §2 后向表（10 HLR → SR）覆盖 100%，无孤儿、无缺口 | **核心目标，本矩阵直接支撑，符合** |

### 3.2 HLR→LLR 层适用目标（§6.4，DAL D）

| 目标 ID | 目标内容 | DO-178C 引用 | 适用性（DAL D） | 状态 |
|---------|---------|--------------|----------------|------|
| A4-1 ~ A4-8 | LLR 验证目标（LLR 符合 HLR、准确一致、可追溯等） | §6.4 表 A-4 | **不适用**：项目配置 `do178c_applicable.llr_verification = []`，DAL D 不注入任何 LLR 验证目标；A4-* 仅适用于 DAL A/B/C | 不声明符合性（本矩阵不主张 A4-* 合规） |

**说明**：HLR→LLR 层在 DAL D **无适用验证目标**，因此本层**不声明任何 DO-178C 目标符合性**。§2-b/§2-c 的 HLR→LLR 前向/后向追溯表作为**结构性追溯证据**提供（覆盖 100%、零孤儿，见 §4.4），供后续设计/代码/测试阶段（A6-* 于测试阶段适用）使用；LLR 各条目 Verifiability 属性仅为需求元数据，非符合性声明。

### 3.3 LLR→Code 层适用目标（编码验证，§6.4.2，DAL D）

| 目标 ID | 目标内容 | DO-178C 引用 | 适用性（DAL D） | 状态 |
|---------|---------|--------------|----------------|------|
| A5-1 / A5-2 / A5-4 | 编码验证目标（源代码符合 LLR 且准确一致、源代码符合标准等） | §6.4.2 表 A-5 | **不适用**：项目配置 `do178c_applicable.code_verification = []`，DAL D 不注入任何编码验证目标；A5-* 仅适用于 DAL A/B/C | 不声明符合性（本矩阵不主张 A5-* 合规） |

**说明**：LLR→Code 层在 DAL D **无适用验证目标**，因此本层**不声明任何 DO-178C 目标符合性**。§2-d/§2-e 的 LLR→Code 前向/后向追溯表作为**结构性追溯证据**提供（覆盖 100%、零孤儿，见 §4.5）。DA-06 code_check.md（任务 code_generation-T02）执行的编译/静态分析/测试为**项目内部代码检查活动**（双编译器零警告、24/24 测试通过、11/11 追溯覆盖），非 DO-178C A5-* 符合性声明（code_check.md §5 已显式声明 A5-* N/A）。

---

## 4. 覆盖完整性评估

### 4.1 覆盖率汇总

| 维度 | 统计口径 | 已覆盖 | 未覆盖 | 覆盖率 |
|------|---------|--------|--------|--------|
| 前向：SR 侧条目 → HLR | SR 条款级 9 项 + 全局行为 1 项 + 表格级 3 项 = 13 项 | 13 | 0 | **100%** |
| 后向：HLR → SR | 10 条 HLR 条目 | 10 | 0 | **100%** |

### 4.2 缺口分析（GAP Analysis）

- 未发现无 HLR 覆盖的 SR 条款（0 项）。
- SR 中所有需求条款（§1a/§1b/§1c、§2a/§2b/§2c、§3）及关键观察、需求分析表、数据关联关系表、规则提取表均已追溯至 HLR。
- **缺口：0**。

### 4.3 孤儿检查（Orphan Check）

- 未发现无 SR 来源的 HLR 条目（0 项）；每条 HLR 的 `Source` 字段均指向明确的 SR 条款。
- **孤儿：0**。

### 4.4 HLR→LLR 层完整性验证

#### 4.4.1 HLR→LLR 覆盖率汇总

| 维度 | 统计口径 | 已覆盖 | 未覆盖 | 覆盖率 |
|------|---------|--------|--------|--------|
| 前向：HLR → LLR | 10 条 HLR 条目 | 10 | 0 | **100%** |
| 后向：LLR → HLR | 11 条 LLR 条目（均有非空 `Source` 字段） | 11 | 0 | **100%** |

映射形态：唯一来源 7 条（LLR-LA-001~003、LLR-LB-001~003、LLR-LC-001）＋ 多来源约束 2 条（LLR-LC-002 主来源 HLR-LC-002 并受 HLR-LC-003 约束；LLR-LC-001 同理）＋ 一对多 2 组（HLR-LC-003→LLR-LC-001/002/COM-003；HLR-COM-001→LLR-COM-001/002）。

#### 4.4.2 缺口分析（GAP Analysis，HLR→LLR 层）

- 未发现无 LLR 覆盖的 HLR 条目（0 项）：10/10 条 HLR 均有 ≥1 条 LLR 承载其语义（HLR-LC-003 由 LLR-LC-001/002 约束 + LLR-COM-003 固化；HLR-COM-001 由 LLR-COM-001/002 拆分落实）。
- 与 `llr.md`「需求分解汇总表」「HLR→LLR 追溯矩阵」结论一致（DA-02 自检覆盖率 100%）。
- **缺口：0**。

#### 4.4.3 孤儿检查（Orphan Check，HLR→LLR 层）

- 未发现无 HLR 来源的 LLR 条目（0 项）：11/11 条 LLR 的 `Source` 字段均指向明确的 HLR 条目（含约束来源）。
- **孤儿：0**。

### 4.5 LLR→Code 层完整性验证

#### 4.5.1 LLR→Code 覆盖率汇总

| 维度 | 统计口径 | 已覆盖 | 未覆盖 | 覆盖率 |
|------|---------|--------|--------|--------|
| 前向：LLR → Code | 11 条 LLR 条目（均有 ≥1 个代码元素） | 11 | 0 | **100%** |
| 后向：Code → LLR | 22 个代码元素（14 函数 + 8 结构/常量，均有 LLR 追溯注释） | 22 | 0 | **100%** |

映射形态：LLR→Code 均为唯一映射（每条 LLR 对应明确函数/结构/常量，11/11 与 code_check.md §3 一致）；Code→LLR 存在一对多（如 FUN1_ProcessEqaValidOutput → LLR-COM-001/002 并消费 8 条通道条目；FUN1_CompareLcMatch / FUN1_LcOutputAllowed 同时体现 LLR-COM-003 约束），与代码注释一致。

#### 4.5.2 缺口分析（GAP Analysis，LLR→Code 层）

- 未发现无代码落实点的 LLR 条目（0 项）：11/11 条 LLR 均有 ≥1 个代码元素承载（函数/结构体/常量），与 `code_check.md` §3 追溯覆盖表（11/11 covered，DA-06 逐条核对）一致。
- **缺口：0**。

#### 4.5.3 孤儿检查（Orphan Check，LLR→Code 层）

- 未发现无 LLR 追溯注释的代码元素（0 项）：sr1.c 全部 14 个函数定义与 sr1.h 全部 8 个结构/常量均带 LLR 追溯注释（DA-06 静态分析确认函数注释头覆盖 100%）。
- **孤儿：0**。

---

## 5. 追溯链数据流图

```
┌─────────────────────────── SR-1（FUN1数据对比输出）───────────────────────────┐
│ §1a → HLR-LA-001（有效性检查）      §2a → HLR-LB-001（有效性检查）              │
│ §1b → HLR-LA-002（一致性比较）      §2b → HLR-LB-002（一致性比较）              │
│ §1c → HLR-LA-003（输出抑制）        §2c → HLR-LB-003（输出抑制）                │
│ §3  → HLR-LC-001（一致性比较）      §3  → HLR-LC-002（输出抑制）                │
│ §3 关键观察 → HLR-LC-003（无有效性检查，设计意图显式声明）                       │
│ §1/§2/§3 全局 → HLR-COM-001（周期条件输出通用行为）                             │
└───────────────────────────────────────────────────────────────────────────────┘
         ▲ 前向 13 SR 侧条目 → 10 HLR（100%）｜ 后向 10 HLR → SR（100%，无孤儿）
```

### 5.2 HLR→LLR 层追溯链数据流图

```
┌────────────────────────── HLR 层（10 条目）──────────────────────────┐
│ HLR-LA-001 → LLR-LA-001（有效性评估）   HLR-LB-001 → LLR-LB-001      │
│ HLR-LA-002 → LLR-LA-002（一致性比较）   HLR-LB-002 → LLR-LB-002      │
│ HLR-LA-003 → LLR-LA-003（输出门控）     HLR-LB-003 → LLR-LB-003      │
│ HLR-LC-001 → LLR-LC-001（一致性比较）   HLR-COM-001 → LLR-COM-001    │
│ HLR-LC-002 → LLR-LC-002（输出门控）     HLR-COM-001 → LLR-COM-002    │
│ HLR-LC-003 → LLR-COM-003（不对称性保持）＋ 约束 LLR-LC-001/LLR-LC-002 │
└──────────────────────────────────────────────────────────────────────┘
         ▼ 前向 10 HLR → 11 LLR（100%）｜ 后向 11 LLR → HLR（100%，无孤儿）
┌────────────────────────── LLR 层（11 条目）──────────────────────────┐
│ LLR-LA-001~003（LA 链）  LLR-LB-001~003（LB 链）  LLR-LC-001~002      │
│ LLR-COM-001（周期调度）  LLR-COM-002（通道独立）  LLR-COM-003（约束） │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.3 LLR→Code 层追溯链数据流图

```
┌────────────────────────── LLR 层（11 条目）──────────────────────────┐
│ LLR-LA-001~003（LA 链）  LLR-LB-001~003（LB 链）  LLR-LC-001~002      │
│ LLR-COM-001（周期调度）  LLR-COM-002（通道独立）  LLR-COM-003（约束） │
└──────────────────────────────────────────────────────────────────────┘
         ▼ 前向 11 LLR → Code（100%）｜ 后向 22 Code 元素 → LLR（100%，无孤儿）
┌────────────────────────── Code 层（sr1.c / sr1.h）───────────────────┐
│ FUN1_IsLaDataValid / EQA_Data_t.la_valid      ← LLR-LA-001           │
│ FUN1_CompareLaMatch / EQC_Data_t.la           ← LLR-LA-002           │
│ FUN1_LaOutputAllowed / EQA_Output_t.la_out_*  ← LLR-LA-003           │
│ FUN1_IsLbDataValid / EQA_Data_t.lb_valid      ← LLR-LB-001           │
│ FUN1_CompareLbMatch / EQC_Data_t.lb           ← LLR-LB-002           │
│ FUN1_LbOutputAllowed / EQA_Output_t.lb_out_*  ← LLR-LB-003           │
│ FUN1_CompareLcMatch / EQB_Data_t.lc           ← LLR-LC-001           │
│ FUN1_LcOutputAllowed / EQA_Output_t.lc_out_*  ← LLR-LC-002           │
│ PROCESS_CYCLE_MS / FUN1_ProcessEqaValidOutput ← LLR-COM-001          │
│ FUN1_ProcessEqaValidOutput（三通道独立判定）   ← LLR-COM-002          │
│ LC 路径无有效性分支（FUN1_CompareLcMatch 等）  ← LLR-COM-003（AMB-04）│
└──────────────────────────────────────────────────────────────────────┘
```

---

## 6. 追溯性限制说明（AMB-01 ~ AMB-07）

以下歧义由 DA-01 标记、经人工评审确认为 **SR 固有（SR-inherent）**，本阶段不消解、不补充工程假设（原则：只记录不消解）。它们**不影响追溯链接的结构完整性**，但影响链接所承载语义的最终可验证性，作为追溯性限制记录如下：

| 编号 | 维度 | 对追溯/验证的影响 | 处理 |
|------|------|------------------|------|
| AMB-01 | 周期语义（时长/边界/触发/输出时刻未定义） | HLR-LA-001/002、HLR-LB-001/002、HLR-LC-001、HLR-COM-001 中「每个周期」行为的验证依赖其消解 | 追溯链接保持，验证深度受限 |
| AMB-02 | 有效性定义（判据未定义） | HLR-LA-001/003、HLR-LB-001/003 有效性分支的验证依赖其消解 | 追溯链接保持，验证深度受限 |
| AMB-03 | 比较方法（比较语义未定义） | HLR-LA-002/003、HLR-LB-002/003、HLR-LC-001/002 一致性判定验证依赖其消解 | 追溯链接保持，验证深度受限 |
| AMB-04 | LC 有效性不对称（设计意图已确认） | HLR-LC-003 为正式记录；下游不得「补全」LC 有效性检查 | 追溯链接保持；作为显式记录条目 |
| AMB-05 | 错误处理缺失（抑制范围/故障行为未定义） | HLR-LA-003、HLR-LB-003、HLR-LC-002、HLR-COM-001 抑制行为边界验证受限；`req_analysis.md` TS-10（比较数据缺失场景）期望行为未定义 | 追溯链接保持；TS-10 场景暂挂起 |
| AMB-06 | 数据类型/格式未定义 | 全部输出相关条目的数据级验证受限 | 追溯链接保持 |
| AMB-07 | 数据来源未定义（LA/LB 生成方式未指明） | HLR-LA-001/002、HLR-LB-001/002 输入来源验证受限；与 TS-10 关联 | 追溯链接保持 |

**结论**：AMB-01~07 属于 SR 语义层未决项，不影响 SR→HLR 追溯链的存在性与完整性（结构性覆盖率 100%），但相关行为的**验证深度**待歧义消解后提升。已随本任务 `unresolved` 上报，不触发新的追溯缺口。

---

## 附注

- 本矩阵由 DA-12 (trace-maint) 依据既有制品（sr.md / req_analysis.md / hlr.md / llr.md / sr1.c / sr1.h / code_check.md）的权威映射构建，仅记录已存在的追溯关系，未生成或修改任何制品内容。
- 本矩阵现覆盖三层追溯：SR→HLR（原 sr_to_hlr-T03 构建，§1/§2/§3 保持原样）、HLR→LLR（hlr_to_llr-T02 扩展：§2-b/§2-c、§3.2、§4.4、§5.2，依据 DA-02 hlr_to_llr-T01 重新生成的 llr.md 权威 `Source` 字段）与 LLR→Code（本次 code_generation-T03 扩展：§2-d/§2-e、§3.3、§4.5、§5.3，依据 DA-05 代码追溯注释 + DA-06 code_check.md §3）；LLR→Test、Code→Test 追溯不属于本任务范围，留待测试阶段扩展。
- HLR→LLR 层在 DAL D 无适用验证目标（`llr_verification = []`），本矩阵不声明 A4-* 符合性；LLR 层新增未决项 LLR-AMB-08~11（llr.md 记录，只记录不消解）随本任务 `unresolved` 上报，不触发追溯缺口。
- LLR→Code 层在 DAL D 无适用验证目标（`code_verification = []`），本矩阵不声明 A5-* 符合性；LLR→Code 链接全部取自代码追溯注释（sr1.h「LLR→Code 追溯矩阵」块 sr1.h:8-19 + sr1.c 文件头/逐函数注释，DA-05 code_generation-T01 输出）与 code_check.md §3 追溯覆盖表（DA-06 code_generation-T02 逐条核对 11/11），两来源完全一致，未发明任何链接，无「待确认」项。
- 任务链：sr_to_hlr-T01（DA-01 需求分析）→ sr_to_hlr-T02（DA-02 需求分解）→ sr_to_hlr-T03（DA-12 追溯维护）→ hlr_to_llr-T01（DA-02 需求分解，重新生成 llr.md）→ hlr_to_llr-T02（DA-12 追溯维护）→ code_generation-T01（DA-05 代码生成，再生成 sr1.c/sr1.h）→ code_generation-T02（DA-06 代码检查）→ code_generation-T03（DA-12 追溯维护，本扩展）。
