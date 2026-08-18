import hashlib
import os
from collections import Counter
from pathlib import Path


def exact_line_deduplication(
    paths: list[os.PathLike | str],
    output_directory: os.PathLike | str,
) -> None:
    out_dir = Path(output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Pass 1: count how many times each line (by hash) appears across ALL files
    line_counts: Counter[str] = Counter()

    for path in paths:
        p = Path(path)
        with open(p, "r", encoding="utf-8") as in_f:
            for line in in_f:
                line_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()
                line_counts[line_hash] += 1

    # Pass 2: write out only lines that appear exactly once across the corpus
    for path in paths:
        p = Path(path)
        file_lines: list[str] = []

        with open(p, "r", encoding="utf-8") as in_f:
            for line in in_f:
                line_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()
                if line_counts[line_hash] == 1:
                    file_lines.append(line)

        output_file = out_dir / p.name
        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.writelines(file_lines)


def run_exact_line_deduplication(
    input_files: list[os.PathLike | str], output_directory: os.PathLike | str
) -> None:
    exact_line_deduplication(input_files, output_directory)