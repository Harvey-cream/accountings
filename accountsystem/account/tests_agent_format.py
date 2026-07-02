from django.test import SimpleTestCase

from account.utils.response import to_api_dict
from account.utils.schemas import AccountingResult, ToolObservation


class AgentFormatTests(SimpleTestCase):
    def test_record_from_steps(self):
        obs = ToolObservation(
            ok=True,
            kind="record",
            record=AccountingResult(
                type="支出",
                category="餐饮",
                money=25.0,
                remark="午饭",
            ),
        )
        result = to_api_dict(
            {
                "output": "好哒，午饭25元记下啦～",
                "intermediate_steps": [(None, obs.for_agent())],
            }
        )
        self.assertEqual(result["money"], 25.0)
        self.assertEqual(result["category"], "餐饮")
        self.assertIn("25", result["reply"])

    def test_chat_when_no_record(self):
        result = to_api_dict({"output": "在呢～", "intermediate_steps": []})
        self.assertEqual(result["money"], 0.0)
        self.assertEqual(result["reply"], "在呢～")
