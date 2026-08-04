import json

from django.test import SimpleTestCase

from account.ai.llm.response import to_api_dict


class AgentFormatTests(SimpleTestCase):
    def test_record_from_create_bill_steps(self):
        obs = json.dumps(
            {
                "success": True,
                "data": {
                    "id": 42,
                    "type": "expense",
                    "category": "餐饮",
                    "amount": 25.0,
                    "icon": "food-o",
                    "remark": "午饭",
                    "date": "2026-08-05",
                },
                "message": "账单已创建",
            },
            ensure_ascii=False,
        )
        result = to_api_dict(
            {
                "output": "好哒，午饭25元记下啦～",
                "intermediate_steps": [
                    ({"name": "create_bill", "id": "1", "args": {}}, obs)
                ],
            }
        )
        self.assertEqual(result["money"], 25.0)
        self.assertEqual(result["category"], "餐饮")
        self.assertEqual(result["record_id"], 42)
        self.assertIn("25", result["reply"])

    def test_chat_when_no_record(self):
        result = to_api_dict({"output": "在呢～", "intermediate_steps": []})
        self.assertEqual(result["money"], 0.0)
        self.assertEqual(result["reply"], "在呢～")
