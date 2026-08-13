from fastwarc.warc import ArchiveIterator, WarcRecordType
import resiliparse
from resiliparse.parse.encoding import detect_encoding
from resiliparse.extract.html2text import extract_plain_text
html_utf8 = "<html><body><h1>Hello World</h1><p>This is UTF-8 text.</p></body></html>".encode("utf-8")
html_cp1252 = "<html><body><h1>Café</h1><p>Bonjour, ça va?</p></body></html>".encode("cp1252")

def extract_file(input):
    try:
        decoded_input = input.decode("utf-8")
    except UnicodeDecodeError:
        enc = detect_encoding(input)
        decoded_input = input.decode(f"{enc}")
    return resiliparse.extract.html2text.extract_plain_text(decoded_input) 
if __name__ == "__main__":
    print(extract_file(html_utf8))
    print(extract_file(html_cp1252))