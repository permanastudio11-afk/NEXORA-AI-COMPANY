
import unittest

from nexora.agent_config import get_all_agents
from nexora.quality import evaluate_output
from nexora.workflow_engine import validate_dependencies


class TestNexoraCore(unittest.TestCase):

    def test_agents_are_available(self):
        agents = get_all_agents()
        self.assertGreaterEqual(len(agents), 13)

    def test_empty_output_fails_quality_check(self):
        result = evaluate_output(
            agent_key="research",
            output="",
            task="Research market opportunities",
        )
        self.assertFalse(result["passed"])

    def test_valid_tasks_are_ordered(self):
        tasks = [
            {
                "id": "task_2",
                "agent": "content",
                "title": "Create content",
                "depends_on": ["task_1"],
            },
            {
                "id": "task_1",
                "agent": "research",
                "title": "Research market",
                "depends_on": [],
            },
        ]

        ordered = validate_dependencies(tasks)

        self.assertEqual(ordered[0]["id"], "task_1")
        self.assertEqual(ordered[1]["id"], "task_2")

    def test_circular_dependency_is_rejected(self):
        tasks = [
            {
                "id": "task_1",
                "agent": "research",
                "title": "Research",
                "depends_on": ["task_2"],
            },
            {
                "id": "task_2",
                "agent": "content",
                "title": "Create content",
                "depends_on": ["task_1"],
            },
        ]

        with self.assertRaises(ValueError):
            validate_dependencies(tasks)

    def test_unknown_dependency_is_rejected(self):
        tasks = [
            {
                "id": "task_1",
                "agent": "research",
                "title": "Research",
                "depends_on": ["missing_task"],
            },
        ]

        with self.assertRaises(ValueError):
            validate_dependencies(tasks)


if __name__ == "__main__":
    unittest.main()
