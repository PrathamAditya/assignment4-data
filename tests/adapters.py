from __future__ import annotations

import os
from typing import Any
from fastwarc.warc import ArchiveIterator, WarcRecordType
import resiliparse
from resiliparse.parse.encoding import detect_encoding
from resiliparse.extract.html2text import extract_plain_text
from cs336_data.language_identification import identify_language
from cs336_data.mask_pii import mask_emails, mask_phone_numbers, mask_ipv4
from cs336_data.harmful_content import nsfw_classifier, toxic_speech_nsfw_classifier
from cs336_data.gopher_quality_filters import gopher_quality_filter_subset
from cs336_data.train_classifier import test_model

def run_extract_text_from_html_bytes(html_bytes: bytes) -> str | None:
    try:
        decoded_input = html_bytes.decode("utf-8")
    except UnicodeDecodeError:
        enc = detect_encoding(html_bytes)
        decoded_input = html_bytes.decode(f"{enc}")
    return resiliparse.extract.html2text.extract_plain_text(decoded_input) 

def run_identify_language(text: str) -> tuple[Any, float]:
    return identify_language(text)


def run_mask_emails(text: str) -> tuple[str, int]:
    return mask_emails(text)


def run_mask_phone_numbers(text: str) -> tuple[str, int]:
    return mask_phone_numbers(text)


def run_mask_ips(text: str) -> tuple[str, int]:
    return mask_ipv4(text)


def run_classify_nsfw(text: str) -> tuple[Any, float]:
    return nsfw_classifier(text)


def run_classify_toxic_speech(text: str) -> tuple[Any, float]:
    return toxic_speech_nsfw_classifier(text)


def run_classify_quality(text: str) -> tuple[Any, float]:
    return test_model(text)


def run_gopher_quality_filter(text: str) -> bool:
    return gopher_quality_filter_subset(text)


def run_exact_line_deduplication(
    input_files: list[os.PathLike], output_directory: os.PathLike
):
    raise NotImplementedError


def run_minhash_deduplication(
    input_files: list[os.PathLike],
    num_hashes: int,
    num_bands: int,
    ngrams: int,
    jaccard_threshold: float,
    output_directory: os.PathLike,
):
    raise NotImplementedError
