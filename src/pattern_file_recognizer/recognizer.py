import csv
from pathlib import Path
from typing import List, Optional, Set, Union, Tuple

from presidio_analyzer import EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts
from flashtext import KeywordProcessor

FileSpec = Union[str, Tuple[str, str]]


class PatternFileRecognizer(EntityRecognizer):
    def __init__(
        self,
        patterns_files: List[FileSpec],
        entity_type: str,
        allowlist_files: Optional[List[FileSpec]] = None,
        csv_column: str = "name",
        case_sensitive: bool = False,
    ):
        if not patterns_files:
            raise ValueError("patterns_files must be non-empty")

        super().__init__(
            supported_entities=[entity_type],
            supported_language="en",
        )

        self.entity_type = entity_type
        self.csv_column = csv_column
        self.case_sensitive = case_sensitive
        self.keyword_processor = KeywordProcessor(case_sensitive=case_sensitive)

        allowlist = self._load_allowlist(allowlist_files or [])
        patterns = self._load_patterns(patterns_files)

        if case_sensitive:
            filtered_patterns = [p for p in patterns if p not in allowlist]
        else:
            allowlist_lower = {a.lower() for a in allowlist}
            filtered_patterns = [
                p for p in patterns if p.lower() not in allowlist_lower
            ]

        self.keyword_processor.add_keywords_from_list(filtered_patterns)

    def _load_patterns(self, files: List[FileSpec]) -> List[str]:
        patterns = []
        for file_spec in files:
            patterns.extend(self._load_file(file_spec))
        return list(dict.fromkeys(patterns))

    def _load_allowlist(self, files: List[FileSpec]) -> Set[str]:
        allowlist = set()
        for file_spec in files:
            allowlist.update(self._load_file(file_spec))
        return allowlist

    def _load_file(self, file_spec: FileSpec) -> List[str]:
        if isinstance(file_spec, tuple):
            path_str, column = file_spec
        else:
            path_str = file_spec
            column = self.csv_column

        path = Path(path_str)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if path.suffix.lower() == ".csv":
            return self._load_csv(path, column)
        else:
            return self._load_txt(path)

    def _load_txt(self, path: Path) -> List[str]:
        patterns = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
        return patterns

    def _load_csv(self, path: Path, column: str) -> List[str]:
        patterns = []
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None or column not in reader.fieldnames:
                available = list(reader.fieldnames) if reader.fieldnames else []
                raise ValueError(
                    f"Column '{column}' not found in {path}. "
                    f"Available columns: {available}"
                )
            for row in reader:
                value = row[column]
                if value and value.strip():
                    patterns.append(value.strip())
        return patterns

    def load(self) -> None:
        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        results = []
        matches = self.keyword_processor.extract_keywords(text, span_info=True)

        for _name, start, end in matches:
            result = RecognizerResult(
                entity_type=self.entity_type,
                start=start,
                end=end,
                score=1.0,
            )
            results.append(result)

        return results
