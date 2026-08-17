import gzip
import random
from typing import List


def reservoir_sample_gz(
    input_path: str,
    k: int = 10_000,
    seed: int | None = 42
) -> List[str]:
    """
    Samples exactly k lines uniformly at random from a gzipped text file.
    Memory complexity: O(k)
    Time complexity: O(N)
    """
    if seed is not None:
        random.seed(seed)

    reservoir: List[str] = []

    # Open the gzipped file in text-reading mode ('rt')
    with gzip.open(input_path, mode="rt", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f):
            cleaned_line = line.strip()
            if not cleaned_line:
                continue

            # Fill phase: populate the initial k slots
            if len(reservoir) < k:
                reservoir.append(cleaned_line)
            else:
                # Stream phase: idx is 0-indexed, so we pick j uniformly from [0, idx]
                j = random.randint(0, idx)
                if j < k:
                    reservoir[j] = cleaned_line

    return reservoir


def save_samples(samples: List[str], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        for item in samples:
            f.write(f"{item}\n")