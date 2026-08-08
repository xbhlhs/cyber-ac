# 融合开发体系 — 构建系统
# 双编译器: 本地GCC(快速开发) + arm-none-eabi-gcc(机载验证)
#
# make sr1          — 本地GCC编译+运行 (开发迭代)
# make sr1-embedded — arm-none-eabi交叉编译 (机载目标验证)
# make sr1-all      — 两个目标都编译

# ============================================================
# 编译器配置
# ============================================================

# 本地编译器 (ARM64 host, 快速开发)
HOST_CC      = gcc
HOST_CFLAGS  = -Wall -Wextra -std=c11 -pedantic -O2
HOST_LDFLAGS =

# 嵌入式交叉编译器 (ARM Cortex-M4, 机载目标)
ARM_GCC      = $(HOME)/.local/arm-gnu-toolchain/bin/arm-none-eabi-gcc
ARM_CFLAGS   = -mcpu=cortex-m4 -mthumb -std=c11 -ffreestanding \
               -Wall -Wextra -fno-common -O2
ARM_LDFLAGS  = -nostdlib -T /dev/null  # 仅验证编译，不链接

# ============================================================
# 源文件
# ============================================================

SR1_SRC_DIR   = projects/sr1/src
SR1_BUILD_DIR = projects/sr1/build
SR1_EMBED_DIR = projects/sr1/build/embedded

SR1_SRCS      = $(wildcard $(SR1_SRC_DIR)/*.c)
SR1_HOST_OBJS = $(SR1_SRCS:$(SR1_SRC_DIR)/%.c=$(SR1_BUILD_DIR)/%.o)
SR1_EMBED_OBJS= $(SR1_SRCS:$(SR1_SRC_DIR)/%.c=$(SR1_EMBED_DIR)/%.o)

SR1_HOST_BIN  = $(SR1_BUILD_DIR)/sr1

# ============================================================
# 本地目标 (开发迭代)
# ============================================================

.PHONY: all sr1 sr1-build sr1-test sr1-clean

all: sr1

sr1: sr1-build sr1-test

sr1-build: $(SR1_HOST_BIN)

$(SR1_BUILD_DIR):
	mkdir -p $(SR1_BUILD_DIR)

$(SR1_BUILD_DIR)/%.o: $(SR1_SRC_DIR)/%.c | $(SR1_BUILD_DIR)
	$(HOST_CC) $(HOST_CFLAGS) -c $< -o $@

$(SR1_HOST_BIN): $(SR1_HOST_OBJS)
	$(HOST_CC) $(HOST_LDFLAGS) $^ -o $@

sr1-test: $(SR1_HOST_BIN)
	./$(SR1_HOST_BIN)

sr1-clean:
	rm -rf $(SR1_BUILD_DIR) $(SR1_EMBED_DIR)

# ============================================================
# 嵌入式目标 (机载验证)
# ============================================================

.PHONY: sr1-embedded sr1-embedded-asm sr1-all

$(SR1_EMBED_DIR):
	mkdir -p $(SR1_EMBED_DIR)

$(SR1_EMBED_DIR)/%.o: $(SR1_SRC_DIR)/%.c | $(SR1_EMBED_DIR)
	@echo "[ARM-EMBED] $< → Cortex-M4 Thumb-2"
	@$(ARM_GCC) $(ARM_CFLAGS) -c $< -o $@
	@echo "  ✓ $(notdir $@)"

sr1-embedded: $(SR1_EMBED_DIR) $(SR1_EMBED_OBJS)
	@echo ""
	@echo "=== 嵌入式编译验证通过 ==="
	@echo "目标: ARM Cortex-M4 / Thumb-2"
	@echo "编译器: arm-none-eabi-gcc 13.3.1"
	@echo "标准: C11 + freestanding"
	@echo "文件: $(notdir $(SR1_EMBED_OBJS))"
	@echo ""

# 生成汇编代码供检查
sr1-embedded-asm: $(SR1_EMBED_DIR)
	@for src in $(SR1_SRCS); do \
		base=$$(basename $$src .c); \
		echo "=== $$base.s (Cortex-M4 Thumb-2) ==="; \
		$(ARM_GCC) $(ARM_CFLAGS) -S $$src -o $(SR1_EMBED_DIR)/$$base.s; \
		echo "  → $(SR1_EMBED_DIR)/$$base.s"; \
	done

# 两个目标都编译
sr1-all: sr1-build sr1-embedded
	@echo ""
	@echo "=== 双编译器验证完成 ==="
	@echo "Host:   $(SR1_HOST_BIN)"
	@echo "Embedded: $(SR1_EMBED_DIR)/*.o (Cortex-M4)"

# ============================================================
# 清理
# ============================================================

clean: sr1-clean
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
