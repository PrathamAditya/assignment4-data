from fastwarc.warc import ArchiveIterator, WarcRecordType
import resiliparse
from resiliparse.parse.encoding import detect_encoding
from resiliparse.extract.html2text import extract_plain_text
from fastwarc.warc import ArchiveIterator, WarcRecordType
import re


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
    inspect_wrac_records()