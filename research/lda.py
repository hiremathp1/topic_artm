# https://towardsdatascience.com/topic-modelling-in-python-with-spacy-and-gensim-dc8f7748bdbf
# https://radimrehurek.com/gensim/auto_examples/tutorials/run_word2vec.html#sphx-glr-auto-examples-tutorials-run-word2vec-py

import multiprocessing
from dataclasses import dataclass
import matplotlib.pyplot as plt
import gensim
from gensim import corpora
from gensim.models import CoherenceModel, LdaMulticore

from parse_json import parsefile
from preprocess import preprocess2


@dataclass
class Report:
    model: LdaMulticore
    cv_score: float

    def __repr__(self):
        topics = self.model.print_topics(-1)
        for topic in topics:
            print(topic)


def print_topics(model):
    for idx, topic in model.print_topics(-1):
        print('Topic: {} \nWords: {}'.format(idx, topic))

def lda(text_data: [str], n_topics: int) -> Report:
    dictionary = corpora.Dictionary(text_data)
    # dictionary.filter_extremes(no_below=5, no_above=0.5, keep_n=1000)
    corpus = [dictionary.doc2bow(text) for text in text_data]
    kwargs = {
        # "alpha": "auto",
        # "eta": "auto",
        "corpus": corpus,
        "id2word": dictionary,
        "iterations": 50,
        "num_topics": n_topics,
        "workers": int(multiprocessing.cpu_count() / 2),
        "passes": 15,
        "random_state": 100
    }
    try:
        ldamodel = LdaMulticore(**kwargs)
    except Exception as e:
        print("Falling back to single core processing: " + str(e))
        del kwargs["workers"]
        ldamodel = gensim.models.ldamodel.LdaModel(**kwargs)

    cv = CoherenceModel(model=ldamodel, texts=text_data,
                        corpus=corpus, dictionary=dictionary, coherence='c_v')
    return Report(model=ldamodel, cv_score=cv.get_coherence())


def test():
    text_data = []
    text = parsefile("samples/number_system.json")
    tokens = preprocess2(text)
    # pprint(tokens)
    # return
    text_data.append(tokens)
    reports = []

    # We suppose there can't more more than "total_number_of_words/10"
    max_topics = int(len(tokens) / 10)
    for i in range(1, max_topics):
        reports.append(lda(text_data, i))
    # plt.plot(list(range(1, max_topics)), [report.cv_score for report in reports])
    # plt.xlabel('Number of Topics')
    # plt.ylabel('cv Coherence Score')
    # plt.show()

    print_topics(reports[5].model)


if __name__ == "__main__":
    test()
