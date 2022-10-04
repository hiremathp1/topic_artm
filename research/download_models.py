import nltk

def download_models():
    nltk.download("stopwords")
    nltk.download("wordnet")

if __name__ == '__main__':
    download_models()
