def gopher_quality_filter(text: str) -> bool:
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