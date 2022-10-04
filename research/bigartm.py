# https://towardsdatascience.com/hierarchical-topic-modeling-with-bigartm-library-6f2ff730689f
# https://bigartm.readthedocs.io/en/stable/tutorials/index.html
# https://bigartm.readthedocs.io/en/stable/tutorials/python_userguide/loading_data.html

import artm
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass
from sklearn.feature_extraction.text import CountVectorizer

from parse_json import parsefile
from preprocess import preprocess2, text_to_ngrams

@dataclass
class Topics:
    names: [str]
    vocabulary: np.ndarray
    n_wd: np.ndarray


def get_topics(all_texts, bigrams, n_topics):
    n_wd_bigrams = np.empty((len(bigrams), len(all_texts)))

    for i in range(len(bigrams)):
        for j in range(len(all_texts)):
            n_wd_bigrams[i][j] = all_texts[j].count(bigrams[i])

    max_features = 5
    cv = CountVectorizer(max_features=max_features, stop_words='english')
    n_wd = np.array(cv.fit_transform(all_texts).todense()).T
    vocabulary = cv.get_feature_names()

    n_wd = np.concatenate((n_wd, n_wd_bigrams))
    vocabulary += bigrams
    topic_names = bigrams[:n_topics]
    return Topics(topic_names, vocabulary, n_wd)

def artm_model(topics):
    topic_names, vocabulary, n_wd = topics.names, topics.vocabulary, topics.n_wd
    bv = artm.BatchVectorizer(data_format='bow_n_wd',
                              n_wd=n_wd,
                              vocabulary=vocabulary)
    dictionary = bv.dictionary
    model_artm = artm.ARTM(topic_names=topic_names, cache_theta=True,
                           scores=[
                               artm.PerplexityScore(name='PerplexityScore',
                                                    dictionary=dictionary),
                               artm.SparsityPhiScore(name='SparsityPhiScore'),
                               artm.SparsityThetaScore(
                                   name='SparsityThetaScore'),
                               artm.TopicKernelScore(
                                   name='TopicKernelScore', probability_mass_threshold=0.3),
                               artm.TopTokensScore(
                                   name='TopTokensScore', num_tokens=8),
                           ],
                           regularizers=[
                               artm.SmoothSparseThetaRegularizer(
                                   name='SparseTheta', tau=-0.4),
                               artm.DecorrelatorPhiRegularizer(
                                   name='DecorrelatorPhi', tau=2.5e+5),
                           ])

    model_artm.num_document_passes = 4
    model_artm.initialize(dictionary)
    model_artm.fit_offline(batch_vectorizer=bv, num_collection_passes=20)
    return model_artm


def print_measures(model_artm):
    print('Sparsity Phi ARTM:{}'.format(
        model_artm.score_tracker['SparsityPhiScore'].last_value))
    print('Sparsity Theta ARTM:{}'.format(
        model_artm.score_tracker['SparsityThetaScore'].last_value))
    print('Perplexity ARTM: {}'.format(
        model_artm.score_tracker['PerplexityScore'].last_value))

    ig, axs = plt.subplots(1, 3, figsize=(30, 5))

    for idx, score, y_label in zip(range(3), ['PerplexityScore', 'SparsityPhiScore', 'SparsityThetaScore'], ['ARTM perplexity', 'ARTM Phi sparsity', 'ARTM Theta sparsity']):
        axs[idx].plot(range(model_artm.num_phi_updates),
                      model_artm.score_tracker[score].value, 'r--', linewidth=2)
        axs[idx].set_xlabel('Iterations count')
        axs[idx].set_ylabel(y_label)
        axs[idx].grid(True)


def test():
    text = parsefile("samples/number_system.json")
    tokens = preprocess2(text)
    bigrams = text_to_ngrams([tokens], 1, 0)
    topics = get_topics(tokens, bigrams, 10)
    print(topics.names)
    bigrams = text_to_ngrams([tokens], 2, 0)
    topics = get_topics(tokens, bigrams, 10)
    print(topics.names)
    bigrams = text_to_ngrams([tokens], 3, 0)
    topics = get_topics(tokens, bigrams, 10)
    print(topics.names)
    # model = artm_model(topics)
    # print_measures(model)


if __name__ == "__main__":
    test()
