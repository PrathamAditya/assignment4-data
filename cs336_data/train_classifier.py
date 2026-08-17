import os
import re
from typing import Dict, Tuple
import fasttext


def train_quality_classifier(
    train_path: str,
    output_model_path: str = "data/classifier/quality_classifier.bin",
    lr: float = 0.3,
    epoch: int = 20,
    word_ngrams: int = 2,
    dim: int = 64,
    bucket: int = 200000,
) -> fasttext.FastText._FastText:
    """Trains a fastText supervised classifier for document quality."""
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"Training file not found: {train_path}")

    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)

    print(f"Training fastText quality classifier on '{train_path}'...")
    model = fasttext.train_supervised(
        input=train_path,
        lr=lr,
        epoch=epoch,
        wordNgrams=word_ngrams,
        dim=dim,
        bucket=bucket,
        loss="softmax",
    )

    model.save_model(output_model_path)
    print(f"Model saved successfully to '{output_model_path}'.\n")
    return model


def evaluate_classifier(model: fasttext.FastText._FastText, valid_path: str) -> Tuple[int, float, float, float]:
    """Evaluates the classifier on the validation split and prints standard metrics."""
    if not os.path.exists(valid_path):
        raise FileNotFoundError(f"Validation file not found: {valid_path}")

    n_samples, precision, recall = model.test(valid_path)
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print("-" * 35)
    print("VALIDATION METRICS")
    print("-" * 35)
    print(f"Evaluated Samples : {n_samples}")
    print(f"Precision @ 1     : {precision:.4f}")
    print(f"Recall @ 1        : {recall:.4f}")
    print(f"F1 Score          : {f1:.4f}")
    print("-" * 35 + "\n")

    return n_samples, precision, recall, f1


def get_quality_score(
    text: str,
    model: fasttext.FastText._FastText,
    positive_label: str = "__label__positive"
) -> float:
    """
    Returns a numeric quality score between 0.0 and 1.0 representing
    the predicted probability of the document being high quality.
    """
    cleaned_text = " ".join(text.replace("\n", " ").split())
    if not cleaned_text:
        return 0.0

    labels, probs = model.predict(cleaned_text, k=len(model.get_labels()))
    for label, prob in zip(labels, probs):
        if label == positive_label:
            return float(prob)

    return 0.0


def run_sanity_checks(model: fasttext.FastText._FastText):
    """Runs quality predictions across standard test archetypes."""
    test_cases: Dict[str, str] = {
        "High Quality (Academic/Prose)": (
            "Stanford University, officially Leland Stanford Junior University, is a private "
            "research university in Stanford, California. The campus occupies 8,180 acres among "
            "the largest in the United States, and enrolls over 17,000 students. Stanford is "
            "ranked among the top universities in the world by major academic publications."
        ),
        "Low Quality (Error Log Dump)": (
            "Strict Standards: Non-static method utf_normalizer::nfkc() should not be called "
            "statically in /home/mati/domains/forum.programosy.pl/public_html/includes/utf/utf_tools.php on line 1663. "
            "Deprecated: preg_replace(): The /e modifier is deprecated, use preg_replace_callback instead."
        ),
        "Low Quality (Nav / Boilerplate)": (
            "Skip to content TICKETS Artists Useful information Menores Movilidad Reducida "
            "How to get there Sustainability The City and Territory Podcast Tienda Merch Privacy Policy"
        ),
    }

    print("SANITY CHECK PREDICTIONS")
    print("-" * 35)
    for category, text in test_cases.items():
        score = get_quality_score(text, model)
        print(f"[{category}]\nScore: {score:.4f}\n")

def test_model(text: str):
    model_path = "data/classifier/quality_classifier.bin"
    model = fasttext.load_model(model_path)
    clean_text = re.sub(r"\s+", " ", text).strip()
    if not clean_text:
        return ("", 0.0)
    labels, probabilities = model.predict(clean_text, k=1)
    lang_code = labels[0].replace("__label__", "")
    confidence_score = float(probabilities[0])
    return (lang_code, confidence_score)
if __name__ == "__main__":
    # TRAIN_FILE = "data/classifier/train.txt"
    # VALID_FILE = "data/classifier/valid.txt"
    # MODEL_OUTPUT = "data/classifier/quality_classifier.bin"

    # # 1. Train
    # model = train_quality_classifier(
    #     train_path=TRAIN_FILE,
    #     output_model_path=MODEL_OUTPUT,
    #     lr=0.3,
    #     epoch=20,
    #     word_ngrams=2,
    #     dim=512,
    #     bucket=200000,
    # )

    # # 2. Evaluate on validation split
    # evaluate_classifier(model, VALID_FILE)

    # # 3. Test on sanity check samples
    # run_sanity_checks(model)
    long_article_sample = """
    Stanford University, officially Leland Stanford Junior University, is a private research 
    university located in Stanford, California. The university was founded in 1885 by Leland 
    and Jane Stanford in memory of their only child, Leland Stanford Jr., who had died of typhoid 
    fever the previous year at age 15. Stanford was established as a coeducational and non-denominational 
    institution. The campus occupies approximately 8,180 acres, making it one of the largest continuous 
    university campuses in the United States. 

    Stanford is organized into seven academic schools, including business, law, medicine, and engineering, 
    alongside humanities and sciences. Its faculty and alumni have founded numerous prominent technology 
    companies, contributing significantly to the development of Silicon Valley. Stanford researchers 
    have achieved global recognition, with dozens of Nobel laureates, Turing Award winners, and Fields 
    Medalists among its affiliated scholars and graduates. The university consistently ranks among the 
    top higher education institutions worldwide in academic rankings and research output.
    """

    print("Long Sample Score:", test_model(long_article_sample))