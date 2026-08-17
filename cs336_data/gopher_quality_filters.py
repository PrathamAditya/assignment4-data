import os
import re
import fasttext
from collections import Counter
from typing import List
from cs336_data.language_identification import identify_language
from fastwarc.warc import ArchiveIterator, WarcRecordType
from typing import Optional
import random


BASIC_STOPWORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have",
    "i", "it", "for", "not", "on", "with", "he", "as", "you",
    "do", "at", "this", "but", "his", "by", "from"
}

def get_ngrams(words: List[str], n: int) -> List[tuple]:
    return [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]

def basic_length_filter(text: str, min_words: int = 50, max_words: int = 100_000) -> bool:
    """Basic length check so negative examples match the word-count distribution of positives."""
    words = text.split()
    return min_words <= len(words) <= max_words

def gopher_quality_filter_subset(text: str) -> bool:
    if not text or not text.strip():
        return False

    words = text.split()
    num_words = len(words)

    if num_words < 50 or num_words > 100000:
        return False

    mean_word_length = sum(len(w) for w in words) / num_words
    if mean_word_length < 3 or mean_word_length > 10:
        return False

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return False

    num_line_with_ellipsis = sum(
        1 for line in lines if line.endswith(("...", "…"))
    )
    if (num_line_with_ellipsis / len(lines)) > 0.3:
        return False

    alpha_word_count = sum(
        1 for w in words if any(char.isalpha() for char in w)
    )
    if (alpha_word_count / num_words) < 0.80:
        return False

    return True

def full_gopher_quality_filter(text: str) -> bool:
    if not text or not text.strip():
        return False

    words = text.split()
    num_words = len(words)

    if num_words < 50 or num_words > 100_000:
        return False

    mean_word_length = sum(len(w) for w in words) / num_words
    if mean_word_length < 3 or mean_word_length > 10:
        return False

    words_lower = [w.lower() for w in words]
    stop_word_count = sum(1 for w in words_lower if w in BASIC_STOPWORDS)
    if stop_word_count < 2:
        return False

    alpha_word_count = sum(1 for w in words if any(char.isalpha() for char in w))
    if (alpha_word_count / num_words) < 0.80:
        return False

    symbol_count = sum(1 for w in words if "#" in w or "..." in w or "…" in w)
    if (symbol_count / num_words) > 0.10:
        return False

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return False

    num_ellipsis_lines = sum(1 for line in lines if line.endswith(("...", "…")))
    if (num_ellipsis_lines / len(lines)) > 0.30:
        return False

    bullet_prefixes = ("-", "*", "•", "—", ">")
    num_bullet_lines = sum(1 for line in lines if line.startswith(bullet_prefixes))
    if (num_bullet_lines / len(lines)) > 0.90:
        return False

    for n, threshold in [(2, 0.20), (3, 0.18), (4, 0.16)]:
        if num_words >= n:
            ngrams = get_ngrams(words_lower, n)
            counts = Counter(ngrams)
            most_common_count = counts.most_common(1)[0][1]
            if (most_common_count / len(ngrams)) > threshold:
                return False

    return True

def gopher_filter_line(text: str) -> bool:
    """Evaluates text against Gopher quality criteria."""
    words = text.split()
    num_words = len(words)

    if num_words < 50 or num_words > 100_000:
        return False

    mean_word_length = sum(len(w) for w in words) / num_words
    if mean_word_length < 3 or mean_word_length > 10:
        return False

    words_lower = [w.lower() for w in words]
    stop_word_count = sum(1 for w in words_lower if w in BASIC_STOPWORDS)
    if stop_word_count < 2:
        return False

    alpha_word_count = sum(1 for w in words if any(char.isalpha() for char in w))
    if (alpha_word_count / num_words) < 0.80:
        return False

    symbol_count = sum(1 for w in words if "#" in w or "..." in w or "…" in w)
    if (symbol_count / num_words) > 0.10:
        return False

    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if sentences:
        ellipsis_count = text.count("...") + text.count("…")
        if (ellipsis_count / len(sentences)) > 0.30:
            return False

    for n, threshold in [(2, 0.20), (3, 0.18), (4, 0.16)]:
        if num_words >= n:
            ngrams = get_ngrams(words_lower, n)
            counts = Counter(ngrams)
            most_common_count = counts.most_common(1)[0][1]
            if (most_common_count / len(ngrams)) > threshold:
                return False

    return True

def filter_dataset(
    input_path: str,
    output_path: str,
    lid_model_path: str = "local-shared-data/classifiers/lid.176.bin"
) -> dict:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not os.path.exists(lid_model_path):
        raise FileNotFoundError(f"Language model not found: {lid_model_path}")

    # 1. Load the language ID model ONCE
    print("Loading language identification model...")
    lid_model = fasttext.load_model(lid_model_path)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    total_count = 0
    passed_lid = 0
    passed_gopher = 0

    with open(input_path, "r", encoding="utf-8") as in_f, open(output_path, "w", encoding="utf-8") as out_f:
        for line in in_f:
            total_count += 1
            raw_line = line.strip()
            if not raw_line:
                continue

            # Extract pure text for evaluation (strip __label__* prefix if present)
            text = re.sub(r"^__label__\w+\s+", "", raw_line).strip()

            # Step 1: Language Identification Filter ('en' with conf > 0.5)
            lang, conf = identify_language(text, lid_model)
            if lang != "en" or conf <= 0.5:
                continue
            passed_lid += 1

            # Step 2: Gopher Quality Filter
            if not gopher_filter_line(text):
                continue
            passed_gopher += 1

            # Preserve original labeled line in destination file
            out_f.write(raw_line + "\n")

            if total_count % 500 == 0:
                print(f"Total: {total_count} | Passed LID: {passed_lid} | Passed Gopher: {passed_gopher}", end="\r")

    print(f"\nFiltering complete:")
    print(f"- Total processed: {total_count}")
    print(f"- Passed English LID: {passed_lid}")
    print(f"- Passed both (Final Output): {passed_gopher}")
    print(f"- Saved to: {output_path}")

    return {"total": total_count, "passed_lid": passed_lid, "passed_gopher": passed_gopher}

def extract_non_english_negatives_from_wet(
    wet_path: str,
    output_path: str,
    lid_model_path: str,
    target_count: int = 3382,
    conf_threshold: float = 0.70,
):
    if not os.path.exists(wet_path):
        raise FileNotFoundError(f"WET file not found: {wet_path}")
    if not os.path.exists(lid_model_path):
        raise FileNotFoundError(f"LID model not found: {lid_model_path}")

    print("Loading language identification model...")
    lid_model = fasttext.load_model(lid_model_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    extracted_count = 0
    total_records = 0

    with open(wet_path, "rb") as wet_f, open(output_path, "w", encoding="utf-8") as out_f:
        for record in ArchiveIterator(wet_f, record_types=WarcRecordType.conversion):
            total_records += 1

            raw_bytes = record.reader.read()
            if not raw_bytes:
                continue

            try:
                raw_text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raw_text = raw_bytes.decode("utf-8", errors="replace")

            single_line_text = " ".join(raw_text.split())
            if not single_line_text:
                continue

            # Check language: Keep ONLY NON-ENGLISH with confidence > 0.70
            lang, conf = identify_language(single_line_text, lid_model)
            if lang == "en" or conf <= conf_threshold:
                continue

            if not gopher_quality_filter_subset(raw_text):
                continue

            out_f.write(f"__label__negative {single_line_text}\n")
            extracted_count += 1

            if extracted_count % 100 == 0:
                print(
                    f"Extracted non-English negative records: {extracted_count}/{target_count} (Scanned {total_records} records)...",
                    end="\r"
                )

            if extracted_count >= target_count:
                break

    print(f"\nFinished! Extracted {extracted_count} non-English negative records to '{output_path}'.")

def merge_and_shuffle_datasets(
    pos_file: str,
    neg_file: str,
    train_output: str,
    valid_output: Optional[str] = None,
    valid_ratio: float = 0.0,
    seed: int = 42,
) -> None:
    """
    Merges positive and negative examples, shuffles them thoroughly,
    and writes train.txt. If valid_output is provided, it splits a fraction
    into valid_output.
    """
    random.seed(seed)

    with open(pos_file, "r", encoding="utf-8") as f:
        pos_lines = [line.strip() for line in f if line.strip()]

    with open(neg_file, "r", encoding="utf-8") as f:
        neg_lines = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(pos_lines)} positive and {len(neg_lines)} negative examples.")
    all_data = pos_lines + neg_lines
    random.shuffle(all_data)

    if valid_output and valid_ratio > 0.0:
        split_idx = int(len(all_data) * (1.0 - valid_ratio))
        train_data = all_data[:split_idx]
        valid_data = all_data[split_idx:]

        os.makedirs(os.path.dirname(valid_output), exist_ok=True)
        with open(valid_output, "w", encoding="utf-8") as f:
            for line in valid_data:
                f.write(line + "\n")
        print(f" -> Validation set: {len(valid_data)} records saved to '{valid_output}'")
    else:
        train_data = all_data

    os.makedirs(os.path.dirname(train_output), exist_ok=True)
    with open(train_output, "w", encoding="utf-8") as f:
        for line in train_data:
            f.write(line + "\n")

    print(f" -> Training set: {len(train_data)} records saved to '{train_output}'")

def extract_english_negative_samples(
    wet_path: str,
    output_path: str,
    lid_model_path: str,
    target_count: int = 3382,
    conf_threshold: float = 0.50,
):
    if not os.path.exists(wet_path):
        raise FileNotFoundError(f"WET file not found: {wet_path}")
    if not os.path.exists(lid_model_path):
        raise FileNotFoundError(f"LID model not found: {lid_model_path}")

    print("Loading language identification model...")
    lid_model = fasttext.load_model(lid_model_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    extracted_count = 0
    total_scanned = 0

    with open(wet_path, "rb") as wet_f, open(output_path, "w", encoding="utf-8") as out_f:
        for record in ArchiveIterator(wet_f, record_types=WarcRecordType.conversion):
            total_scanned += 1

            raw_bytes = record.reader.read()
            if not raw_bytes:
                continue

            try:
                raw_text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raw_text = raw_bytes.decode("utf-8", errors="replace")

            # 1. Flatten to single line
            single_line_text = " ".join(raw_text.split())
            if not single_line_text:
                continue

            # 2. Check length (match positive length threshold so model doesn't just learn doc length)
            if not basic_length_filter(single_line_text, min_words=50):
                continue

            # 3. English Language Check (MUST BE ENGLISH)
            lang, conf = identify_language(single_line_text, lid_model)
            if lang != "en" or conf < conf_threshold:
                continue

            # 4. Write as negative sample (DO NOT apply Gopher quality filters)
            out_f.write(f"__label__negative {single_line_text}\n")
            extracted_count += 1

            if extracted_count % 100 == 0:
                print(
                    f"Extracted {extracted_count}/{target_count} English negative records (Scanned {total_scanned})...",
                    end="\r",
                )

            if extracted_count >= target_count:
                break

    print(f"\nFinished! Extracted {extracted_count} English negative records to '{output_path}'.")

if __name__ == "__main__":

    # POS_TRAIN = "data/classifier/positive_valid_282.txt"
    # NEG_TRAIN = "data/classifier/negative_valid_282.txt"
    # TRAIN_OUT = "data/classifier/valid_WET.txt"


    # POS_TRAIN = "data/classifier/filtered_positive_WET_train_3100.txt"
    # NEG_TRAIN = "data/classifier/filtered_negative_WET_train_3100.txt"
    # TRAIN_OUT = "data/classifier/train_WET.txt"

    # merge_and_shuffle_datasets(
    #     pos_file=POS_TRAIN,
    #     neg_file=NEG_TRAIN,
    #     train_output=TRAIN_OUT,
    # )
    # WET_INPUT = "local-shared-data/CC/example.warc.wet.gz"
    # OUTPUT_FILE = "data/classifier/negative_extracted_text_2_3382.txt"
    # LID_MODEL = "local-shared-data/classifiers/lid.176.bin"
    # TARGET_RECORDS = 3382

    # extract_english_negative_samples(
    #     wet_path=WET_INPUT,
    #     output_path=OUTPUT_FILE,
    #     lid_model_path=LID_MODEL,
    #     target_count=TARGET_RECORDS,
    #     conf_threshold=0.50,
    # )

    POS_FILE = "data/classifier/filtered_positive_WET_train_3382.txt"
    NEG_FILE = "data/classifier/negative_extracted_text_2_3382.txt"

    TRAIN_OUT = "data/classifier/train.txt"
    VALID_OUT = "data/classifier/valid.txt"

    # ~8.34% of 3382 yields exactly ~282 validation samples per class (564 total)
    merge_and_shuffle_datasets(
        pos_file=POS_FILE,
        neg_file=NEG_FILE,
        train_output=TRAIN_OUT,
        valid_output=VALID_OUT,
        valid_ratio=0.0834,
        seed=42,
    )