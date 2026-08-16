import fasttext
import re

def nsfw_classifier(text: str):
    model_path = "local-shared-data/classifiers/dolma_fasttext_nsfw_jigsaw_model.bin"
    model = fasttext.load_model(model_path)
    clean_text = re.sub(r"\s+", " ", text).strip()
    labels, probabilities = model.predict(clean_text, k=1)
    lang_code = labels[0].replace("__label__", "")
    confidence_score = float(probabilities[0])
    return (lang_code, confidence_score)

def toxic_speech_nsfw_classifier(text: str):
    model_path = "local-shared-data/classifiers/dolma_fasttext_hatespeech_jigsaw_model.bin"
    model = fasttext.load_model(model_path)
    clean_text = re.sub(r"\s+", " ", text).strip()
    labels, probabilities = model.predict(clean_text, k=1)
    lang_code = labels[0].replace("__label__", "")
    confidence_score = float(probabilities[0])
    return (lang_code, confidence_score)
