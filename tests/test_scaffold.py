import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_cases import validate
from score import score

class ScaffoldTests(unittest.TestCase):
    def test_fixture_and_gold_integrity(self):
        cases, gold = validate()
        self.assertEqual(set(cases), set(gold))
        self.assertEqual(len(cases), 5)

    def test_empty_predictions_are_not_a_success(self):
        obj = json.loads((ROOT / "examples/empty_predictions.json").read_text())
        result = score(obj)
        self.assertEqual(result["tp"], 0)
        self.assertEqual(result["fn"], 3)
        self.assertEqual(result["false_warnings_per_clean_case"], 0)

    def test_invalid_evidence_pointer_rejected(self):
        obj = json.loads((ROOT / "examples/empty_predictions.json").read_text())
        obj["predictions"][0]["findings"] = [{
            "type":"contradiction", "claim":"some discrepancy",
            "action":"Ask human to review", "evidence":["does-not-exist"]
        }]
        with self.assertRaises(ValueError):
            score(obj)

    def test_duplicate_case_rejected(self):
        obj = json.loads((ROOT / "examples/empty_predictions.json").read_text())
        obj["predictions"][1]["case_id"] = "C001"
        with self.assertRaises(ValueError):
            score(obj)

if __name__ == "__main__":
    unittest.main()
