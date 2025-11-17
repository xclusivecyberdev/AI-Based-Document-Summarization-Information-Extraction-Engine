"""
Initialize and download required models
"""
import spacy
import nltk
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer
from loguru import logger


def download_spacy_model():
    """Download spaCy model"""
    logger.info("Downloading spaCy model...")
    try:
        import subprocess
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
        logger.info("spaCy model downloaded successfully")
    except Exception as e:
        logger.error(f"Failed to download spaCy model: {str(e)}")


def download_nltk_data():
    """Download NLTK data"""
    logger.info("Downloading NLTK data...")

    datasets = [
        'punkt',
        'stopwords',
        'averaged_perceptron_tagger',
        'wordnet',
        'omw-1.4'
    ]

    for dataset in datasets:
        try:
            nltk.download(dataset, quiet=True)
            logger.info(f"Downloaded: {dataset}")
        except Exception as e:
            logger.error(f"Failed to download {dataset}: {str(e)}")


def download_transformers_model():
    """Download transformer model"""
    logger.info("Downloading transformer models...")

    models = [
        "facebook/bart-large-cnn",
        # "t5-small",  # Uncomment if needed
    ]

    for model_name in models:
        try:
            logger.info(f"Downloading {model_name}...")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            logger.info(f"Downloaded: {model_name}")
        except Exception as e:
            logger.error(f"Failed to download {model_name}: {str(e)}")


def download_sentence_transformer():
    """Download sentence transformer model"""
    logger.info("Downloading sentence transformer...")

    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Sentence transformer downloaded successfully")
    except Exception as e:
        logger.error(f"Failed to download sentence transformer: {str(e)}")


def main():
    """Main function"""
    logger.info("Initializing models...")

    download_spacy_model()
    download_nltk_data()
    download_transformers_model()
    download_sentence_transformer()

    logger.info("All models initialized successfully!")


if __name__ == "__main__":
    main()
