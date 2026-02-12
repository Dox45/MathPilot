import unittest
from unittest.mock import patch, MagicMock
from mathpilot.parser.core import parse_paper
from mathpilot.parser.models import ParsedPaper, ExtractedAlgorithm, AlgorithmStep, ParsingError

class TestParser(unittest.TestCase):
    @patch('mathpilot.parser.core.extract_pdf_sections')
    @patch('mathpilot.parser.core.extract_pdf_text')
    @patch('mathpilot.parser.core.call_gemini')
    def test_parse_paper_success(self, mock_gemini, mock_text, mock_sections):
        # Setup mocks
        # Make content > 500 chars to avoid fallback
        long_content = "This is the method section content. " * 20
        mock_sections.return_value = {"method": long_content}
        mock_text.return_value = "" # Not used if sections found
        
        expected_paper = ParsedPaper(
            title="Test Paper",
            algorithms=[
                ExtractedAlgorithm(
                    name="Algo1",
                    summary="Summary",
                    problem_addressed="Problem",
                    inputs=["x"],
                    outputs=["y"],
                    steps=[
                        AlgorithmStep(number=1, description="Step 1")
                    ]
                )
            ]
        )
        mock_gemini.return_value = expected_paper
        
        # Execute
        result = parse_paper("test.pdf", "Test Paper")
        
        # Verify
        self.assertEqual(result.title, "Test Paper")
        self.assertEqual(len(result.algorithms), 1)
        self.assertEqual(result.algorithms[0].name, "Algo1")
        mock_gemini.assert_called_once()
        
    @patch('mathpilot.parser.core.extract_pdf_sections')
    @patch('mathpilot.parser.core.extract_pdf_text')
    @patch('mathpilot.parser.core.call_gemini')
    def test_parse_paper_fallback_to_text(self, mock_gemini, mock_text, mock_sections):
        # Setup mocks: sections empty/short
        mock_sections.return_value = {"method": ""}
        mock_text.return_value = "This is the full text of the paper including methods."
        
        expected_paper = ParsedPaper(
            title="Fallback Paper",
            algorithms=[]
        )
        mock_gemini.return_value = expected_paper
        
        # Execute
        parse_paper("test.pdf", "Fallback Paper")
        
        # Verify text fallback was used
        mock_text.assert_called_once()
        
    @patch('mathpilot.parser.core.extract_pdf_sections')
    @patch('mathpilot.parser.core.extract_pdf_text')
    def test_parse_paper_no_content(self, mock_text, mock_sections):
        # Setup mocks to return nothing
        mock_sections.return_value = {}
        mock_text.return_value = ""
        
        # Execute & Verify
        with self.assertRaises(ParsingError):
            parse_paper("test.pdf", "Empty Paper")

if __name__ == '__main__':
    unittest.main()
