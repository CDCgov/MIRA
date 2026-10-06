import csv
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from app.seqsender_handler import _absolutize_raw_reads_paths


class AbsolutizeRawReadsPathsTests(TestCase):
    fieldnames = ["sequence_name", "sra-sample_name", "sra-file_1", "sra-file_2"]

    def _write_metadata(self, metadata_file: Path, rows: list[dict[str, str]]) -> None:
        with metadata_file.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_accepts_absolute_paths_and_resolves_relative_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            submission_dir = root / "submission"
            raw_reads_dir = submission_dir / "raw_reads"
            raw_reads_dir.mkdir(parents=True)
            relative_read = raw_reads_dir / "relative.fastq.gz"
            absolute_read = root / "external.fastq.gz"
            relative_read.write_bytes(b"relative")
            absolute_read.write_bytes(b"absolute")
            metadata_file = submission_dir / "metadata.csv"
            self._write_metadata(metadata_file, [{
                "sequence_name": "sequence-a",
                "sra-sample_name": "sample-a",
                "sra-file_1": str(absolute_read),
                "sra-file_2": relative_read.name,
            }])

            missing_samples = _absolutize_raw_reads_paths(
                str(metadata_file),
                str(submission_dir),
            )

            self.assertEqual(missing_samples, [])
            with metadata_file.open(newline="", encoding="utf-8") as fh:
                row = next(csv.DictReader(fh))
            self.assertEqual(row["sra-file_1"], os.path.realpath(absolute_read))
            self.assertEqual(row["sra-file_2"], os.path.realpath(relative_read))

    def test_returns_unique_missing_samples_without_rewriting_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            submission_dir = root / "submission"
            (submission_dir / "raw_reads").mkdir(parents=True)
            metadata_file = submission_dir / "metadata.csv"
            self._write_metadata(metadata_file, [
                {
                    "sequence_name": "sequence-a",
                    "sra-sample_name": "sample-a",
                    "sra-file_1": "missing-1.fastq.gz",
                    "sra-file_2": "missing-2.fastq.gz",
                },
                {
                    "sequence_name": "sequence-b",
                    "sra-sample_name": "sample-b",
                    "sra-file_1": str(root / "missing-3.fastq.gz"),
                    "sra-file_2": "../outside.fastq.gz",
                },
            ])
            original_metadata = metadata_file.read_text(encoding="utf-8")

            missing_samples = _absolutize_raw_reads_paths(
                str(metadata_file),
                str(submission_dir),
            )

            self.assertEqual(missing_samples, ["sample-a", "sample-b"])
            self.assertEqual(metadata_file.read_text(encoding="utf-8"), original_metadata)


if __name__ == "__main__":
    import unittest

    unittest.main()