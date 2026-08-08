/*
 * FUN1 数据对比输出模块 (SR-1 实现)
 *
 * 来源: LLR 低级需求直接生成代码 (DO-178C DAL D, LLM 直接路径, 跳过详细设计)
 * 功能: EQA 周期性评估 LA/LB/LC 数据有效性与一致性，按条件输出
 * 编译器: GCC (C11) ｜ 约束: 无动态内存分配、无递归、固定周期处理
 *
 * LLR→Code 追溯矩阵 (当前 LLR 编号体系 LLR-{CH}-{NN}):
 *   LLR-LA-001 → FUN1_IsLaDataValid() / EQA_Data_t.la_valid   LA 每周期有效性评估
 *   LLR-LA-002 → FUN1_CompareLaMatch() / EQC_Data_t.la        LA 与 EQC.LA 一致性比较
 *   LLR-LA-003 → FUN1_LaOutputAllowed() / EQA_Output_t.la_*   LA 输出门控 (la_valid && la_match)
 *   LLR-LB-001 → FUN1_IsLbDataValid() / EQA_Data_t.lb_valid   LB 每周期有效性评估
 *   LLR-LB-002 → FUN1_CompareLbMatch() / EQC_Data_t.lb        LB 与 EQC.LB 一致性比较
 *   LLR-LB-003 → FUN1_LbOutputAllowed() / EQA_Output_t.lb_*   LB 输出门控 (lb_valid && lb_match)
 *   LLR-LC-001 → FUN1_CompareLcMatch() / EQB_Data_t.lc        LC 与 EQB.LC 一致性比较 (无有效性检查)
 *   LLR-LC-002 → FUN1_LcOutputAllowed() / EQA_Output_t.lc_*   LC 输出门控 (仅 lc_match 单一判据)
 *   LLR-COM-001 → #define PROCESS_CYCLE_MS                    固定周期处理调度 (编译期常量)
 *   LLR-COM-002 → FUN1_ProcessEqaValidOutput() 三通道独立评估  (LA/LB/LC 互不耦合)
 *   LLR-COM-003 → LC 路径无有效性分支                           LC 不对称性保持 (设计约束, AMB-04)
 *
 * 关键设计约束 (LLR-COM-003 / AMB-04):
 *   LC 无有效性概念: 不定义 lc_valid 标志、不执行有效性评估、不引入有效性分支。
 *   禁止以任何名义将 LC 归一化为 LA/LB (有效性+一致性) 行为。
 */

#ifndef SR1_H
#define SR1_H

#include <stdbool.h>
#include <stddef.h>   /* NULL */

/* ---- 周期调度常量 (LLR-COM-001) ---- */
/* 固定周期处理: 周期时长以编译期常量参数化，实现不依赖运行时动态配置。
 * 数值 10ms 为既有基线值保留; 具体数值与命名未定义 (LLR-AMB-09, 只记录不消解)。 */
#define PROCESS_CYCLE_MS  10  /* 数据处理周期, 单位ms */

/* ---- 数据范围配置 (LLR-LA-001, LLR-LB-001) ---- */
/* 各通道数据有效范围参数。
 * 注意: 「数据有效」的判定准则 (范围/校验/新鲜度等) SR/HLR 未定义 (AMB-02)，
 * 本结构仅提供范围式评估所需的参数槽位，供调用方经 FUN1_IsLaDataValid/
 * FUN1_IsLbDataValid 评估后填入周期有效性标志。 */
typedef struct {
    double la_lo;          /* LA 数据下限 */
    double la_hi;          /* LA 数据上限 */
    double lb_lo;          /* LB 数据下限 */
    double lb_hi;          /* LB 数据上限 */
} Fun1_RangeConfig_t;

/* 默认范围配置 (LLR-LA-001, LLR-LB-001) - 调用方应根据实际数据规范覆盖 */
static const Fun1_RangeConfig_t FUN1_DEFAULT_RANGE = {
    .la_lo = -1000.0,
    .la_hi =  1000.0,
    .lb_lo = -1000.0,
    .lb_hi =  1000.0
};

/* ---- 数据类型 (LLR-AMB-08: 成员/类型/取值范围未定义, 采用最小结构) ---- */

/**
 * EQA 本周期待输出数据 (LLR-LA-001, LLR-LB-001)
 *
 * la_valid/lb_valid 为周期内有效性标志 (LLR-LA-001/LLR-LB-001 落实的布尔标志),
 * 由调用方按有效性评估结果置位 (评估判据未定义, AMB-02)。
 * 注: LC 无有效性标志 (LLR-LC-001, LLR-COM-003)。
 */
typedef struct {
    double la;        /* LA 待输出值 */
    double lb;        /* LB 待输出值 */
    double lc;        /* LC 待输出值 */
    bool   la_valid;  /* LA 周期有效性标志 (LLR-LA-001) */
    bool   lb_valid;  /* LB 周期有效性标志 (LLR-LB-001) */
} EQA_Data_t;

/**
 * EQB 提供的数据 (LLR-LC-001)
 *
 * EQB.LC 为 LC 一致性比较的远端参照值。
 */
typedef struct {
    double lc;        /* EQB.LC 比较值 */
} EQB_Data_t;

/**
 * EQC 提供的数据 (LLR-LA-002, LLR-LB-002)
 *
 * EQC.LA / EQC.LB 分别为 LA/LB 一致性比较的远端参照值。
 */
typedef struct {
    double la;        /* EQC.LA 比较值 */
    double lb;        /* EQC.LB 比较值 */
} EQC_Data_t;

/**
 * EQA 内部缓存: 维护已接收的 EQB/EQC 数据 (LLR-COM-002, LLR-AMB-11)
 *
 * 各通道每周期数据获取/存储/传递方式未定义 (LLR-AMB-11);
 * 本缓存为最小结构: 远端数据 + 已接收有效性标志。
 * 远端数据未接收时视为「不一致/不可比」→ 对应通道抑制 (与 main.c TC10 契约一致)。
 */
typedef struct {
    EQB_Data_t eqb;       /* 缓存的 EQB 数据 (LLR-LC-001) */
    bool       eqb_valid; /* EQB 数据是否已接收 */
    EQC_Data_t eqc;       /* 缓存的 EQC 数据 (LLR-LA-002, LLR-LB-002) */
    bool       eqc_valid; /* EQC 数据是否已接收 */
} EQA_Cache_t;

/**
 * EQA 输出结构 (LLR-LA-003, LLR-LB-003, LLR-LC-002)
 *
 * 每路输出独立有效标志:
 *   la_out_valid=true  → la_out 为本周期有效输出值
 *   la_out_valid=false → LA 被抑制 (抑制期间下游行为未定义, LLR-AMB-10)
 *   同理适用于 LB 和 LC。
 */
typedef struct {
    bool   la_out_valid;   /* LA 输出有效 (LLR-LA-003) */
    double la_out;         /* LA 输出值 */
    bool   lb_out_valid;   /* LB 输出有效 (LLR-LB-003) */
    double lb_out;         /* LB 输出值 */
    bool   lc_out_valid;   /* LC 输出有效 (LLR-LC-002) */
    double lc_out;         /* LC 输出值 */
} EQA_Output_t;

/* ---- 函数声明 (LLR-LA-001~003 / LLR-LB-001~003 / LLR-LC-001~002 / LLR-COM-001~003) ---- */

/* === 数据范围配置 (LLR-LA-001, LLR-LB-001) === */

/**
 * FUN1_SetRangeDefault — 使用默认范围初始化范围配置 (LLR-LA-001, LLR-LB-001)
 */
void FUN1_SetRangeDefault(Fun1_RangeConfig_t *cfg);

/**
 * FUN1_SetRangeLa — 配置 LA 数据有效范围 (LLR-LA-001)
 */
void FUN1_SetRangeLa(Fun1_RangeConfig_t *cfg, double lo, double hi);

/**
 * FUN1_SetRangeLb — 配置 LB 数据有效范围 (LLR-LB-001)
 */
void FUN1_SetRangeLb(Fun1_RangeConfig_t *cfg, double lo, double hi);

/* === 有效性评估 (LLR-LA-001, LLR-LB-001) === */

/**
 * FUN1_IsLaDataValid — LA 数据有效性评估 (LLR-LA-001)
 *
 * 结构式评估: 指针非空 且 数据在配置范围内。
 * 注意: 完整有效性判据 (范围/校验/新鲜度等) 未定义 (AMB-02)，
 * 本函数仅提供最小结构式评估; 调用方可将结果置入 EQA_Data_t.la_valid。
 *
 * 返回 true 当且仅当 (a) AND (b) 均满足:
 *   (a) la != NULL 且 cfg != NULL   (无效指针 → 视为无效, 不引入额外语义)
 *   (b) cfg->la_lo <= *la <= cfg->la_hi
 */
bool FUN1_IsLaDataValid(const double *la, const Fun1_RangeConfig_t *cfg);

/**
 * FUN1_IsLbDataValid — LB 数据有效性评估 (LLR-LB-001)
 *
 * 结构式评估: 指针非空 且 数据在配置范围内。
 * 判据细节同 FUN1_IsLaDataValid (AMB-02 未定义, 不补充)。
 *
 * 返回 true 当且仅当 (a) AND (b) 均满足:
 *   (a) lb != NULL 且 cfg != NULL
 *   (b) cfg->lb_lo <= *lb <= cfg->lb_hi
 */
bool FUN1_IsLbDataValid(const double *lb, const Fun1_RangeConfig_t *cfg);

/* === 一致性比较 (LLR-LA-002, LLR-LB-002, LLR-LC-001) === */

/**
 * FUN1_CompareLaMatch — LA 一致性比较 (LLR-LA-002)
 *
 * 比较本地 LA 值与 EQC.LA 值是否一致: 字段逐一相等比较 (==)。
 * 不涉及内存分配 (禁止 malloc/realloc/calloc)。
 * 比较语义 (逐位相等/容差/粒度) 未定义 (AMB-03), 本实现采用逐字段相等。
 */
bool FUN1_CompareLaMatch(double la_local, double la_remote);

/**
 * FUN1_CompareLbMatch — LB 一致性比较 (LLR-LB-002)
 *
 * 比较本地 LB 值与 EQC.LB 值是否一致: 字段逐一相等比较 (==)。
 * 不涉及内存分配。比较语义未定义 (AMB-03), 本实现采用逐字段相等。
 */
bool FUN1_CompareLbMatch(double lb_local, double lb_remote);

/**
 * FUN1_CompareLcMatch — LC 一致性比较 (LLR-LC-001)
 *
 * 比较本地 LC 值与 EQB.LC 值是否一致: 字段逐一相等比较 (==)。
 * 不涉及内存分配。
 * 注意: LC 路径不执行任何有效性评估、无有效性分支 (LLR-LC-001, LLR-COM-003,
 * 设计意图 AMB-04), 本函数仅执行一致性比较。
 */
bool FUN1_CompareLcMatch(double lc_local, double lc_remote);

/* === 输出门控 (LLR-LA-003, LLR-LB-003, LLR-LC-002) === */

/**
 * FUN1_LaOutputAllowed — LA 输出允许判定 (LLR-LA-003)
 *
 * 输出条件: (a) la_valid == true (LLR-LA-001 评估结果)
 *           (b) la_match == true (LLR-LA-002 比较结果)
 * 仅当 (a) AND (b) 同时满足时返回 true; 任一不满足 → 抑制本周期 LA 输出
 * (抑制期间下游接口行为未定义, LLR-AMB-10)。
 */
bool FUN1_LaOutputAllowed(bool la_valid, bool la_match);

/**
 * FUN1_LbOutputAllowed — LB 输出允许判定 (LLR-LB-003)
 *
 * 输出条件: (a) lb_valid == true (LLR-LB-001 评估结果)
 *           (b) lb_match == true (LLR-LB-002 比较结果)
 * 仅当 (a) AND (b) 同时满足时返回 true; 任一不满足 → 抑制本周期 LB 输出
 * (抑制期间下游接口行为未定义, LLR-AMB-10)。
 */
bool FUN1_LbOutputAllowed(bool lb_valid, bool lb_match);

/**
 * FUN1_LcOutputAllowed — LC 输出允许判定 (LLR-LC-002)
 *
 * 输出条件: (a) lc_match == true (LLR-LC-001 比较结果)
 * 输出判定仅依赖一致性单一判据, 不包含任何有效性条件
 * (LC 无有效性概念, LLR-LC-002, LLR-COM-003, AMB-04)。
 */
bool FUN1_LcOutputAllowed(bool lc_match);

/* === EQA 数据收发接口 (LLR-AMB-11) === */

/**
 * FUN1_StoreEqbData — 更新 EQA 内部缓存中的 EQB 数据 (LLR-LC-001, LLR-AMB-11)
 *
 * 数据获取接口未定义 (LLR-AMB-11); 本函数提供最小存储动作: 拷贝数据并置已接收标志。
 */
void FUN1_StoreEqbData(EQA_Cache_t *cache, const EQB_Data_t *eqb);

/**
 * FUN1_StoreEqcData — 更新 EQA 内部缓存中的 EQC 数据 (LLR-LA-002, LLR-LB-002, LLR-AMB-11)
 *
 * 数据获取接口未定义 (LLR-AMB-11); 本函数提供最小存储动作: 拷贝数据并置已接收标志。
 */
void FUN1_StoreEqcData(EQA_Cache_t *cache, const EQC_Data_t *eqc);

/* === 周期输出处理主入口 (LLR-COM-001, LLR-COM-002) === */

/**
 * FUN1_ProcessEqaValidOutput — EQA 周期输出处理 (LLR-COM-001, LLR-COM-002)
 *
 * 每个处理周期调用一次 (固定周期, PROCESS_CYCLE_MS, LLR-COM-001),
 * 按固定顺序执行三通道独立评估 (LLR-COM-002):
 *   1. LA 有效性标志消费 (LLR-LA-001) + 一致性比较 (LLR-LA-002) + 门控 (LLR-LA-003)
 *   2. LB 有效性标志消费 (LLR-LB-001) + 一致性比较 (LLR-LB-002) + 门控 (LLR-LB-003)
 *   3. LC 一致性比较 (LLR-LC-001) + 门控 (LLR-LC-002)  — 无有效性分支 (LLR-COM-003)
 *
 * 三路输出独立判定、分别输出、分别抑制 (LLR-COM-002):
 * 任一路输出失败不影响其他通道输出结果。
 *
 * @param eqa   EQA 本周期数据 (含 la_valid/lb_valid 周期有效性标志)
 * @param cache 缓存的 EQB/EQC 远端数据
 * @param cfg   数据范围配置 (供调用方有效性评估使用, 见 FUN1_IsLaDataValid)
 * @return      EQA_Output_t 三路输出结果
 */
EQA_Output_t FUN1_ProcessEqaValidOutput(
    const EQA_Data_t *eqa,
    const EQA_Cache_t *cache,
    const Fun1_RangeConfig_t *cfg
);

#endif /* SR1_H */
