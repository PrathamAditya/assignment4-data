import os
import random
import string
import unicodedata
from collections import defaultdict
from functools import partial
from itertools import combinations
from pathlib import Path
from typing import Callable, Sequence, Union
import mmh3


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def remove_punctuation(text: str) -> str:
    return text.translate(str.maketrans("", "", string.punctuation))


def create_hash_functions(seeds: Sequence[int]) -> list[Callable[[str], int]]:
    return [partial(mmh3.hash, seed=s, signed=False) for s in seeds]


def generate_random_integers(n: int, seed: int = 42) -> list[int]:
    rng = random.Random(seed)
    return [rng.randint(0, 2**31 - 1) for _ in range(n)]


class DisjointSetUnion:
    def __init__(self, elements):
        self.parent = {x: x for x in elements}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x != root_y:
            self.parent[root_y] = root_x


def minhash_deduplication(
    input_files: list[Union[os.PathLike, str]],
    num_hashes: int,
    num_bands: int,
    ngram_size: int,
    jaccard_threshold: float,
    output_directory: Union[os.PathLike, str],
    seed: int = 42,
) -> None:
    assert num_hashes % num_bands == 0, (
        f"num_hashes ({num_hashes}) must be evenly divisible by num_bands ({num_bands})"
    )
    rows_per_band = num_hashes // num_bands

    out_dir = Path(output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)

    seeds = generate_random_integers(num_hashes, seed=seed)
    hash_functions = create_hash_functions(seeds)

    file_contents: dict[str, str] = {}
    signatures: dict[str, list[int]] = {}

    for path_str in input_files:
        path = Path(path_str)
        with open(path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        file_contents[path.name] = raw_text

        nfd_text = unicodedata.normalize("NFD", raw_text)
        stripped = "".join(c for c in nfd_text if unicodedata.category(c) != "Mn")
        cleaned_text = normalize_whitespace(remove_punctuation(stripped.lower()))
        words = cleaned_text.split()

        if len(words) >= ngram_size:
            shingles = {" ".join(words[i : i + ngram_size]) for i in range(len(words) - ngram_size + 1)}
        elif words:
            shingles = {" ".join(words)}
        else:
            shingles = {""}

        sig = [min(h_func(shingle) for shingle in shingles) for h_func in hash_functions]
        signatures[path.name] = sig

    buckets = defaultdict(lambda: defaultdict(list))
    for doc_id, sig in signatures.items():
        for band_idx in range(num_bands):
            start = band_idx * rows_per_band
            end = start + rows_per_band
            band_chunk = tuple(sig[start:end])
            buckets[band_idx][band_chunk].append(doc_id)

    candidate_pairs = set()
    for band_idx, band_buckets in buckets.items():
        for chunk_hash, cluster_docs in band_buckets.items():
            if len(cluster_docs) > 1:
                for doc1, doc2 in combinations(sorted(cluster_docs), 2):
                    candidate_pairs.add((doc1, doc2))

    dsu = DisjointSetUnion(list(file_contents.keys()))
    for doc1, doc2 in candidate_pairs:
        sig1 = signatures[doc1]
        sig2 = signatures[doc2]
        estimated_jaccard = sum(1 for a, b in zip(sig1, sig2) if a == b) / num_hashes
        if estimated_jaccard >= jaccard_threshold:
            dsu.union(doc1, doc2)

    clusters = defaultdict(list)
    for doc_id in sorted(file_contents.keys()):
        clusters[dsu.find(doc_id)].append(doc_id)

    rng = random.Random(seed)
    retained_docs = set()
    for cluster_members in clusters.values():
        if len(cluster_members) == 1:
            retained_docs.add(cluster_members[0])
        else:
            chosen = rng.choice(sorted(cluster_members))
            retained_docs.add(chosen)

    for doc_name in retained_docs:
        out_path = out_dir / doc_name
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(file_contents[doc_name])