import os
import string
import mmh3
import random
from pathlib import Path
import unicodedata
from functools import partial
from typing import Callable
import mmh3


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())

def create_hash_functions(seeds: list[int]) -> list[Callable[[str], int]]:
    """Returns a list of hash functions, each bound to a specific seed."""
    return [partial(mmh3.hash, seed=s, signed=False) for s in seeds]

def remove_punctuation(text: str) -> str:
    return text.translate(str.maketrans("", "", string.punctuation))

def generate_random_integers(n: int) -> list[int]:
    return [random.randint(0, n*100) for _ in range(n)]

def minhash_deduplication(
        paths: list[os.PathLike | str],
        output_directory: os.PathLike | str,
        h: int,
        b: int,
        n_grams: int
    )-> None: 
    out_dir = Path(output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    seeds = generate_random_integers(h)
    signature_per_doc = []
    for path in paths:
        p = Path(path)
        with open(p, "r", encoding="utf-8") as doc:
            counter = 0
            n_grams_sets = set()
            text = doc.read()
            S = []

            # normalization
            nfd_text = unicodedata.normalize("NFD", text)
            stripped = "".join(c for c in nfd_text if unicodedata.category(c) != "Mn")
            lower = stripped.lower()
            remove_punc = remove_punctuation(lower)
            white_space_removal = normalize_whitespace(remove_punc)
            words = white_space_removal.strip()
            if len(words) > n_grams:
                while counter <= len(words):
                    inner_counter = counter
                    temp_list = []
                    while inner_counter <= n_grams:
                        temp_list.append(words[inner_counter])
                    n_grams_sets.add(tuple(temp_list))
            else:
                n_grams_sets.add(tuple(words))

            # hash function
            hash_functions = create_hash_functions(seeds)

            for fun in hash_functions:
                min_val = 0
                for gram in n_grams_sets:
                    min_val = min(min_val, fun(gram))
                S.append(min_val)
            signature_per_doc.append(S)

            

            
            






