import unittest
import tempfile
import os

from presidio_analyzer import AnalyzerEngine
from pattern_file_recognizer import PatternFileRecognizer


class TestPatternFileRecognizer(unittest.TestCase):
    def setUp(self):
        self.analyzer = AnalyzerEngine()
        self.temp_files = []

    def tearDown(self):
        for f in self.temp_files:
            if os.path.exists(f):
                os.unlink(f)

    def _create_temp_file(self, content: str, suffix: str = ".txt") -> str:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=suffix) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name

    def test_empty_patterns_files_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            PatternFileRecognizer(patterns_files=[], entity_type="TEST")
        self.assertIn("must be non-empty", str(ctx.exception))

    def test_missing_file_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            PatternFileRecognizer(
                patterns_files=["/nonexistent/path.txt"],
                entity_type="TEST"
            )

    def test_txt_file_loading(self):
        patterns_file = self._create_temp_file("TestPattern\nAnotherPattern\n")
        recognizer = PatternFileRecognizer(
            patterns_files=[patterns_file],
            entity_type="TEST_ENTITY"
        )

        text = "Found TestPattern here"
        results = recognizer.analyze(text, entities=[], nlp_artifacts=None)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_type, "TEST_ENTITY")
        self.assertEqual(text[results[0].start:results[0].end], "TestPattern")

    def test_txt_file_comments_and_blank_lines(self):
        patterns_file = self._create_temp_file(
            "# This is a comment\n"
            "ValidPattern\n"
            "\n"
            "  \n"
            "# Another comment\n"
            "AnotherValid\n"
        )
        recognizer = PatternFileRecognizer(
            patterns_files=[patterns_file],
            entity_type="TEST_ENTITY"
        )

        text = "Found ValidPattern and # This is a comment here"
        results = recognizer.analyze(text, entities=[], nlp_artifacts=None)

        self.assertEqual(len(results), 1)
        self.assertEqual(text[results[0].start:results[0].end], "ValidPattern")

    def test_csv_file_loading(self):
        csv_file = self._create_temp_file(
            "name,description\n"
            "CustomerA,First customer\n"
            "CustomerB,Second customer\n",
            suffix=".csv"
        )
        recognizer = PatternFileRecognizer(
            patterns_files=[csv_file],
            entity_type="CUSTOMER",
            csv_column="name"
        )

        text = "Working with CustomerA today"
        results = recognizer.analyze(text, entities=[], nlp_artifacts=None)

        self.assertEqual(len(results), 1)
        self.assertEqual(text[results[0].start:results[0].end], "CustomerA")

    def test_csv_file_with_tuple_column_override(self):
        csv_file = self._create_temp_file(
            "product_name,category\n"
            "ProductX,Electronics\n"
            "ProductY,Furniture\n",
            suffix=".csv"
        )
        recognizer = PatternFileRecognizer(
            patterns_files=[(csv_file, "product_name")],
            entity_type="PRODUCT"
        )

        text = "Check out ProductX and ProductY"
        results = recognizer.analyze(text, entities=[], nlp_artifacts=None)

        self.assertEqual(len(results), 2)

    def test_csv_missing_column_raises_error(self):
        csv_file = self._create_temp_file(
            "col_a,col_b\n"
            "value1,value2\n",
            suffix=".csv"
        )
        with self.assertRaises(ValueError) as ctx:
            PatternFileRecognizer(
                patterns_files=[csv_file],
                entity_type="TEST",
                csv_column="nonexistent"
            )
        self.assertIn("nonexistent", str(ctx.exception))
        self.assertIn("col_a", str(ctx.exception))
        self.assertIn("col_b", str(ctx.exception))

    def test_allowlist_filtering(self):
        patterns_file = self._create_temp_file("Apple\nOrange\nUniqueCustomer\n")
        allowlist_file = self._create_temp_file("apple\norange\n")

        recognizer = PatternFileRecognizer(
            patterns_files=[patterns_file],
            allowlist_files=[allowlist_file],
            entity_type="TEST_ENTITY"
        )

        text_apple = "We work with Apple on this project."
        results_apple = recognizer.analyze(text_apple, entities=[], nlp_artifacts=None)
        self.assertEqual(len(results_apple), 0, "Allowlisted word 'Apple' should be filtered")

        text_unique = "UniqueCustomer is our partner."
        results_unique = recognizer.analyze(text_unique, entities=[], nlp_artifacts=None)
        self.assertEqual(len(results_unique), 1)
        self.assertEqual(results_unique[0].entity_type, "TEST_ENTITY")

    def test_allowlist_csv_with_tuple_override(self):
        patterns_file = self._create_temp_file("Apple\nOrange\nUniqueCustomer\n")
        allowlist_file = self._create_temp_file(
            "word,type\n"
            "apple,fruit\n"
            "orange,fruit\n",
            suffix=".csv"
        )

        recognizer = PatternFileRecognizer(
            patterns_files=[patterns_file],
            allowlist_files=[(allowlist_file, "word")],
            entity_type="TEST_ENTITY"
        )

        text = "Apple and UniqueCustomer"
        results = recognizer.analyze(text, entities=[], nlp_artifacts=None)

        self.assertEqual(len(results), 1)
        self.assertEqual(text[results[0].start:results[0].end], "UniqueCustomer")

    def test_case_insensitive_by_default(self):
        patterns_file = self._create_temp_file("TestPattern\n")
        recognizer = PatternFileRecognizer(
            patterns_files=[patterns_file],
            entity_type="TEST_ENTITY"
        )

        text = "Found testpattern here"
        results = recognizer.analyze(text, entities=[], nlp_artifacts=None)
        self.assertEqual(len(results), 1)

    def test_case_sensitive_option(self):
        patterns_file = self._create_temp_file("TestPattern\n")
        recognizer = PatternFileRecognizer(
            patterns_files=[patterns_file],
            entity_type="TEST_ENTITY",
            case_sensitive=True
        )

        text_exact = "Found TestPattern here"
        results_exact = recognizer.analyze(text_exact, entities=[], nlp_artifacts=None)
        self.assertEqual(len(results_exact), 1)

        text_lower = "Found testpattern here"
        results_lower = recognizer.analyze(text_lower, entities=[], nlp_artifacts=None)
        self.assertEqual(len(results_lower), 0)

    def test_multiple_patterns_files(self):
        file1 = self._create_temp_file("PatternFromFile1\n")
        file2 = self._create_temp_file("PatternFromFile2\n")

        recognizer = PatternFileRecognizer(
            patterns_files=[file1, file2],
            entity_type="TEST_ENTITY"
        )

        text = "Found PatternFromFile1 and PatternFromFile2"
        results = recognizer.analyze(text, entities=[], nlp_artifacts=None)
        self.assertEqual(len(results), 2)

    def test_analyzer_integration(self):
        patterns_file = self._create_temp_file("SpecialClient\n")
        recognizer = PatternFileRecognizer(
            patterns_files=[patterns_file],
            entity_type="CUSTOM_ENTITY"
        )
        self.analyzer.registry.add_recognizer(recognizer)

        text = "Does SpecialClient know about the deal?"
        results = self.analyzer.analyze(text=text, language="en")

        found = False
        for res in results:
            if res.entity_type == "CUSTOM_ENTITY":
                found = True
                break
        self.assertTrue(found, "Should find CUSTOM_ENTITY via AnalyzerEngine")

    def test_whitespace_handling(self):
        patterns_file = self._create_temp_file("  TrimmedPattern  \n  AnotherOne\n")
        recognizer = PatternFileRecognizer(
            patterns_files=[patterns_file],
            entity_type="TEST_ENTITY"
        )

        text = "Found TrimmedPattern here"
        results = recognizer.analyze(text, entities=[], nlp_artifacts=None)
        self.assertEqual(len(results), 1)
        self.assertEqual(text[results[0].start:results[0].end], "TrimmedPattern")

    def test_duplicate_patterns_deduplicated(self):
        patterns_file = self._create_temp_file("DuplicatePattern\nDuplicatePattern\n")
        recognizer = PatternFileRecognizer(
            patterns_files=[patterns_file],
            entity_type="TEST_ENTITY"
        )

        text = "Found DuplicatePattern here"
        results = recognizer.analyze(text, entities=[], nlp_artifacts=None)
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
