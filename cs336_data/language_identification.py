import fasttext
import re
import random
from fastwarc.warc import ArchiveIterator
from cs336_data.extract_text import extract_file, normalize_id


def identify_language(text: str):
    model_path = "local-shared-data/classifiers/lid.176.bin"
    model = fasttext.load_model(model_path)
    clean_text = re.sub(r"\s+", " ", text).strip()
    labels, probabilities = model.predict(clean_text, k=1)
    lang_code = labels[0].replace("__label__", "")
    confidence_score = float(probabilities[0])
    return (lang_code, confidence_score)

def print_extractions(start_idx: int, end_idx: int):
    warc_path = "local-shared-data/CC/example.warc.wet.gz"
    with open(warc_path, "rb") as f:
        for i, record in enumerate(ArchiveIterator(f)):
            classifier_response = identify_language(extract_file(record.reader.read()))
            actual_lang = record.headers.get("WARC-Identified-Content-Language")
            if start_idx<=i < end_idx: 
                print(f"AC: {actual_lang} and CR: {classifier_response}")
                print("#################################################")
            if i>end_idx:
                break

    warc_path = "local-shared-data/CC/example.warc.gz"
    all_extractions = []

    with open(warc_path, "rb") as warc_file:
        for i, record in enumerate(ArchiveIterator(warc_file)):
            print(i)
            if i == 200:
                break
            # print(record)
            # print(record.record_type)
            # if record.record_type == "response":
            rec_id = normalize_id(record.headers.get("WARC-Record-ID"))
            if rec_id:
                rec_id = normalize_id(record.headers.get("WARC-Record-ID"))
                rec_icl = record.headers.get("WARC-Identified-Content-Language")
                # print(rec_icl)
                warc_html = record.reader.read()
                # print(warc_html)
                my_text = extract_file(warc_html)
                if my_text and my_text.strip():
                    all_extractions.append({"id": rec_id, "text": my_text, "rec_icl": rec_icl})

    print(f"Total extracted WARC records: {len(all_extractions)}")

    # 2. Randomly sample 30 records
    sample_size = min(num_samples, len(all_extractions))
    random_samples = random.sample(all_extractions, sample_size)

    # 3. Print the randomly chosen records
    for idx, item in enumerate(random_samples, start=1):
        print("========================================")
        print(f"Record ID: {item['id']} | ICL: {item['rec_icl']}")
        print("\n")

# def print_random_warc_extractions(num_samples: int = 40):
    warc_path = "local-shared-data/CC/example.warc.gz"
    candidate_records = []

    print("Collecting records from WARC file...")
    with open(warc_path, "rb") as f:
        for record in ArchiveIterator(f):
            # 1. WARC files use "response" records for web pages
            if record.record_type != "response":
                continue

            # 2. Skip non-HTML responses (images, CSS, JS, etc.)
            http_headers = record.http_headers
            content_type = (
                http_headers.get("Content-Type", "") if http_headers else ""
            )
            if "text/html" not in content_type.lower():
                continue

            # 3. Read raw HTML payload
            payload_bytes = record.reader.read()
            if not payload_bytes:
                continue

            actual_lang = record.headers.get(
                "WARC-Identified-Content-Language"
            )

            # Store payload to process ONLY the chosen 40 samples later
            candidate_records.append((actual_lang, payload_bytes))

    total_found = len(candidate_records)
    print(f"Total valid HTML records found: {total_found}")

    if not candidate_records:
        print("No valid HTML records found in WARC file.")
        return

    # 4. Pick N random records from candidates
    sample_size = min(num_samples, total_found)
    selected_samples = random.sample(candidate_records, sample_size)

    # 5. Extract text and classify ONLY the chosen 40 records (saves massive compute!)
    for idx, (actual_lang, payload_bytes) in enumerate(
        selected_samples, start=1
    ):
        extracted_text = extract_file(payload_bytes)

        if not extracted_text or not extracted_text.strip():
            classifier_response = ("empty_text", 0.0)
        else:
            classifier_response = identify_language(extracted_text)

        print(f"SAMPLE {idx}/{sample_size}")
        print(f"AC: {actual_lang} | CR: {classifier_response}")
        print("-------------------------------------------------")
        print(f"TEXT PREVIEW: {extracted_text[:200]}...")
        print("#################################################\n")
if __name__ == "__main__":
    # _print_random_warc_extractions(30)
    print_extractions(200, 260)