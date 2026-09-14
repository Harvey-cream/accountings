"""确认恢复整链路：run_orchestrator(confirm=...) -> execute_plan -> 业务 runner。

补齐 `execute_plan` / `_to_graph_input` 单点测试之外的接缝：
服务端持久化确认卡回传后，workflow_plan 是否正确回放为计划、
参数与 confirmed_plan 是否原样透传给业务 runner。
"""

from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from account.ai.orchestrator import executor, run_orchestrator


def _task(task_id, task_type, action, goal, task_input, depends_on=None):
    return {
        "id": task_id,
        "type": task_type,
        "action": action,
        "goal": goal,
        "input": task_input,
        "depends_on": depends_on or [],
    }


def _extra(entity, action, payload, workflow_plan, candidates=None):
    """模拟 services.langchain_chat 落库的确认卡 extra_data。"""
    return {
        "entity": entity,
        "action": action,
        "payload": payload,
        "candidates": candidates or [],
        "workflow_plan": workflow_plan,
        "plan_tasks": workflow_plan,
        "resolved": True,
    }


def _confirm(extra):
    return {"confirm": True, "message_id": 1, "confirm_extra": extra}


class ConfirmResumeChainTests(SimpleTestCase):
    def test_budget_preview_resume_passes_params(self):
        plan_tasks = [
            _task(
                "budget_set_budget",
                "budget",
                "set_budget",
                "下月餐饮预算3000",
                {"amount": 3000, "period": "2026-10", "budget_type": "month", "is_total": False, "category": "餐饮"},
            )
        ]
        extra = _extra("budget", "set_budget", plan_tasks[0]["input"], plan_tasks)
        run = Mock(return_value={"output": "预算已调整为3000", "intermediate_steps": []})
        with patch.object(executor, "_RUNNERS", {"budget": run}):
            result = run_orchestrator("确认", None, confirm=_confirm(extra))

        kwargs = run.call_args.kwargs
        self.assertEqual(kwargs["task_action"], "set_budget")
        self.assertEqual(kwargs["task_input"]["amount"], 3000)
        self.assertEqual(kwargs["task_input"]["period"], "2026-10")
        self.assertTrue(kwargs["task_confirmed"])
        self.assertTrue(kwargs["confirm"]["confirmed_plan"])
        self.assertEqual(result["output"], "预算已调整为3000")

    def test_bill_midloop_resume_passes_task_and_confirm(self):
        plan_tasks = [
            _task(
                "bill_update",
                "bill",
                "update",
                "把兼职的账单改成80",
                {"keyword": "兼职", "amount": 80, "bill_id": None},
            )
        ]
        extra = _extra(
            "bill",
            "update",
            {"need_confirm": True, "entity": "bill", "action": "update", "candidates": [{"id": 7, "amount": 60}]},
            plan_tasks,
            candidates=[{"id": 7, "amount": 60}],
        )
        run = Mock(return_value={"output": "已把兼职改成80", "intermediate_steps": []})
        with patch.object(executor, "_RUNNERS", {"bill": run}):
            run_orchestrator("确认", None, confirm=_confirm(extra))

        kwargs = run.call_args.kwargs
        self.assertEqual(kwargs["task_action"], "update")
        self.assertEqual(kwargs["task_input"]["keyword"], "兼职")
        self.assertTrue(kwargs["task_confirmed"])
        # 有确认卡片回传的域必须拿到 confirm，供 Workflow 判定 confirmed 后重定位执行
        self.assertIn("confirm", kwargs)

    def test_bill_create_preview_resume_executes(self):
        plan_tasks = [_task("bill_create", "bill", "create", "记一笔30午饭", {"amount": 30, "category": "午饭"})]
        extra = _extra("bill", "create", plan_tasks[0]["input"], plan_tasks)
        run = Mock(return_value={"output": "记好啦", "intermediate_steps": []})
        with patch.object(executor, "_RUNNERS", {"bill": run}):
            result = run_orchestrator("确认", None, confirm=_confirm(extra))

        self.assertEqual(run.call_args.kwargs["task_action"], "create")
        self.assertEqual(run.call_args.kwargs["task_input"]["amount"], 30)
        self.assertEqual(result["plan_result"]["status"], "success")

    def test_invalid_workflow_plan_fails_gracefully(self):
        # set_budget 缺 amount：回放时应被 schema 拒绝，不抛异常、不执行
        bad = [_task("budget_set_budget", "budget", "set_budget", "预算", {"period": "2026-10", "budget_type": "month"})]
        extra = _extra("budget", "set_budget", bad[0]["input"], bad)
        run = Mock()
        with patch.object(executor, "_RUNNERS", {"budget": run}):
            result = run_orchestrator("确认", None, confirm=_confirm(extra))

        run.assert_not_called()
        self.assertIn("确认信息无效", result["output"])
        self.assertEqual(result["plan_result"]["status"], "failed")

    def test_cancel_short_circuits(self):
        run = Mock()
        with patch.object(executor, "_RUNNERS", {"bill": run}):
            result = run_orchestrator("取消", None, confirm={"confirm": False, "message_id": 1})

        run.assert_not_called()
        self.assertIn("取消", result["output"])


class OrchestratorEntryTests(SimpleTestCase):
    def test_greeting_short_circuits_before_planner(self):
        with patch("account.ai.orchestrator._try_greeting", return_value="嗨，我是福娃鸭～") as greet:
            with patch("account.ai.orchestrator.build_route_plan") as planner:
                result = run_orchestrator("你好", None)

        greet.assert_called_once()
        planner.assert_not_called()
        self.assertEqual(result["output"], "嗨，我是福娃鸭～")

    def test_plan_result_maps_to_plain_text(self):
        from account.ai.llm.response import to_api_dict

        api = to_api_dict(
            {
                "output": "最近共 3 笔账单。",
                "plan_result": {
                    "plan_id": "p",
                    "status": "success",
                    "task_results": [],
                    "summary": "最近共 3 笔账单。",
                    "analysis_view": {},
                    "intermediate_steps": [],
                },
            }
        )
        self.assertEqual(api["reply"], "最近共 3 笔账单。")
        self.assertFalse(api.get("need_confirm"))
