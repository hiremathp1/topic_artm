# Model for topic extraction from text
# Author: Praveen Hiremath
# Date: 2022-31-07
#
# This model will preprocess the text and then apply a counter vectorizer for counting the number of times a token appears in a document. The tokens are ngrams. This way, for example, if a word appears alone it is counted separately from when it occurs in bigrams.

from collections import Counter
from copy import deepcopy

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from .preprocess import get_ngrams, preprocess2


def clusterize(points: [int], n_clusters: int = 2) -> [int]:
    """Cluters the points into n_clusters clusters. Returns an array of arrays of numbers"""
    assert n_clusters > 1 and n_clusters <= len(
        points), "n_clusters must be between 2 and len(points)"
    points = sorted(points)
    n_gaps = n_clusters - 1

    # Loop over sorted points computing their differences
    differences = {i: points[i + 1] - points[i]
                   for i in range(len(points) - 1)}
    # Find the biggest n_gaps difference indexes
    biggest_differences = sorted(
        sorted(differences, key=differences.get, reverse=True)[:n_gaps])

    clusters = []
    last = 0
    for i in range(n_gaps):
        new = biggest_differences.pop(0) + 1
        clusters.append(points[last:new])
        last = new
    clusters.append(points[last:])

    return clusters


def filter_low(points: [int]):
    """Filters out low values based on the standard deviation"""
    points = sorted(points)
    for n in range(2, len(points)):
        clusters = clusterize(points, n)
        std1 = 0
        rest = []
        for i, cluster in enumerate(clusters):
            if i == 0:
                std1 = np.std(cluster)
            else:
                rest += cluster
        std2 = np.std(rest)
        if std1 < std2:
            return [clusters[0], rest]
    return [[], points]


def ngram_contains(children_ngram: str, partent_ngram: str) -> bool:
    """Checks if a ngram is contained in another ngram.
    """
    children_ngram = children_ngram.split()
    partent_ngram = partent_ngram.split()
    if len(children_ngram) > len(partent_ngram):
        return False
    for i in range(len(children_ngram)):
        if children_ngram[i] != partent_ngram[i]:
            return False
    return True

# Template for the model
class TopicExtractor:
    def __init__(self, content: str, ngram_range: tuple = (1, 2, 3)):
        """Initialize the model."""
        self.tokens = preprocess2(content)
        self.ngram_range = sorted(ngram_range, reverse=True)
        self.counts = {}
        self.model = None
        self.topics = None
        self.ngram_tokens = {}
        self.ngrams_map = {}

        # Populate ngram tokens for each ngram range
        for n in ngram_range:
            self.ngram_tokens[n] = get_ngrams(" ".join(self.tokens), n)

    def count(self) -> Counter:
        """Compute the total count for each token of ngram_tokens. HashMap implementation.
        Returns a Counter object only with ngrams that repeate more than once.
        """
        self.ngrams_map = {}
        self.counts = {}

        # Loop through higher ngrams to lower ones
        for i, n in enumerate(self.ngram_range):
            counter = Counter(self.ngram_tokens[n])
            # Remove tokens that appear only once
            self.counts[n] = {
                k: c for k, c in counter.items() if c > 1
            }

            # Loop over bigger ngrams than the current one and decrease the counter each time the current ngram
            # is found in a bigger ngram
            for k, c in deepcopy(self.counts[n]).items():
                for bk, bc in self.ngrams_map.items():
                    if ngram_contains(k, bk):
                        self.counts[n][k] -= bc
                    if self.counts[n][k] <= 1:
                        del self.counts[n][k]
                        break

            self.ngrams_map = {**self.ngrams_map, **self.counts[n]}

        self.ngrams_map = Counter(self.ngrams_map)
        return self.ngrams_map

    def count_vectorizer(self, ngram_size: int = 1) -> Counter:
        """Get the counter of the topics for a fixed ngram size. CountVectorizer implementation"""
        max_features = 5
        n = ngram_size
        tokens = self.ngram_tokens[ngram_size]
        cv = CountVectorizer(ngram_range=(n, n),
                             max_features=max_features)
        vec = cv.fit(tokens)
        bag_of_words = vec.transform(tokens)
        sum_words = bag_of_words.sum(axis=0)
        words_freq = [(word, sum_words[0, i])
                      for word, i in vec.vocabulary_.items()]
        words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)
        return Counter({k: v for k, v in words_freq})
