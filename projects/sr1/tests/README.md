# SR-1 测试用例

## 测试清单

| 编号 | 场景 | 输入状态 | 期望输出 | 对应需求 |
|------|------|---------|---------|---------|
| TC01 | 三设备全部 VALID | VALID×3 | 中值, AVAILABLE | LLR-1.3.2 |
| TC02 | 两个 VALID + 一个 INVALID | VALID×2, INVALID×1 | 平均值, AVAILABLE | LLR-1.3.1 |
| TC03 | 一个 VALID + 两个 INVALID | VALID×1, INVALID×2 | 默认值, UNAVAILABLE | LLR-1.2.2 |
| TC04 | 两个 VALID + 一个 DEGRADED | VALID×2, DEGRADED×1 | 平均值, AVAILABLE | LLR-1.4.1 |
| TC05 | 一个 VALID + 一个 DEGRADED + 一个 INVALID | VALID×1, DEGRADED×1, INVALID×1 | 默认值, DEGRADED | LLR-1.4.1 |
| TC06 | 输入超出范围（钳位） | VALID×3, 越界值 | 钳位后中值, AVAILABLE | LLR-1.1.1 |
| TC07 | 全部 DEGRADED | DEGRADED×3 | 默认值, UNAVAILABLE | LLR-1.4.1 |

## 测试实现

测试在主程序 `sr1/src/main.c` 中以自测试方式实现（main 函数直接调用 sr1_process 并输出结果）。

## 运行

```bash
make sr1
```
