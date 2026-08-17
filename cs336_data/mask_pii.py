import re

EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_PATTERN = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
# IPV4_PATTERN = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
IPV4_PATTERN = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"

def mask_emails(text: str):
    return re.subn(EMAIL_PATTERN, '|||EMAIL_ADDRESS|||', text)

def mask_phone_numbers(text: str):
    return re.subn(PHONE_PATTERN, '|||PHONE_NUMBER|||', text)

def mask_ipv4(text: str):
    return re.subn(IPV4_PATTERN, '|||IP_ADDRESS|||', text)

    

