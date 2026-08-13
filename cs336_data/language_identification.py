import fasttext
import re

def identify_language(text: str):
    model_path = "local-shared-data/classifiers/lid.176.bin"
    model = fasttext.load_model(model_path)
    clean_text = re.sub(r"\s+", " ", text).strip()
    labels, probabilities = model.predict(clean_text, k=1)
    lang_code = labels[0].replace("__label__", "")
    confidence_score = float(probabilities[0])
    return (lang_code, confidence_score)
