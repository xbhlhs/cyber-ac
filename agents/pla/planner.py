"""
PLA L2 决策层 — 动态路径选择 + TaskPlan生成 + 评估

融合策略 = 活动类型→路径静态映射 + DAL自适应动态路由
"""

import re
from pathlib import Path
import yaml

from runtime.task_plan import TaskPlan, TaskItem, CheckItem, HumanGate
from agents.pla.perception import ActivityContext


class Planner:
    """L2决策: 基于活动类型+DAL+制品状态动态选择路径和产出物"""

    # 研发活动类型→路径
    ACTIVITY_PATH = {
        "sr_analysis":    "llm_priority",      # 知识理解类 → LLM优先
        "sr_to_hlr":      "model_llm_fusion",  # HLR建模 → 融合
        "hlr_to_llr":     "model_llm_fusion",  # LLR设计 → 融合
        "architecture_model": "model_priority", # 架构建模 → 模型优先
        "detailed_design": "model_llm_fusion",  # 详细设计 → 融合
        "code_generation": "model_driven",      # 自动代码生成 → 模型驱动
        "code_refinement": "llm_priority",      # 代码完善 → LLM优先
        "test_case_gen":   "model_llm_fusion", # 测试用例 → 融合
        "test_proc_gen":   "llm_priority",     # 测试规程 → LLM优先
        "test_execution":  "model_driven",      # 测试执行 → 模型驱动
        "verification":    "model_llm_fusion", # 验证分析 → 融合
        "review_prep":     "model_llm_fusion", # 评审材料 → 融合
        "evidence_pack":   "model_llm_fusion", # 适航证据 → 融合
    }

    def __init__(self, dal_level: str = "D", project_id: str = None):
        self.dal_level = dal_level
        self.project_id = project_id
        self._project_prefix = f"projects/{project_id}/" if project_id else ""
        self._dag_version = 1
        self._do178c = self._load_do178c()

    def _load_do178c(self) -> dict:
        project_id = self.project_id or "sr1"
        p = Path(f"projects/{project_id}/.pla/environment/constraints/do178c.yaml")
        if p.exists():
            with open(str(p)) as f:
                return yaml.safe_load(f)
        return {}

    # ============================================================
    # L2: 路径选择
    # ============================================================

    def select_path(self, activity_type: str, context: ActivityContext) -> str:
        """
        路径选择 = f(活动类型, DAL, 公司规范, 项目约束)

        优先级: 项目约束 > 公司规范 > DAL推荐
        """
        dal = context.dal_level
        company = context.constraints.get("company", {})
        project_path = context.constraints.get("project_path", {})

        # Step 1: DAL默认推荐
        path = self.ACTIVITY_PATH.get(activity_type, "model_llm_fusion")

        # Step 2: DAL自适应
        if dal in ["A", "B"] and path == "llm_priority":
            path = "model_llm_fusion"

        # Step 3: 公司规范覆盖
        company_model = company.get("model_policy", "model_optional")
        if company_model == "model_required":
            if path == "llm_priority":
                path = "model_llm_fusion"
        elif company_model == "model_prohibited":
            if path in ["model_driven", "model_priority"]:
                path = "llm_priority"

        # Step 4: 项目约束覆盖 (最高优先级)
        proj_model = project_path.get("model_policy", "as_dal")
        if proj_model == "required":
            if path == "llm_priority":
                path = "model_llm_fusion"
        elif proj_model == "text_only":
            if path in ["model_driven", "model_priority"]:
                path = "llm_priority"

        return path

    def decide_mixed_mode(self, activity_type: str, context: ActivityContext) -> str:
        """决定表达方式: text_only | model_only | text_model_mixed"""
        dal = context.dal_level
        company = context.constraints.get("company", {})
        project_path = context.constraints.get("project_path", {})

        # 项目显式指定 mixed_mode
        proj_mix = project_path.get("mixed_mode", "as_dal")
        if proj_mix != "as_dal":
            return proj_mix

        # 项目model_policy影响mixed_mode
        proj_model = project_path.get("model_policy", "as_dal")
        if proj_model == "required":
            return "text_model_mixed"
        if proj_model == "text_only":
            return "text_only"

        # 公司规范
        company_model = company.get("model_policy", "model_optional")
        if company_model == "model_required":
            return "text_model_mixed"
        if company_model == "model_prohibited":
            return "text_only"

        # DAL默认
        return "text_only" if dal in ["D", "E"] else "text_model_mixed"

    def decide_skip_detailed_design(self, context: ActivityContext) -> bool:
        """决定是否跳过详细设计, LLR直接生成代码"""
        dal = context.dal_level
        project_path = context.constraints.get("project_path", {})

        proj_skip = project_path.get("skip_detailed_design", "as_dal")
        if proj_skip == True:
            return True
        if proj_skip == False:
            return False
        # as_dal: DAL D/E可跳过
        return dal in ["D", "E"]

    def decide_artifacts(self, activity_type: str, path: str, context: ActivityContext) -> dict:
        """
        L2动态决定产出物形式和DA能力。

        综合: 活动类型 + 开发路径 + 公司规范 + 项目约束 + DAL
        """
        dal = context.dal_level
        mixed_mode = self.decide_mixed_mode(activity_type, context)
        skip_dd = self.decide_skip_detailed_design(context)
        requires_model = mixed_mode in ["text_model_mixed", "model_only"]

        # 默认产出物策略
        strategy = {
            "sr_analysis": {
                "das": ["req-analysis"],
                "artifacts": ["evidence/req_analysis.md"],
            },
            "sr_to_hlr": {
                "das": ["req-analysis", "req-decomp", "trace-maint"],
                "artifacts": ["evidence/req_analysis.md", "requirements/hlr.md", "evidence/trace_matrix.md"],
                "extra_artifacts": ["models/sr1_requirements.sysml"] if requires_model else [],
            },
            "hlr_to_llr": {
                "das": ["req-decomp", "trace-maint"],
                "artifacts": ["requirements/llr.md", "evidence/trace_matrix.md"],
                "extra_artifacts": ["models/sr1_architecture.sysml"] if requires_model else [],
                "skip_to_code": skip_dd,
            },
            # 模型活动: 架构用SysML, 详细设计用UML
            "architecture_model": {
                "das": ["model-build", "trace-maint"],
                "artifacts": ["models/sr1.sysml", "evidence/trace_matrix.md"],
            },
            "detailed_design": {
                "das": ["model-build", "trace-maint"],
                "artifacts": ["models/sr1.puml", "evidence/trace_matrix.md"],
            },
            # 代码: 可跳过详细设计直接从LLR生成
            "code_generation": {
                "das": ["code-gen", "code-check", "trace-maint"],
                "artifacts": ["src/sr1.c", "src/sr1.h", "evidence/code_check.md", "evidence/trace_matrix.md"],
                "skip_detailed_design": True if (dal in ["D", "E"]) else False,
            },
            # 测试
            "test_case_gen": {
                "das": ["test-scenario", "test-case-gen", "test-proc-gen", "trace-maint"],
                "artifacts": ["evidence/test_scenarios.md", "tests/test_cases.md", "tests/test_procedures.md", "evidence/trace_matrix.md"],
            },
            "test_execution": {
                "das": ["test-exec"],
                "artifacts": ["evidence/test_results.md"],
            },
            "verification": {
                "das": ["verify-analysis", "trace-maint"],
                "artifacts": ["evidence/verification_analysis.md", "evidence/trace_matrix.md"],
            },
            "review_prep": {
                "das": ["review-materials"],
                "artifacts": ["evidence/review_materials.md"],
            },
            "evidence_pack": {
                "das": ["airworth-evidence"],
                "artifacts": ["evidence/evidence_index.md"],
            },
        }

        s = strategy.get(activity_type, {"das": [], "artifacts": []})

        # SCADE: 如果可用且DAL≥B, 可走SCADE路径(本验证未集成)
        # s["use_scade"] = False

        return s if isinstance(s, dict) else {"das": [], "artifacts": []}

    # ============================================================
    # L2: plan / replan
    # ============================================================

    def plan(self, context: ActivityContext, activity_type: str) -> TaskPlan:
        """L2: 动态生成TaskPlan"""
        path = self.select_path(activity_type, context)
        decision = self.decide_artifacts(activity_type, path, context)

        plan = TaskPlan(
            activity_id=activity_type, activity_type=activity_type,
            dal_level=context.dal_level, development_path=path, version=self._dag_version,
        )

        mixed_mode = self.decide_mixed_mode(activity_type, context)
        skip_dd = self.decide_skip_detailed_design(context)

        plan.constraints["path_decision"] = {
            "activity_type": activity_type,
            "base_path": self.ACTIVITY_PATH.get(activity_type),
            "dal_adapted_path": path,
            "mixed_mode": mixed_mode,
            "skip_detailed_design": skip_dd,
            "company_model_policy": context.constraints.get("company", {}).get("model_policy", "?") if context.constraints.get("company") else "?",
            "project_model_policy": context.constraints.get("project_path", {}).get("model_policy", "as_dal"),
        }

        # 生成TaskItem
        da_names = decision.get("das", [])
        artifacts = decision.get("artifacts", []) + decision.get("extra_artifacts", [])

        # 如果需要模型混合表达, 插入model-build DA
        if mixed_mode in ["text_model_mixed", "model_only"]:
            da_names = da_names[:1] + ["model-build"] + da_names[1:]

        prev_id = None
        for i, da_name in enumerate(da_names):
            tid = f"{activity_type}-T{i+1:02d}"
            # Prepend project path to expected outputs for correct resolution
            raw_outputs = [artifacts[i]] if i < len(artifacts) else []
            resolved_outputs = [self._project_prefix + o for o in raw_outputs]
            task = TaskItem(
                id=tid,
                name=self._da_desc(da_name),
                da_name=da_name,
                description=self._da_desc(da_name), activity_type=activity_type,
                depends_on=[prev_id] if prev_id else [],
                inputs={"upstream": activity_type} if i == 0 else {},
                expected_outputs=resolved_outputs,
            )
            plan.tasks.append(task)
            prev_id = tid

        plan.checklist = self._build_checklist(activity_type)
        plan.human_gates = self._identify_gates(plan)
        self._dag_version += 1
        return plan

    def replan(self, context: ActivityContext, prev_plan: TaskPlan, assessment: dict) -> TaskPlan:
        plan = self.plan(context, prev_plan.activity_type)
        plan.constraints["replan_reason"] = {
            "previous_version": prev_plan.version,
            "issues": assessment.get("issues", []),
            "unresolved_count": len(assessment.get("unresolved", [])),
        }
        return plan

    # ============================================================
    # L1: assess
    # ============================================================

    def assess(self, task_item: TaskItem, result, activity_type: str) -> dict:
        issues = []
        unresolved = []
        if not result or getattr(result, 'status', '') == 'failed':
            return {"status":"failed","issues":["DA执行失败或结果不可读"],"unresolved":[],"compliance":{"summary":"N/A","checks":[]},"action":"replan"}
        for out in task_item.expected_outputs:
            p = Path(out) if Path(out).is_absolute() else Path.cwd() / out
            if not p.exists():
                issues.append(f"产物缺失: {p.name}")
        if hasattr(result, 'unresolved') and isinstance(result.unresolved, list):
            unresolved.extend(result.unresolved)
        output_data = getattr(result, 'output', None)
        if isinstance(output_data, dict):
            for key in ['ambiguities', 'unresolved', 'open_questions']:
                found = output_data.get(key, [])
                if isinstance(found, list):
                    for item in found:
                        if isinstance(item, dict):
                            desc = item.get('description') or item.get('issue') or ''
                            unresolved.append(f"{item.get('id','')}: {desc}")
                        elif isinstance(item, str):
                            unresolved.append(item)
        if not unresolved:
            unresolved = self._scan_artifacts(result)
        truly_unresolved = [u for u in unresolved if not (isinstance(u,str) and u.startswith("RESOLVED"))]
        objectives = self._get_objectives(activity_type)
        obj_comp = getattr(result, 'objective_compliance', []) or []
        compliance = {"summary": f"{len(obj_comp)}/{len(objectives)} declared", "checks": []}
        if truly_unresolved:
            return {"status":"human_review_required","issues":issues,"unresolved":truly_unresolved,"compliance":compliance,"action":"human_gate"}
        if issues:
            return {"status":"deviation","issues":issues,"unresolved":unresolved,"compliance":compliance,"action":"replan"}
        return {"status":"pass","issues":[],"unresolved":unresolved,"compliance":compliance,"action":"continue"}

    def _get_objectives(self, activity_type: str) -> list:
        tables = {"sr_to_hlr":"hlr_verification","hlr_to_llr":"llr_verification","code_generation":"coding_verification"}
        table = tables.get(activity_type, "hlr_verification")
        return [o for o in self._do178c.get(table, []) if self.dal_level in o.get("applicable_DAL",[])]

    def _scan_artifacts(self, result) -> list:
        unresolved = []
        patterns = [(r'(AMB-\d+)|(FA-\d+)','歧义'),(r'LQ-\d+|TD-\d+','待决策'),(r'UC-\d+','未收敛'),(r'待确认|待决策|待人工','待处理')]
        for ap in getattr(result, 'artifacts', []) or []:
            p = Path(ap) if Path(ap).is_absolute() else Path.cwd() / ap
            if not p.exists(): continue
            try:
                content = p.read_text()
                for pat, cat in patterns:
                    for m in re.findall(pat, content)[:5]:
                        item = str(m[0] if isinstance(m,tuple) else m)
                        idx = content.find(item)
                        ctx = content[max(0,idx-30):idx+len(item)+50]
                        if 'RESOLVED' not in ctx:
                            unresolved.append(f"{p.name}:{cat}:{item}")
            except: pass
        return unresolved

    def _da_desc(self, da_name: str) -> str:
        return {"req-analysis":"分析需求","req-decomp":"分解需求","model-build":"构建模型","model-check":"检查模型","code-gen":"生成代码","code-check":"检查代码","test-scenario":"识别场景","test-case-gen":"生成用例","test-proc-gen":"生成规程","test-exec":"执行测试","verify-analysis":"验证分析","trace-maint":"追溯维护","review-materials":"整理评审","airworth-evidence":"证据归档"}.get(da_name, da_name)

    def _build_checklist(self, activity_type: str) -> list:
        cl = [CheckItem(id=f"CK-{activity_type}-01",description="所有期望输出文件已生成",category="artifact",check_method="auto",exit_condition="files_exist")]
        for i, obj in enumerate(self._get_objectives(activity_type)):
            cl.append(CheckItem(id=f"CK-{activity_type}-DO-{i+2:02d}",description=obj["desc"],category="do178c",do178c_ref=obj["id"],applicable_dal=[self.dal_level],check_method="auto" if self.dal_level in ["D","E"] else "hybrid",exit_condition=f"objective_{obj['id']}_satisfied"))
        if self.dal_level in ["A","B","C"]:
            cl.append(CheckItem(id=f"CK-{activity_type}-HM-01",description="人工评审确认",category="human",check_method="manual",exit_condition="human_approved"))
        return cl

    def _identify_gates(self, plan: TaskPlan) -> list:
        gates = []
        if self.dal_level in ["A","B"] and plan.tasks:
            gates.append(HumanGate(gate_type="initial_plan",task_id=plan.tasks[0].id,trigger_condition="DAL A/B 必需",authorization="项目技术负责人",timing="before"))
        if self.dal_level in ["A","B","C"] and plan.tasks:
            gates.append(HumanGate(gate_type="verification_confirm",task_id=plan.tasks[-1].id,trigger_condition="阶段输出需人工确认",authorization="质量保证人员",timing="after"))
        return gates
