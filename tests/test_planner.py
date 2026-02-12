import unittest
from unittest.mock import patch, MagicMock
from mathpilot.planner.core import generate_plan
from mathpilot.planner.models import ImplementationPlan, WorkflowStep, StepType
from mathpilot.parser.models import ExtractedAlgorithm, AlgorithmStep

class TestPlanner(unittest.TestCase):
    @patch('mathpilot.planner.core.call_gemini')
    def test_generate_plan_success(self, mock_gemini):
        # Setup input
        algo = ExtractedAlgorithm(
            name="Algo1",
            summary="Summary",
            problem_addressed="Problem",
            inputs=["x"],
            outputs=["y"],
            steps=[AlgorithmStep(number=1, description="Step 1")]
        )
        
        # Setup output
        expected_plan = ImplementationPlan(
            paper_title="Test Paper",
            algorithm_name="Algo1",
            summary="Plan Summary",
            steps=[
                WorkflowStep(
                    step_id="step_01",
                    title="Setup",
                    description="Setup env",
                    step_type=StepType.SETUP,
                    code_prompt="import things"
                )
            ]
        )
        mock_gemini.return_value = expected_plan
        
        # Execute
        result = generate_plan("Test Paper", algo)
        
        # Verify
        self.assertEqual(result.algorithm_name, "Algo1")
        self.assertEqual(len(result.steps), 1)
        self.assertEqual(result.steps[0].step_id, "step_01")
        mock_gemini.assert_called_once()

    @patch('mathpilot.planner.core.call_gemini')
    def test_generate_plan_failure(self, mock_gemini):
        # Setup failure
        algo = ExtractedAlgorithm(
            name="Algo1",
            summary="Summary",
            problem_addressed="Problem",
            inputs=["x"],
            outputs=["y"],
            steps=[]
        )
        mock_gemini.side_effect = Exception("LLM Error")
        
        # Execute & Verify
        # Execute & Verify
        with self.assertRaises(Exception): 
             generate_plan("Test Paper", algo)

if __name__ == '__main__':
    unittest.main()
