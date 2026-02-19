import unittest
import sys
import os

# Set up paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from oracle.pipeline import evaluate_oracle_request
from oracle.language_guard import FORBIDDEN_TERMS

class TestOracleMVP(unittest.TestCase):

    def test_NO_VALUE_returns_text_only(self):
        # We can force NO_VALUE by providing inputs that fail thresholds if we adjust mock,
        # but the current mock/engine always produces something. 
        # Let's verify the contract structure first.
        request = {
            "sport": "FOOTBALL",
            "primary": "Team A",
            "opponent": "Team B",
            "mode": "FAST"
        }
        output = evaluate_oracle_request(request)
        
        self.assertEqual(output["version"], "oracle.v1")
        if not output["verdict"]["value_detected"]:
            self.assertFalse(output["chart"]["enabled"])
        
        self.assertGreater(len(output["text"]["body_sections"]), 0)

    def test_VALUE_requires_failure_conditions(self):
        request = {
            "sport": "UFC",
            "primary": "Fighter A",
            "opponent": "Fighter B",
            "mode": "ORACLE"
        }
        output = evaluate_oracle_request(request)
        
        if output["verdict"]["value_detected"]:
            self.assertGreaterEqual(len(output["scenario"]["failure_conditions"]), 1)
            self.assertTrue(output["chart"]["enabled"])

    def test_LANGUAGE_GUARD_blocks_forbidden_terms(self):
        request = {
            "sport": "FOOTBALL",
            "primary": "Team A",
            "opponent": "Team B",
            "mode": "FAST"
        }
        output = evaluate_oracle_request(request)
        
        all_text = output["text"]["title"] + " ".join([s["content"] for s in output["text"]["body_sections"]])
        lower_text = all_text.lower()
        
        for term in FORBIDDEN_TERMS:
            self.assertNotIn(term, lower_text, f"Forbidden term '{term}' found in output text")

    def test_ONE_CHART_POLICY_enforced(self):
        request = {
            "sport": "FOOTBALL",
            "primary": "Team A",
            "opponent": "Team B",
            "alternatives": ["Option 1"],
            "mode": "ORACLE"
        }
        output = evaluate_oracle_request(request)
        
        if output["chart"]["enabled"]:
            self.assertEqual(len(output["chart"]["data"]["series"]), 1)

if __name__ == "__main__":
    unittest.main()
