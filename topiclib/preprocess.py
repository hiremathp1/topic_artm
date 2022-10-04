# Text processing and cleaning tools

from collections import Counter

import en_core_web_md
import nltk
from nltk import ngrams, word_tokenize
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer
from spacy.lang.en import English

parser = English()

# make sure punkt is installed
if nltk.data.find('tokenizers/punkt') is None:
    nltk.download('punkt')

MIN_WORD_LENGTH = 3


def tokenize(text):
    lda_tokens = []
    tokens = parser(text)
    for token in tokens:
        if token.orth_.isspace():
            continue
        elif token.like_url:
            lda_tokens.append("URL")
        elif token.orth_.startswith("@"):
            lda_tokens.append("SCREEN_NAME")
        else:
            lda_tokens.append(token.lower_)
    return lda_tokens


def get_lemma(word):
    lemma = wn.morphy(word)
    if lemma is None:
        return word
    else:
        return lemma


def get_lemma2(word):
    return WordNetLemmatizer().lemmatize(word)


def preprocess(text: str) -> [str]:
    """Removes english stop words and lemmatizes words"""
    en_stop = set(nltk.corpus.stopwords.words("english"))
    tokens = tokenize(text)
    tokens = [token for token in tokens if len(token) > 4]
    tokens = [token for token in tokens if token not in en_stop]
    tokens = [get_lemma2(token) for token in tokens]
    return tokens


def preprocess2(text: str) -> [str]:
    """Same as preprocess but also removes adjectives, pronomes, conjunctions, etc."""
    nlp = en_core_web_md.load()
    removal = [
        "ADV",
        "PRON",
        "CCONJ",
        "PUNCT",
        "PART",
        "DET",
        "ADP",
        "SPACE",
        "NUM",
        "SYM",
    ]
    tokens = []
    for token in nlp(text):
        if token.pos_ not in removal and not token.is_stop and token.is_alpha and len(token) >= MIN_WORD_LENGTH:
            tokens.append(token.lemma_.lower())
    return tokens


def get_ngrams(text, n):
    n_grams = ngrams(word_tokenize(text), n)
    return [' '.join(grams) for grams in n_grams]


def text_to_ngrams(all_texts, n, min_size=5):
    bigrams = []
    articles = [" ".join(text) for text in all_texts]
    for article in articles:
        bigrams += list(map(lambda x: x[0], list(filter(lambda x: x[1]
                        >= min_size, Counter(get_ngrams(article, n)).most_common()))))

    # bigrams = list(
    #     filter(lambda x: 'package' not in x and 'document' not in x, bigrams))
    bigrams = list(map(lambda x: x[0], (list(
        filter(lambda x: x[1] >= min_size, Counter(bigrams).most_common())))))
    return bigrams


def flatten(array: [str]) -> str:
    """Flattens a list of strings recursively into a string"""
    if isinstance(array, str):
        return array
    if len(array) == 0:
        return ""
    elif len(array) == 1:
        return array[0]
    else:
        return array[0] + " " + flatten(array[1:])
