/*
 * FUN1 数据对比输出 — 实现 (sr1.c)
 *
 * 来源: LLR 低级需求直接生成代码 (DO-178C DAL D, LLM 直接路径, 跳过详细设计)
 * 生成依据: projects/sr1/requirements/llr.md (当前 LLR 编号体系 LLR-{CH}-{NN})
 *
 * LLR→Code 追溯:
 *   LLR-COM-001 → PROCESS_CYCLE_MS 常量定义 (header) / FUN1_ProcessEqaValidOutput() 周期处理主入口
 *   LLR-LA-001  → FUN1_IsLaDataValid()  LA 有效性评估 (结果经 EQA_Data_t.la_valid 消费)
 *   LLR-LA-002  → FUN1_CompareLaMatch() LA-EQC.LA 一致性比较 (字段逐一相等, 零动态内存)
 *   LLR-LA-003  → FUN1_LaOutputAllowed() LA 输出门控 (la_valid && la_match)
 *   LLR-LB-001  → FUN1_IsLbDataValid()  LB 有效性评估 (结果经 EQA_Data_t.lb_valid 消费)
 *   LLR-LB-002  → FUN1_CompareLbMatch() LB-EQC.LB 一致性比较 (字段逐一相等, 零动态内存)
 *   LLR-LB-003  → FUN1_LbOutputAllowed() LB 输出门控 (lb_valid && lb_match)
 *   LLR-LC-001  → FUN1_CompareLcMatch() LC-EQB.LC 一致性比较 (无有效性检查)
 *   LLR-LC-002  → FUN1_LcOutputAllowed() LC 输出门控 (仅 lc_match 单一判据)
 *   LLR-COM-002 → FUN1_ProcessEqaValidOutput() 三通道独立评估 (互不耦合)
 *   LLR-COM-003 → LC 路径无有效性分支 (LC 不对称性保持, 设计约束 AMB-04)
 *
 * 关键约束:
 *   - 零动态内存分配 (无 malloc/realloc/calloc/free)
 *   - 无递归, 有界循环 (本实现无循环)
 *   - 固定周期处理 (LLR-COM-001)
 *   - LC 无有效性检查 (LLR-LC-001, LLR-COM-003, 设计意图 AMB-04)
 */

#include "sr1.h"

/* ====================================================================
 * 数据范围配置 (LLR-LA-001, LLR-LB-001)
 * ==================================================================== */

/**
 * FUN1_SetRangeDefault — 用默认值初始化范围配置 (LLR-LA-001, LLR-LB-001)
 *
 * 调用方在使用范围配置前调用。cfg 为 NULL 时不执行任何动作 (无效指针最小处理)。
 */
void FUN1_SetRangeDefault(Fun1_RangeConfig_t *cfg)
{
    if (cfg != NULL) {
        *cfg = FUN1_DEFAULT_RANGE;
    }
}

/**
 * FUN1_SetRangeLa — 配置 LA 数据有效范围 (LLR-LA-001)
 *
 * 调用时机: 系统启动时或数据规格变更时调用一次。
 * cfg 为 NULL 时不执行任何动作 (无效指针最小处理)。
 */
void FUN1_SetRangeLa(Fun1_RangeConfig_t *cfg, double lo, double hi)
{
    if (cfg != NULL) {
        cfg->la_lo = lo;
        cfg->la_hi = hi;
    }
}

/**
 * FUN1_SetRangeLb — 配置 LB 数据有效范围 (LLR-LB-001)
 *
 * 调用时机: 系统启动时或数据规格变更时调用一次。
 * cfg 为 NULL 时不执行任何动作 (无效指针最小处理)。
 */
void FUN1_SetRangeLb(Fun1_RangeConfig_t *cfg, double lo, double hi)
{
    if (cfg != NULL) {
        cfg->lb_lo = lo;
        cfg->lb_hi = hi;
    }
}

/* ====================================================================
 * 有效性评估 (LLR-LA-001, LLR-LB-001)
 * ==================================================================== */

/**
 * FUN1_IsLaDataValid — LA 数据有效性评估 (LLR-LA-001)
 *
 * 最小结构式评估:
 *   条件 (a): la 指针非空 且 cfg 指针非空  (无效指针 → 视为无效, 不引入额外语义)
 *   条件 (b): 数据在预期有效范围内 (cfg->la_lo <= *la <= cfg->la_hi)
 * 返回 true 当且仅当 (a) AND (b) 均满足。
 *
 * 注意: 有效性判定准则 (范围/校验/新鲜度等) 未定义 (AMB-02), 本函数仅落实
 * 「存在有效性评估」的结构性要求 (LLR-LA-001); 调用方可将结果置入
 * EQA_Data_t.la_valid 供 FUN1_ProcessEqaValidOutput 消费。
 */
bool FUN1_IsLaDataValid(const double *la, const Fun1_RangeConfig_t *cfg)
{
    /* 条件 (a): 指针非空 */
    if (la == NULL || cfg == NULL) {
        return false;
    }

    /* 条件 (b): 数据在预期有效范围内 */
    if ((*la < cfg->la_lo) || (*la > cfg->la_hi)) {
        return false;
    }

    return true;
}

/**
 * FUN1_IsLbDataValid — LB 数据有效性评估 (LLR-LB-001)
 *
 * 与 FUN1_IsLaDataValid 对称 (LLR-LB-001 与 LLR-LA-001 对称):
 *   条件 (a): lb 指针非空 且 cfg 指针非空
 *   条件 (b): 数据在预期有效范围内 (cfg->lb_lo <= *lb <= cfg->lb_hi)
 * 返回 true 当且仅当 (a) AND (b) 均满足。
 */
bool FUN1_IsLbDataValid(const double *lb, const Fun1_RangeConfig_t *cfg)
{
    /* 条件 (a): 指针非空 */
    if (lb == NULL || cfg == NULL) {
        return false;
    }

    /* 条件 (b): 数据在预期有效范围内 */
    if ((*lb < cfg->lb_lo) || (*lb > cfg->lb_hi)) {
        return false;
    }

    return true;
}

/* ====================================================================
 * 一致性比较 (LLR-LA-002, LLR-LB-002, LLR-LC-001)
 * ==================================================================== */

/**
 * FUN1_CompareLaMatch — LA 一致性比较 (LLR-LA-002)
 *
 * 将本地 LA 数据与 EQC.LA 数据进行字段逐一相等比较 (==)。
 * 所有字段完全匹配 → true; 任一字段不匹配 → false。
 * 不涉及内存分配 (禁止 malloc/realloc/calloc)。
 * 比较语义 (逐位相等/容差/粒度/编码域) 未定义 (AMB-03), 本条不补充。
 */
bool FUN1_CompareLaMatch(double la_local, double la_remote)
{
    return (la_local == la_remote);
}

/**
 * FUN1_CompareLbMatch — LB 一致性比较 (LLR-LB-002)
 *
 * 将本地 LB 数据与 EQC.LB 数据进行字段逐一相等比较 (==)。
 * 所有字段完全匹配 → true; 任一字段不匹配 → false。
 * 不涉及内存分配。比较语义未定义 (AMB-03), 本条不补充。
 */
bool FUN1_CompareLbMatch(double lb_local, double lb_remote)
{
    return (lb_local == lb_remote);
}

/**
 * FUN1_CompareLcMatch — LC 一致性比较 (LLR-LC-001)
 *
 * 将本地 LC 数据与 EQB.LC 数据进行字段逐一相等比较 (==)。
 * 所有字段完全匹配 → true; 任一字段不匹配 → false。
 * 不涉及内存分配。
 *
 * 注意: LC 路径不执行任何有效性评估、无有效性标志、无有效性分支
 * (LLR-LC-001, LLR-COM-003, 设计意图 AMB-04) — 本函数仅执行一致性比较。
 */
bool FUN1_CompareLcMatch(double lc_local, double lc_remote)
{
    return (lc_local == lc_remote);
}

/* ====================================================================
 * 输出门控 (LLR-LA-003, LLR-LB-003, LLR-LC-002)
 * ==================================================================== */

/**
 * FUN1_LaOutputAllowed — LA 输出允许判定 (LLR-LA-003)
 *
 * 输出条件:
 *   (a) la_valid == true  (LLR-LA-001 评估结果)
 *   (b) la_match == true  (LLR-LA-002 比较结果)
 * 仅当 (a) AND (b) 同时满足时允许输出; 任一不满足 → 抑制本周期 LA 输出
 * (抑制期间下游接口行为未定义, LLR-AMB-10, 本条不定义)。
 */
bool FUN1_LaOutputAllowed(bool la_valid, bool la_match)
{
    return (la_valid && la_match);
}

/**
 * FUN1_LbOutputAllowed — LB 输出允许判定 (LLR-LB-003)
 *
 * 输出条件:
 *   (a) lb_valid == true  (LLR-LB-001 评估结果)
 *   (b) lb_match == true  (LLR-LB-002 比较结果)
 * 仅当 (a) AND (b) 同时满足时允许输出; 任一不满足 → 抑制本周期 LB 输出
 * (抑制期间下游接口行为未定义, LLR-AMB-10, 本条不定义)。
 */
bool FUN1_LbOutputAllowed(bool lb_valid, bool lb_match)
{
    return (lb_valid && lb_match);
}

/**
 * FUN1_LcOutputAllowed — LC 输出允许判定 (LLR-LC-002)
 *
 * 输出条件:
 *   (a) lc_match == true  (LLR-LC-001 比较结果)
 * 输出判定仅依赖一致性单一判据, 不包含任何有效性条件
 * (LC 无有效性概念, LLR-LC-002, LLR-COM-003, AMB-04)。
 * 这与 LA/LB 需要同时满足 valid AND match 不同 — 该差异为设计意图, 必须保留。
 */
bool FUN1_LcOutputAllowed(bool lc_match)
{
    return lc_match;
}

/* ====================================================================
 * EQA 数据收发接口 (LLR-AMB-11)
 * ==================================================================== */

/**
 * FUN1_StoreEqbData — 更新 EQA 内部缓存中的 EQB 数据 (LLR-LC-001, LLR-AMB-11)
 *
 * 每个周期收到新 EQB 数据时调用, 更新缓存并置已接收标志。
 * 数据获取接口未定义 (LLR-AMB-11), 本函数仅提供最小存储动作。
 * cache/eqb 为 NULL 时不执行任何动作 (无效指针最小处理)。
 */
void FUN1_StoreEqbData(EQA_Cache_t *cache, const EQB_Data_t *eqb)
{
    if (cache != NULL && eqb != NULL) {
        cache->eqb = *eqb;
        cache->eqb_valid = true;
    }
}

/**
 * FUN1_StoreEqcData — 更新 EQA 内部缓存中的 EQC 数据 (LLR-LA-002, LLR-LB-002, LLR-AMB-11)
 *
 * 每个周期收到新 EQC 数据时调用, 更新缓存并置已接收标志。
 * 数据获取接口未定义 (LLR-AMB-11), 本函数仅提供最小存储动作。
 * cache/eqc 为 NULL 时不执行任何动作 (无效指针最小处理)。
 */
void FUN1_StoreEqcData(EQA_Cache_t *cache, const EQC_Data_t *eqc)
{
    if (cache != NULL && eqc != NULL) {
        cache->eqc = *eqc;
        cache->eqc_valid = true;
    }
}

/* ====================================================================
 * 周期输出处理主入口 (LLR-COM-001, LLR-COM-002)
 * ==================================================================== */

/**
 * FUN1_ProcessEqaValidOutput — EQA 周期输出处理 (LLR-COM-001, LLR-COM-002)
 *
 * 每个处理周期到达时调用一次 (固定周期, PROCESS_CYCLE_MS, LLR-COM-001),
 * 按固定顺序执行三通道独立评估与输出判定 (LLR-COM-002):
 *
 *   Step 1: LA 有效性标志消费      (LLR-LA-001) → la_valid (eqa->la_valid)
 *   Step 2: LA 一致性比较          (LLR-LA-002) → la_match (vs EQC.LA)
 *   Step 3: LA 输出门控            (LLR-LA-003) → out.la_out_*  (la_valid && la_match)
 *   Step 4: LB 有效性标志消费      (LLR-LB-001) → lb_valid (eqa->lb_valid)
 *   Step 5: LB 一致性比较          (LLR-LB-002) → lb_match (vs EQC.LB)
 *   Step 6: LB 输出门控            (LLR-LB-003) → out.lb_out_*  (lb_valid && lb_match)
 *   Step 7: LC 一致性比较          (LLR-LC-001) → lc_match (vs EQB.LC)  — 无有效性评估
 *   Step 8: LC 输出门控            (LLR-LC-002) → out.lc_out_*  (仅 lc_match)
 *
 * 三路独立判定、分别输出、分别抑制 (LLR-COM-002):
 * 任一路输出失败不影响其他通道输出结果。
 *
 * 无效指针 (eqa/cache/cfg 任一为 NULL) → 返回全抑制输出 (视为无效/不一致, 最小处理)。
 */
EQA_Output_t FUN1_ProcessEqaValidOutput(
    const EQA_Data_t *eqa,
    const EQA_Cache_t *cache,
    const Fun1_RangeConfig_t *cfg
)
{
    EQA_Output_t out = {0};  /* 初始化为全抑制 (LLR-AMB-10: 抑制语义未定义, 取最小静默) */

    /* 无效指针最小处理: 视为无效/不一致 → 全抑制 (不引入额外语义) */
    if (eqa == NULL || cache == NULL || cfg == NULL) {
        return out;
    }

    /* cfg: 有效性评估范围配置 (LLR-LA-001, LLR-LB-001)。
     * 周期有效性标志 la_valid/lb_valid 由调用方评估后传入 EQA_Data_t
     * (评估判据未定义, AMB-02; 调用方可经 FUN1_IsLaDataValid/FUN1_IsLbDataValid
     * 使用 cfg 完成范围评估)。本函数仅消费标志并按 LLR-LA-003/LLR-LB-003 门控,
     * 不在此重复评估, 以免与调用方评估结果冲突 (与 main.c 测试契约一致)。 */
    (void)cfg;

    /* ===== LA 通道: 有效性 且 一致性 (LLR-LA-001 ~ LLR-LA-003) ===== */

    /* Step 1: LA 周期有效性标志 (LLR-LA-001) */
    bool la_valid = eqa->la_valid;

    /* Step 2: LA 一致性比较 (LLR-LA-002)
     * 远端数据未接收 (eqc_valid=false) → 视为不一致 (LLR-AMB-11 最小处理) */
    bool la_match = false;
    if (cache->eqc_valid) {
        la_match = FUN1_CompareLaMatch(eqa->la, cache->eqc.la);
    }

    /* Step 3: LA 输出门控 (LLR-LA-003): 仅当 la_valid 且 la_match 时输出 */
    if (FUN1_LaOutputAllowed(la_valid, la_match)) {
        out.la_out_valid = true;
        out.la_out = eqa->la;
    }
    /* 否则 la_out_valid 保持 false → 抑制本周期 LA 输出 (LLR-LA-003) */

    /* ===== LB 通道: 有效性 且 一致性 (LLR-LB-001 ~ LLR-LB-003) ===== */

    /* Step 4: LB 周期有效性标志 (LLR-LB-001) */
    bool lb_valid = eqa->lb_valid;

    /* Step 5: LB 一致性比较 (LLR-LB-002)
     * 远端数据未接收 (eqc_valid=false) → 视为不一致 (LLR-AMB-11 最小处理) */
    bool lb_match = false;
    if (cache->eqc_valid) {
        lb_match = FUN1_CompareLbMatch(eqa->lb, cache->eqc.lb);
    }

    /* Step 6: LB 输出门控 (LLR-LB-003): 仅当 lb_valid 且 lb_match 时输出 */
    if (FUN1_LbOutputAllowed(lb_valid, lb_match)) {
        out.lb_out_valid = true;
        out.lb_out = eqa->lb;
    }
    /* 否则 lb_out_valid 保持 false → 抑制本周期 LB 输出 (LLR-LB-003) */

    /* ===== LC 通道: 仅一致性比较 (LLR-LC-001, LLR-LC-002) ===== */
    /* 注意: LC 无有效性概念 — 无 lc_valid 标志、无有效性评估、无有效性分支
     * (LLR-LC-001, LLR-COM-003, 设计意图 AMB-04)。此不对称性为设计意图,
     * 禁止归一化为 LA/LB 行为。 */

    /* Step 7: LC 一致性比较 (LLR-LC-001)
     * 远端数据未接收 (eqb_valid=false) → 视为不一致 (LLR-AMB-11 最小处理) */
    bool lc_match = false;
    if (cache->eqb_valid) {
        lc_match = FUN1_CompareLcMatch(eqa->lc, cache->eqb.lc);
    }

    /* Step 8: LC 输出门控 (LLR-LC-002): 仅依赖 lc_match 单一判据 */
    if (FUN1_LcOutputAllowed(lc_match)) {
        out.lc_out_valid = true;
        out.lc_out = eqa->lc;
    }
    /* 否则 lc_out_valid 保持 false → 抑制本周期 LC 输出 (LLR-LC-002) */

    /* 本周期处理完成 (LLR-COM-001): 返回后等待下一周期 (PROCESS_CYCLE_MS) 重新进入 */
    return out;
}
