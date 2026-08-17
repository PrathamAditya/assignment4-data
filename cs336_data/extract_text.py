from fastwarc.warc import ArchiveIterator, WarcRecordType
import resiliparse
from resiliparse.parse.encoding import detect_encoding
from resiliparse.extract.html2text import extract_plain_text
from fastwarc.warc import ArchiveIterator, WarcRecordType
import re
import brotli
import zlib
import gzip


def decompress_payload(raw_bytes: bytes, encoding: str) -> bytes:
    """Decompresses HTTP payload according to Content-Encoding header."""
    if not raw_bytes or not encoding:
        return raw_bytes

    encoding = encoding.lower().strip()
    try:
        if encoding == "br":
            return brotli.decompress(raw_bytes)
        elif encoding == "gzip":
            return gzip.decompress(raw_bytes)
        elif encoding == "deflate":
            try:
                return zlib.decompress(raw_bytes)
            except zlib.error:
                # Handle raw deflate without zlib headers
                return zlib.decompress(raw_bytes, -zlib.MAX_WBITS)
    except Exception:
        # If decompression fails, fallback to raw bytes
        return raw_bytes

    return raw_bytes

def normalize_id(val: str | None) -> str | None:
    if not val:
        return None
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        val,
        re.IGNORECASE,
    )
    return match.group(0).lower() if match else val.strip("<> ").lower()

# def extract_file(input):
#     try:
#         decoded_input = input.decode("utf-8")
#     except UnicodeDecodeError:
#         enc = detect_encoding(input)
#         decoded_input = input.decode(f"{enc}")
#     return resiliparse.extract.html2text.extract_plain_text(decoded_input) 

def extract_file(input: bytes) -> str:
    if not input:
        return ""
    try:
        decoded_input = input.decode("utf-8")
    except UnicodeDecodeError:
        enc = detect_encoding(input)
        if not enc:
            enc = "utf-8"
        try:
            decoded_input = input.decode(enc, errors="replace")
        except (UnicodeDecodeError, LookupError):
            # Safe catch-all fallback
            decoded_input = input.decode("utf-8", errors="replace")

    return resiliparse.extract.html2text.extract_plain_text(decoded_input)

def extract_file_2(input_bytes: bytes) -> str:
    """Decodes raw payload bytes and extracts plain text."""
    if not input_bytes:
        return ""
    try:
        decoded_input = input_bytes.decode("utf-8")
    except UnicodeDecodeError:
        enc = detect_encoding(input_bytes)
        if not enc:
            enc = "utf-8"
        try:
            decoded_input = input_bytes.decode(enc, errors="replace")
        except (UnicodeDecodeError, LookupError):
            decoded_input = input_bytes.decode("utf-8", errors="replace")

    return resiliparse.extract.html2text.extract_plain_text(decoded_input)


def process_warc_file(
    warc_path: str, output_path: str, label: str = "__label__positive"
) -> int:
    valid_count = 0

    with open(warc_path, "rb") as warc_file, open(
        output_path, "w", encoding="utf-8"
    ) as out_f:
        # fastwarc ArchiveIterator directly takes record_types filter
        for record in ArchiveIterator(
            warc_file, record_types=WarcRecordType.response
        ):
            # Check Content-Type header
            content_type = ""
            content_encoding = ""

            if record.http_headers:
                # fastwarc headers can be accessed case-insensitively via .get()
                content_type = (
                    record.http_headers.get("Content-Type", "") or ""
                ).lower()
                content_encoding = (
                    record.http_headers.get("Content-Encoding", "") or ""
                ).lower()

            if (
                "text/html" not in content_type
                and "text/plain" not in content_type
            ):
                continue

            # In fastwarc, read payload via record.reader.read()
            raw_payload = record.reader.read()
            if not raw_payload:
                continue

            # Decompress if Brotli/Gzip/Deflate
            payload = decompress_payload(raw_payload, content_encoding)

            # Extract plain text
            extracted_text = extract_file_2(payload)
            if not extracted_text:
                continue

            single_line_text = " ".join(extracted_text.split())
            if len(single_line_text.split()) < 20:
                continue

            out_f.write(f"{label} {single_line_text}\n")
            valid_count += 1

            if valid_count % 100 == 0:
                print(f"Extracted {valid_count} documents...", end="\r")

    print(f"\nDone! Extracted {valid_count} documents to '{output_path}'.")
    return valid_count

def normalize_id(val: str | None) -> str | None:
    if not val:
        return None
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        val,
        re.IGNORECASE,
    )
    return match.group(0).lower() if match else val.strip("<> ").lower()


def comparison_warc_wet():
    warc_path = "local-shared-data/CC/example.warc.gz"
    wet_path = "local-shared-data/CC/example.warc.wet.gz"
    target_id = "410fc213-8e9f-4e18-9416-66b4bac5cdce"

    my_text = None
    wet_text = None

    # 1. Search through WARC file
    with open(warc_path, "rb") as warc_file:
        for record in ArchiveIterator(warc_file):
            rec_id = normalize_id(record.headers.get("WARC-Record-ID"))
            if rec_id == target_id:
                warc_html = record.reader.read()
                my_text = extract_file(warc_html)
                break  # Stop searching once found

    # 2. Search through WET file
    with open(wet_path, "rb") as wet_file:
        for record in ArchiveIterator(wet_file):
            refers_to = normalize_id(record.headers.get("WARC-Refers-To"))
            if refers_to == target_id:
                wet_bytes = record.reader.read()
                wet_text = wet_bytes.decode("utf-8", errors="replace")
                break  # Stop searching once found

    # 3. Print side-by-side output
    print("===== MY EXTRACTION =====")
    print(
        my_text if my_text is not None else "[!] Record not found in WARC file"
    )
                # First matching ID: 410fc213-8e9f-4e18-9416-66b4bac5cdce
    print("\n===== WET EXTRACTION =====")
    print(
        wet_text if wet_text is not None else "[!] Record not found in WET file"
    )


def inspect_wet_records():
    wet_path = "local-shared-data/CC/example.warc.wet.gz"
    with open(wet_path, "rb") as f:
        for i, record in enumerate(ArchiveIterator(f)):
            print(i, record.record_type, record.record_id)
            print(record.headers)
            print("/n")

            if i == 5:
                break

def inspect_wrac_records():
    warc_path = "local-shared-data/CC/example.warc.wet.gz"
    with open(warc_path, "rb") as f:
        for i, record in enumerate(ArchiveIterator(f)):
            # print(i, record.record_type, record.record_id)
            print(record.reader.read())
            # print(extract_file(record.reader.read()))
            print(record.headers.get("WARC-Identified-Content-Language"))
            print("/n")

            if i == 5:
                break

if __name__ == "__main__":
    # WARC_INPUT = "local-shared-data/CC/example.warc.gz"
    WARC_INPUT = "data/subsampled_positive_urls_2.warc.gz"
    OUTPUT_FILE = "data/positive_extracted_text_test_1.txt"

    process_warc_file(WARC_INPUT, OUTPUT_FILE, label="__label__positive")