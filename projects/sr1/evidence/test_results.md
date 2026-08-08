# 测试结果 — SR-1 FUN1 数据对比输出（EQA）

> **项目**: SR-1 / HLR-1 / LLR-1
> **DO-178C DAL**: D
> **执行者**: DA-10 (test-exec) ｜ 任务：test_execution-T01
> **上游输入**: `projects/sr1/tests/test_procedures.md`（DA-09）、`projects/sr1/tests/test_cases.md`（DA-08）、`projects/sr1/src/*.c/*.h`（DA-05）、根 Makefile
> **执行日期**: 2026-08-08（UTC 07:39）
> **执行环境**: Linux 主机（gcc 15.2.0），宿主机二进制 `projects/sr1/build/sr1`（目标环境 Cortex-M4 / arm-none-eabi-gcc 验证另见 DA-06 嵌入式编译证据，本报告聚焦宿主机可执行验证 + 静态分析）
> **DO-178C 目标**: A6-1（§6.4.a 正常范围）、A6-2（§6.4.b 鲁棒性）、A6-5（§6.4.e 目标计算机兼容性，见第 6 节推迟说明）

---

## 1. 编译验证（Compilation Verification）

### 1.1 编译器配置

| 项目 | 配置 |
|------|------|
| 编译器 | gcc（Ubuntu 15.2.0-16ubuntu1）15.2.0 |
| C 标准 | C11（`-std=c11`） |
| 警告级别 | `-Wall -Wextra -pedantic` |
| 优化级别 | `-O2` |
| 构建命令 | `make sr1-build`（自工作区根 `/home/c/workspace/fusion`） |
| 构建日志 | `/tmp/sr1-build.log`（`make sr1-clean && make sr1-build 2>&1 \| tee /tmp/sr1-build.log`） |
| 构建退出码 | **0** |

### 1.2 逐文件编译结果

| 源文件 | 目标文件 | 编译命令 | 警告数 | 错误数 | 结果 |
|--------|----------|----------|--------|--------|------|
| `projects/sr1/src/main.c` | `projects/sr1/build/main.o` | `gcc -Wall -Wextra -std=c11 -pedantic -O2 -c` | 0 | 0 | ✅ 通过 |
| `projects/sr1/src/sr1.c` | `projects/sr1/build/sr1.o` | `gcc -Wall -Wextra -std=c11 -pedantic -O2 -c` | 0 | 0 | ✅ 通过 |
| 链接（main.o + sr1.o） | `projects/sr1/build/sr1` | `gcc` | 0 | 0 | ✅ 通过 |

**警告总数: 0**（`grep -c "warning:" /tmp/sr1-build.log` = 0；`grep -i "warning\|error"` 无匹配）。

**结论**: 编译零警告零错误（DAL D 接受标准：`-Wall -Wextra -pedantic` 下零警告），构建成功，产物 `projects/sr1/build/sr1`（71392 字节，可执行）。

---

## 2. 动态内存静态分析（Dynamic Memory Static Analysis）

### 2.1 扫描命令与结果

| 检查项 | 命令 | 匹配数 | 匹配位置性质 | 结论 |
|--------|------|--------|--------------|------|
| malloc/realloc/calloc 调用 | `grep -rn '\bmalloc\b\|\brealloc\b\|\bcalloc\b' projects/sr1/src/` | 3 | **全部为注释**：`sr1.h:176`（"禁止 malloc/realloc/calloc"）、`sr1.c:21`（"零动态内存分配"）、`sr1.c:136`（"禁止 malloc/realloc/calloc"）——均为约束文档性说明，**零实际调用** | ✅ 通过 |
| free 调用 | `grep -rn '\bfree\s*(' projects/sr1/src/` | 0 | — | ✅ 通过 |
| `stdlib.h` 包含 | `grep -rn '#include' projects/sr1/src/` | 5 个包含，**无 stdlib.h**：`sr1.h`→`stdbool.h`/`stddef.h`；`sr1.c`→`sr1.h`；`main.c`→`stdio.h`/`string.h`/`sr1.h`（stdio/string 仅测试驱动 main.c 使用） | ✅ 通过 |

### 2.2 对应测试规程落实

| 规程 ID | 检查内容 | 执行方式 | 结果 |
|---------|----------|----------|------|
| TP-01-005 | 周期调度全程无 malloc/realloc/calloc | 上述 grep 全源扫描 | ✅ 通过（零调用） |
| TP-04-005 | LA 一致性比较路径无动态内存 | 上述 grep（LA 比较函数 `FUN1_CompareLaMatch` 体内无非分配调用） | ✅ 通过 |
| TP-07-005 | LB 一致性比较路径无动态内存 | 上述 grep（`FUN1_CompareLbMatch`） | ✅ 通过 |
| TP-09-006 | LC 一致性比较路径无动态内存 | 上述 grep（`FUN1_CompareLcMatch`） | ✅ 通过 |
| TP-09-005 | LC 数据路径无任何有效性判断逻辑 | `grep -rn 'lc_valid\|isValid' projects/sr1/src/` | ✅ 通过（2 处匹配均为注释中的设计约束说明，代码中无 `lc_valid` 标志、无有效性分支） |

> 注：测试规程中"cppcheck ≥ 1.90 或自定义 grep 脚本"二选一——本环境未安装 cppcheck，采用规程明确允许的自定义 grep 方式。

**结论**: 源码零动态内存分配调用，无 stdlib.h，LC 无有效性分支（LLR-COM-003 设计约束保持），静态分析全部通过。

---

## 3. 运行测试结果（Runtime Test Results）

### 3.1 执行信息

| 项目 | 内容 |
|------|------|
| 运行命令 | `make sr1-test`（自工作区根；等价于 `./projects/sr1/build/sr1`） |
| 测试日志 | `/tmp/sr1-test.log` |
| 退出码 | **0**（测试驱动 `return failures > 0 ? 1 : 0`） |
| 测试框架 | `main.c` 内置断言驱动（ASSERT_EQ），输出 PASS/FAIL 标记 |

### 3.2 逐用例断言结果（TC01–TC11，宿主机二进制）

| 用例 | 场景描述 | 断言 | 结果 |
|------|----------|------|------|
| TC01 | LA 有效 + 与 EQC.LA 一致 → 输出 | LA输出有效 / LA输出值=42.0 / LB未激活 / LC未激活 | 4/4 ✅ |
| TC02 | LA 有效 + 不一致 → 抑制 | LA被抑制(不一致) | 1/1 ✅ |
| TC03 | LA 无效 → 抑制（跳过一致性检查） | LA被抑制(无效) | 1/1 ✅ |
| TC04 | LB 有效 + 一致 → 输出 | LB输出有效 / LB输出值=77.0 | 2/2 ✅ |
| TC05 | LB 有效 + 不一致 → 抑制 | LB被抑制(不一致) | 1/1 ✅ |
| TC06 | LC 一致 → 输出（无有效性检查，设计意图） | LC输出有效（无有效性检查） / LC输出值=55.0 | 2/2 ✅ |
| TC07 | LC 不一致 → 抑制 | LC被抑制(不一致) | 1/1 ✅ |
| TC08 | 三路全部满足 → 全部输出 | LA输出 / LB输出 / LC输出 | 3/3 ✅ |
| TC09 | 混合场景：LA输出、LB抑制、LC输出 | LA输出 / LB抑制 / LC输出 | 3/3 ✅ |
| TC10 | 外部数据未就绪 → 全部抑制 | LA抑制(无EQC数据) / LB抑制(无EQC数据) / LC抑制(无EQB数据) | 3/3 ✅ |
| TC11 | 三路独立：LA失败不影响 LB/LC | LA抑制(无效) / LB输出(不受LA影响) / LC输出(不受LA影响) | 3/3 ✅ |

**合计: 11/11 用例通过，24/24 断言通过，0 失败，退出码 0。**

> 说明：宿主机测试驱动（main.c，DA-05 生成）以 TC01–TC11 编号组织，与 test_cases.md 的 TC-NM-XXX 编号体系（DA-08，44 条用例，其中 4 条挂起）为不同粒度的两层验证；本报告第 3.2 节记录**实际执行**的宿主机断言级结果，第 5 节按规程 ID 追溯 DA-09 规程覆盖情况。TC10（外部数据未就绪→全抑制）在宿主机上按 test_cases.md TC-10-001 挂起声明**不判定**其语义正确性，仅记录实际行为为全抑制（与代码 LLR-AMB-11 最小处理一致，未虚构预期）。

---

## 4. 测试总结（Test Summary）

| 指标 | 数值 |
|------|------|
| 运行用例数（宿主机） | 11 / 11 |
| 总断言数 | 24 |
| 通过断言数 | 24 |
| 失败断言数 | 0 |
| 通过率 | **100%**（24/24） |
| 测试退出码 | 0 |
| 编译警告数 | 0 |
| 静态分析（动态内存） | 零调用（3 处注释引用除外），无 stdlib.h |

### 功能域覆盖

| 功能域 | 覆盖用例 | 状态 |
|--------|----------|------|
| LA 门控肯定侧（有效∧一致→输出） | TC01, TC08, TC09, TC11 | ✅ |
| LA 门控否定侧（有效∧不一致→抑制；无效→抑制） | TC02, TC03, TC10, TC11 | ✅ |
| LB 门控肯定侧（有效∧一致→输出） | TC04, TC08, TC11 | ✅ |
| LB 门控否定侧（有效∧不一致→抑制） | TC05, TC10 | ✅ |
| LC 单判据肯定侧（一致→输出，无有效性检查） | TC06, TC08, TC09, TC11 | ✅ |
| LC 单判据否定侧（不一致→抑制） | TC07, TC10 | ✅ |
| 三通道独立评估（LLR-COM-002，零耦合） | TC08, TC09, TC11 | ✅ |
| 外部数据未就绪（LLR-AMB-11 最小处理路径） | TC10 | ✅（行为记录，语义不判定） |

---

## 5. 测试规程覆盖追溯（Test Procedure Coverage Trace）

DA-09 规程文档（`test_procedures.md`，TP-01-001 ~ TP-10-003 共 46 条）中：

- **可执行（静态分析类，本环境已执行）**: **5 条**
  - TP-01-005（无动态内存）、TP-04-005（LA 比较无动态内存）、TP-07-005（LB 比较无动态内存）、TP-09-005（LC 无有效性检查）、TP-09-006（LC 比较无动态内存）——全部 ✅ 通过（见第 2.2 节）。
- **推迟（物理硬件/平台类）**: **41 条**
  - TP-01-001~004、TP-02-001~003、TP-03-001~004、TP-04-001~004、TP-05-001~005、TP-06-001~004、TP-07-001~004、TP-08-001~005、TP-09-001~004、TP-10-001~003。
  - 推迟原因：规程要求目标板/模拟器、JTAG/SWD、UART 串口、逻辑分析仪/示波器、gdb 目标调试、≥1ms 计时器等物理设备与目标环境（Cortex-M4），本宿主执行环境不具备；**推迟≠失败**，见第 6 节。

> 规程文档内部追溯矩阵使用旧版编号（`HLR-1.x`/`LLR-1.x`、A3-1/A3-2/A3-6），与当前基线（`HLR-LA/LB/LC/COM-xxx`、`LLR-LA/LB/LC/COM-xxx`、§6.4 A6-* 目标）不一致——此为 DA-09 文档陈旧性问题，由 DA-10 如实记录，不修改、不代判；test_cases.md 变更记录（v2 完全重写）已确认正确目标映射为 A6-1/A6-2/A6-5。

---

## 6. 推迟项（Deferred Items — 物理硬件/平台）

以下规程依赖物理硬件、目标计算机或专用测量设备，在本宿主执行环境中**推迟**（明确标注为推迟，**不标记为失败**），待目标环境（Cortex-M4 / arm-none-eabi-gcc，或等效板级模拟器 + JTAG/UART/逻辑分析仪）就绪后执行：

| 规程 ID 范围 | 依赖资源 | 推迟原因 |
|-------------|----------|----------|
| TP-01-001~004 | main() 入口/初始化符号、周期计时（≥1ms 计时器、UART/逻辑分析仪时间戳） | 需目标板/模拟器与高精度计时设备 |
| TP-02-001~003 | L-3..L-10 节点时间戳标记、≥8 通道逻辑分析仪 GPIO 波形 | 需目标环境插桩与多通道采集设备 |
| TP-03-001~004 | LA 通道 NULL/超限/合法值注入、`la_valid` 内存监视/串口读取 | 需目标板数据通道注入与观测接口 |
| TP-04-001~004 | LA/EQC 数据对注入、`la_match` 读取 | 需目标板数据通道注入与观测接口 |
| TP-05-001~005 | LA 输出接口数据帧监测（串口抓包/示波器） | 需目标环境输出接口监测设备 |
| TP-06-001~004 | LB 通道注入与 `lb_valid` 读取 | 同 TP-03 系列 |
| TP-07-001~004 | LB/EQC 数据对注入、`lb_match` 读取 | 同 TP-04 系列 |
| TP-08-001~005 | LB 输出接口帧监测 | 同 TP-05 系列 |
| TP-09-001~004 | LC/EQB 数据对注入、`lc_match` 读取 | 同 TP-04 系列 |
| TP-10-001~003 | LC 输出接口帧监测 | 同 TP-05 系列 |

**对 A6-5 的影响**: A6-5（可执行目标代码与目标计算机兼容）要求目标计算机（Cortex-M4 / arm-none-eabi-gcc）上执行验证。本任务在宿主机完成了：编译期约束确认（C11、零动态内存静态分析、固定周期编译期常量 `PROCESS_CYCLE_MS`）、行为级宿主机运行验证（24/24 断言通过）。目标机上代码生成验证（arm-none-eabi-gcc 交叉编译）属于 DA-06 嵌入式编译证据范畴；**目标机运行级兼容性验证推迟**，A6-5 声明为部分满足（见结果 JSON objective_compliance）。

---

## 7. 执行记录

| 项目 | 记录 |
|------|------|
| 执行人 | DA-10 (test-exec) |
| 任务 ID | test_execution-T01 |
| 执行日期 | 2026-08-08 |
| 构建日志 | /tmp/sr1-build.log |
| 测试日志 | /tmp/sr1-test.log |
| 测试产物 | /home/c/workspace/fusion/projects/sr1/build/sr1（+ main.o / sr1.o） |

*本测试结果文档由 DA-10 (test-exec) 按 DO-178C DAL D §6.4 测试执行要求生成；结果分析（通过/失败判定的最终评估）由 DA-11 (test-verify) 负责。*
