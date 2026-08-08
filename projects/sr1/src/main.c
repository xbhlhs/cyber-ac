/*
 * FUN1 测试程序 — main.c
 *
 * 验证 SR-1 (FUN1数据对比输出) 的全部场景
 *
 * 测试覆盖:
 *   TC01: LA 有效+一致 → 输出
 *   TC02: LA 有效+不一致 → 抑制
 *   TC03: LA 无效 → 抑制（有效性检查失败）
 *   TC04: LB 有效+一致 → 输出
 *   TC05: LB 不一致 → 抑制
 *   TC06: LC 一致 → 输出（无有效性检查）
 *   TC07: LC 不一致 → 抑制
 *   TC08: 三路全部满足 → 全部输出
 *   TC09: 混合场景 — LA输出 LB抑制 LC输出
 *   TC10: 外部数据未就绪 → 全部抑制
 *   TC11: 三路独立验证 — LA失败不影响LB和LC
 */

#include <stdio.h>
#include <string.h>
#include "sr1.h"

#define ASSERT_EQ(a, b, name) \
    do { \
        if ((a) != (b)) { \
            printf("  FAIL %s: expected %d, got %d\n", name, (int)(b), (int)(a)); \
            failures++; \
        } else { \
            printf("  PASS %s\n", name); \
            passed++; \
        } \
    } while(0)

int main(void)
{
    int passed = 0, failures = 0;

    printf("=== FUN1 数据对比输出 — 测试用例 ===\n\n");

    /* ---- TC01: LA 有效+一致 → 输出 ---- */
    {
        printf("[TC01] LA 有效 + 与EQC.LA一致 → 期望输出LA\n");
        EQA_Data_t eqa = {.la = 42.0, .lb = 0, .lc = 0, .la_valid = true, .lb_valid = false};
        EQA_Cache_t cache = {.eqb_valid = false, .eqc_valid = true};
        cache.eqc.la = 42.0;

        EQA_Output_t out = FUN1_ProcessEqaValidOutput(&eqa, &cache, &FUN1_DEFAULT_RANGE);
        ASSERT_EQ(out.la_out_valid, true, "LA输出有效");
        ASSERT_EQ(out.la_out, 42.0, "LA输出值=42.0");
        ASSERT_EQ(out.lb_out_valid, false, "LB未激活");
        ASSERT_EQ(out.lc_out_valid, false, "LC未激活");
        printf("\n");
    }

    /* ---- TC02: LA 有效+不一致 → 抑制 ---- */
    {
        printf("[TC02] LA 有效 + 不一致 → 期望抑制LA\n");
        EQA_Data_t eqa = {.la = 42.0, .lb = 0, .lc = 0, .la_valid = true, .lb_valid = false};
        EQA_Cache_t cache = {.eqb_valid = false, .eqc_valid = true};
        cache.eqc.la = 99.0;  /* 不一致! */

        EQA_Output_t out = FUN1_ProcessEqaValidOutput(&eqa, &cache, &FUN1_DEFAULT_RANGE);
        ASSERT_EQ(out.la_out_valid, false, "LA被抑制(不一致)");
        printf("\n");
    }

    /* ---- TC03: LA 无效 → 抑制 ---- */
    {
        printf("[TC03] LA 无效 → 期望抑制LA（跳过一致性检查）\n");
        EQA_Data_t eqa = {.la = 42.0, .lb = 0, .lc = 0, .la_valid = false, .lb_valid = false};
        EQA_Cache_t cache = {.eqb_valid = false, .eqc_valid = true};
        cache.eqc.la = 42.0;  /* 一致但无效! */

        EQA_Output_t out = FUN1_ProcessEqaValidOutput(&eqa, &cache, &FUN1_DEFAULT_RANGE);
        ASSERT_EQ(out.la_out_valid, false, "LA被抑制(无效)");
        printf("\n");
    }

    /* ---- TC04: LB 有效+一致 → 输出 ---- */
    {
        printf("[TC04] LB 有效 + 一致 → 期望输出LB\n");
        EQA_Data_t eqa = {.la = 0, .lb = 77.0, .lc = 0, .la_valid = false, .lb_valid = true};
        EQA_Cache_t cache = {.eqb_valid = false, .eqc_valid = true};
        cache.eqc.lb = 77.0;

        EQA_Output_t out = FUN1_ProcessEqaValidOutput(&eqa, &cache, &FUN1_DEFAULT_RANGE);
        ASSERT_EQ(out.lb_out_valid, true, "LB输出有效");
        ASSERT_EQ(out.lb_out, 77.0, "LB输出值=77.0");
        printf("\n");
    }

    /* ---- TC05: LB 不一致 → 抑制 ---- */
    {
        printf("[TC05] LB 有效+不一致 → 期望抑制LB\n");
        EQA_Data_t eqa = {.la = 0, .lb = 77.0, .lc = 0, .la_valid = false, .lb_valid = true};
        EQA_Cache_t cache = {.eqb_valid = false, .eqc_valid = true};
        cache.eqc.lb = 88.0;  /* 不一致! */

        EQA_Output_t out = FUN1_ProcessEqaValidOutput(&eqa, &cache, &FUN1_DEFAULT_RANGE);
        ASSERT_EQ(out.lb_out_valid, false, "LB被抑制(不一致)");
        printf("\n");
    }

    /* ---- TC06: LC 一致 → 输出（无有效性检查！） ---- */
    {
        printf("[TC06] LC 一致 → 期望输出LC（无有效性检查，设计意图）\n");
        EQA_Data_t eqa = {.la = 0, .lb = 0, .lc = 55.0, .la_valid = false, .lb_valid = false};
        EQA_Cache_t cache = {.eqb_valid = true, .eqc_valid = false};
        cache.eqb.lc = 55.0;

        EQA_Output_t out = FUN1_ProcessEqaValidOutput(&eqa, &cache, &FUN1_DEFAULT_RANGE);
        ASSERT_EQ(out.lc_out_valid, true, "LC输出有效（无有效性检查）");
        ASSERT_EQ(out.lc_out, 55.0, "LC输出值=55.0");
        printf("\n");
    }

    /* ---- TC07: LC 不一致 → 抑制 ---- */
    {
        printf("[TC07] LC 不一致 → 期望抑制LC\n");
        EQA_Data_t eqa = {.la = 0, .lb = 0, .lc = 55.0, .la_valid = false, .lb_valid = false};
        EQA_Cache_t cache = {.eqb_valid = true, .eqc_valid = false};
        cache.eqb.lc = 99.0;  /* 不一致! */

        EQA_Output_t out = FUN1_ProcessEqaValidOutput(&eqa, &cache, &FUN1_DEFAULT_RANGE);
        ASSERT_EQ(out.lc_out_valid, false, "LC被抑制(不一致)");
        printf("\n");
    }

    /* ---- TC08: 三路全部满足 → 全部输出 ---- */
    {
        printf("[TC08] 三路全部满足 → 期望全部输出\n");
        EQA_Data_t eqa = {.la = 10.0, .lb = 20.0, .lc = 30.0, .la_valid = true, .lb_valid = true};
        EQA_Cache_t cache;
        memset(&cache, 0, sizeof(cache));
        cache.eqc_valid = true;
        cache.eqc.la = 10.0;
        cache.eqc.lb = 20.0;
        cache.eqb_valid = true;
        cache.eqb.lc = 30.0;

        EQA_Output_t out = FUN1_ProcessEqaValidOutput(&eqa, &cache, &FUN1_DEFAULT_RANGE);
        ASSERT_EQ(out.la_out_valid, true, "LA输出");
        ASSERT_EQ(out.lb_out_valid, true, "LB输出");
        ASSERT_EQ(out.lc_out_valid, true, "LC输出");
        printf("\n");
    }

    /* ---- TC09: 混合场景 ---- */
    {
        printf("[TC09] 混合: LA输出, LB抑制, LC输出\n");
        EQA_Data_t eqa = {.la = 10.0, .lb = 20.0, .lc = 30.0, .la_valid = true, .lb_valid = true};
        EQA_Cache_t cache;
        memset(&cache, 0, sizeof(cache));
        cache.eqc_valid = true;
        cache.eqc.la = 10.0;  /* LA一致 */
        cache.eqc.lb = 99.0;  /* LB不一致! */
        cache.eqb_valid = true;
        cache.eqb.lc = 30.0;  /* LC一致 */

        EQA_Output_t out = FUN1_ProcessEqaValidOutput(&eqa, &cache, &FUN1_DEFAULT_RANGE);
        ASSERT_EQ(out.la_out_valid, true, "LA输出");
        ASSERT_EQ(out.lb_out_valid, false, "LB抑制");
        ASSERT_EQ(out.lc_out_valid, true, "LC输出");
        printf("\n");
    }

    /* ---- TC10: 外部数据未就绪 → 全部抑制 ---- */
    {
        printf("[TC10] 外部数据未就绪 → 期望全部抑制\n");
        EQA_Data_t eqa = {.la = 10.0, .lb = 20.0, .lc = 30.0, .la_valid = true, .lb_valid = true};
        EQA_Cache_t cache;
        memset(&cache, 0, sizeof(cache));  /* eqb_valid=eqc_valid=false */

        EQA_Output_t out = FUN1_ProcessEqaValidOutput(&eqa, &cache, &FUN1_DEFAULT_RANGE);
        ASSERT_EQ(out.la_out_valid, false, "LA抑制(无EQC数据)");
        ASSERT_EQ(out.lb_out_valid, false, "LB抑制(无EQC数据)");
        ASSERT_EQ(out.lc_out_valid, false, "LC抑制(无EQB数据)");
        printf("\n");
    }

    /* ---- TC11: 三路独立验证 ---- */
    {
        printf("[TC11] 三路独立: LA失败, LB和LC不受影响\n");
        EQA_Data_t eqa = {.la = 10.0, .lb = 20.0, .lc = 30.0, .la_valid = false, .lb_valid = true};
        /* LA无效, 但LB有效+LC无有效性要求 */

        EQA_Cache_t cache;
        memset(&cache, 0, sizeof(cache));
        cache.eqc_valid = true;
        cache.eqc.la = 10.0;  /* LA一致但无效 */
        cache.eqc.lb = 20.0;  /* LB一致且有效 */
        cache.eqb_valid = true;
        cache.eqb.lc = 30.0;  /* LC一致 */

        EQA_Output_t out = FUN1_ProcessEqaValidOutput(&eqa, &cache, &FUN1_DEFAULT_RANGE);
        ASSERT_EQ(out.la_out_valid, false, "LA抑制(无效)");
        ASSERT_EQ(out.lb_out_valid, true, "LB输出(不受LA影响)");
        ASSERT_EQ(out.lc_out_valid, true, "LC输出(不受LA影响)");
        printf("\n");
    }

    /* ---- 结果汇总 ---- */
    printf("=== 测试完成 ===\n");
    printf("通过: %d, 失败: %d\n", passed, failures);
    return failures > 0 ? 1 : 0;
}
