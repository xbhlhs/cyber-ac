#!/usr/bin/env python3
"""PLA L1-L3 orchestrator for sr_to_hlr on project sr1 at DAL D.

Topological order (serial):
  Phase 1 -> DA-01 req-analysis (verify/update analysis)
  Phase 2 -> DA-02 req-decomp (SR->HLR decomposition)
  Phase 3 -> DA-12 trace-maint (build trace matrix)

Each DA is spawned as an independent hermes chat -q process.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

WORKDIR = Path("/home/c/workspace/fusion")
PROJECT_ID = "sr1"
PROJECT_DIR = WORKDIR / "projects" / PROJECT_ID
QUEUE_BASE = PROJECT_DIR / ".pla" / "queue"
OUTBOX = QUEUE_BASE / "outbox"
INBOX = QUEUE_BASE / "inbox"

# Model/provider config
DA_MODELS = {
    "req-analysis":    {"provider": "deepseek", "model": "deepseek-v4-pro"},
    "req-decomp":      {"provider": "deepseek", "model": "deepseek-v4-pro"},
    "trace-maint":     {"provider": "deepseek", "model": "deepseek-v4-flash"},
}

# Task definitions (topological DAG)
TASKS = [
    {
        "task_id": "T01",
        "da_name": "req-analysis",
        "da_desc": "验证需求分析",
        "description": ("对SR需求进行分析并识别歧义，"
                        "将已解决的AMB标注为RESOLVED。"),
        "inputs": ["projects/sr1/requirements/sr.md"],
        "outputs": ["projects/sr1/evidence/req_analysis.md"],
    },
    {
        "task_id": "T02",
        "da_name": "req-decomp",
        "da_desc": "需求分解（SR→HLR）",
        "description": ("从SR和已验证的需求分析中，将系统需求逐层分解为高层需求(HLR)。"
                        "DAL D，3个HLR验证目标。"
                        "已解决AMB作为SR固有属性，使用合理默认值在HLR中体现。"
                        "不跨层生成LLR。"),
        "inputs": [
            "projects/sr1/requirements/sr.md",
            "projects/sr1/evidence/req_analysis.md",
        ],
        "outputs": ["projects/sr1/requirements/hlr.md"],
    },
    {
        "task_id": "T03",
        "da_name": "trace-maint",
        "da_desc": "构建追溯矩阵（SR→HLR）",
        "description": ("从已产出的SR和HLR制品中，构建前向追溯表（SR→HLR）、"
                        "后向追溯表（HLR→SR），以及覆盖完整性评估。"
                        "只维护关系，不创造新内容。"),
        "inputs": [
            "projects/sr1/requirements/sr.md",
            "projects/sr1/requirements/hlr.md",
        ],
        "outputs": ["projects/sr1/evidence/trace_matrix.md"],
    },
]

DOBJ = [
    {"id": "A3-1", "desc": "每个HLR必须是无二义的、一致的、完整的、可实现的"},
    {"id": "A3-2", "desc": "每个HLR必须可直接或间接追溯到SR"},
    {"id": "A3-6", "desc": "HLR必须以结构化、一致的方式表达"},
]


def ensure_dirs():
    """Ensure queue directory structure exists."""
    for ta in TASKS:
        (OUTBOX / ta["da_name"]).mkdir(parents=True, exist_ok=True)
        (INBOX / ta["da_name"]).mkdir(parents=True, exist_ok=True)


def make_context(task):
    """Build a TaskContext-like dict matching orchestrator.py schema."""
    obj_strs = []
    for o in DOBJ:
        obj_strs.append(f"- {o['id']}: {o['desc']}")
    return {
        "task_id": task["task_id"],
        "task_name": task["da_desc"],
        "da_name": task["da_name"],
        "activity_type": "sr_to_hlr",
        "description": task["description"],
        "inputs": task["inputs"],
        "expected_outputs": task["outputs"],
        "constraints": {
            "dal_level": "D",
            "applicable_objectives": DOBJ,
            "coding_constraints": {
                "language": "C",
                "standard": "C11",
                "compiler": "GCC",
                "no_dynamic_memory": True,
            },
        },
        "dal_level": "D",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "dag_version": 1,
    }


def enqueue(task):
    """Write task context to outbox. Returns filepath."""
    ctx = make_context(task)
    qfile = OUTBOX / task["da_name"] / f"task_{task['task_id']}.json"
    qfile.write_text(
        json.dumps(ctx, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(qfile)


def spawn_da(da_name, task_id, goal_text):
    """Spawn an independent hermes chat -q process for the DA."""
    mc = DA_MODELS[da_name]
    # Escape single quotes for shell
    escaped = goal_text.replace("'", "'\\''")
    cmd = (
        f"hermes chat -q '{escaped}' "
        f"--provider {mc['provider']} --model {mc['model']} "
        f"-s fusion-development"
    )
    print("")
    print("=" * 72)
    print(f"[SPAWN] {da_name}/{task_id}")
    print(f"  provider={mc['provider']}  model={mc['model']}")
    if len(cmd) > 200:
        print(f"  cmd   : {cmd[:200]}...")
    else:
        print(f"  cmd   : {cmd}")

    result = subprocess.run(
        cmd,
        shell=True,
        cwd=str(WORKDIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=900,
    )
    return result


def collect_result(da_name, task_id):
    """Read result from inbox queue file."""
    rfile = INBOX / da_name / f"result_{task_id}.json"
    if not rfile.exists():
        print(f"  No result file at {rfile}")
        return None
    try:
        data = json.loads(rfile.read_text(encoding="utf-8"))
        print(f"  Result collected: status={data.get('status', '?')}")
        return data
    except json.JSONDecodeError as e:
        print(f"  Invalid JSON in result: {e}")
        return None


def check_artifacts_exists(output_paths):
    """Verify each expected artifact exists on disk."""
    ok = True
    for p in output_paths:
        abspath = PROJECT_DIR / p
        if not abspath.exists():
            print(f"  MISSING: {abspath}")
            ok = False
        else:
            sz = abspath.stat().st_size
            print(f"  Artifact: {abspath} ({sz:,d} bytes)")
    return ok


def build_da_goal(task):
    """Build the goal text injected into 'hermes chat -q' for this DA."""
    obj_lines = []
    for o in DOBJ:
        obj_lines.append(f"- {o['id']}: {o['desc']}")
    obj_section = "\n".join(obj_lines)
    inp_lines = []
    for ip in task["inputs"]:
        inp_lines.append(f"- {ip}")
    input_list = "\n".join(inp_lines)
    out_list = ", ".join(task["outputs"])

    queue_base = f"projects/{PROJECT_ID}/.pla/queue"
    lines = [
        f"You are {task['da_name']} (DA-{task['task_id'][1:]}, {task['da_desc']}).",
        "Load /home/c/.hermes/skills/fusion-development/SKILL.md for conventions.",
        "",
        f"GOAL: {task['description']}",
        "",
        "Available tools: read_file, write_file, terminal, search_files",
        "",
        "## Input Files",
        input_list,
        "",
        "## Required Output",
        f"- {out_list}",
        f"Result JSON → {queue_base}/inbox/{task['da_name']}/result_{task['task_id']}.json",
        "",
        "## Result Format",
        "{"
        '"task_id":"{tid}", '
        '"da_name":"{daname}", '
        '"status":"completed", '
        '"artifacts":["...output paths..."], '
        '"output":{"reasoning":"..."}, '
        '"unresolved":[], '
        '"objective_compliance":[{"objective_id":"...", "status":"compliant", "evidence":"..."}], '
        '"error":""'
        "}".format(tid=task["task_id"], daname=task["da_name"]),
        "",
        "## DO-178C (DAL D)",
        "",
        obj_section,
        "",
        "Declare compliance in objective_compliance array.",
        "",
        "IMPORTANT CONTRACTS:",
        "- DA-01: Only analyze SR. Flag ambiguities. Never decompose.",
        "- DA-02: Decompose SR→HLR only. Trace every HLR back to SR source clause. Use reasonable defaults for already-resolved AMBs. NEVER generate LLR content.",
        "- DA-12: Build trace RELATIONSHIPS ONLY from existing artifacts. Do NOT generate HLR/LLR content.",
        "",
        "START by reading the input files. Work diligently. End by writing the output and result JSON.",
    ]
    return "\n".join(lines).strip()


def run_phase(phase_num, task):
    """Full lifecycle for one DA phase: enqueue -> spawn -> wait -> collect -> verify."""
    dash = "#" * 72
    eq = "=" * 72
    print("")
    print(dash)
    print(f"# PHASE {phase_num}: DA-0{task['task_id'][1:]} {task['da_name']} ({task['da_desc']})")
    print(dash)

    # Step 1: Enqueue task context
    qfile = enqueue(task)
    print(f"Enqueued context → {qfile}")

    # Step 2: Spawn DA as independent hermes process
    goal = build_da_goal(task)
    spawn_start = time.time()
    sp = spawn_da(task["da_name"], task["task_id"], goal)
    wall_time = time.time() - spawn_start
    print("")
    print(
        f"Process exit_code={sp.returncode}"
        f"  wall_time={wall_time:.1f}s"
        f"  stdout_len={len(sp.stdout)}"
    )

    # Step 3: Collect result from inbox
    result = collect_result(task["da_name"], task["task_id"])

    # Step 4: Verify expected artifacts exist on disk
    art_ok = check_artifacts_exists(task["outputs"])

    # Assess phase outcome
    success = sp.returncode == 0 and art_ok
    status = "SUCCESS" if success else "FAILURE"
    print("")
    print(eq)
    print(f"# PHASE {phase_num} RESULT: {status}")
    print(eq)
    if result:
        print(f"Status field: {result.get('status', 'N/A')}")
        unresolved = result.get("unresolved", [])
        print(f"Unresolved: {unresolved}")
        comp = result.get("objective_compliance", [])
        print(f"Objective compliance entries: {len(comp)}")
        err = result.get("error", "")
        if err:
            print(f"Error: {err}")
    print("")
    return success


def main():
    hdr = f"PLA L1->L2->L3 Orchestrator — sr_to_hlr | project={PROJECT_ID} | DAL=D"
    print(hdr)
    print(f"Workdir: {WORKDIR}")

    ensure_dirs()

    # Serial topological dispatch
    results = {}
    for i, task in enumerate(TASKS, 1):
        ok = run_phase(i, task)
        results[task["task_id"]] = ok
        if not ok:
            print("\nPipeline halted due to phase failure.")
            break

    # Final summary
    sep = "@" * 72
    all_ok = all(results.values())
    print("")
    print(sep)
    print("@ PIPELINE SUMMARY")
    print(sep)
    for tid, ok in results.items():
        t = next(x for x in TASKS if x["task_id"] == tid)
        icon = "+" if ok else "-"
        print(f"  [{tid}] {icon} {t['da_name']:20s} {t['da_desc']}")
    overall = "ALL SUCCESS" if all_ok else "SOME FAILURES"
    print(f"\nOverall: {overall}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
