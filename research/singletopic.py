# https://towardsdatascience.com/short-text-topic-modelling-lda-vs-gsdmm-20f1db742e14

from wordcloud import WordCloud
import matplotlib.pyplot as plt
import gensim
import numpy as np
from parse_json import parsefile
from preprocess import preprocess2, flatten
from gsdmm import MovieGroupProcess


def gsd(text_data: [str], n_words=20):
    dictionary = gensim.corpora.Dictionary(text_data)
    vocab_length = len(dictionary)

    max_topics = int(len(flatten(text_data)) / 10)
    model = MovieGroupProcess(K=max_topics, alpha=0.1, beta=0.3, n_iters=15)
    model.fit(np.array(text_data), vocab_length)

    doc_count = np.array(model.cluster_doc_count)
    top_index = doc_count.argsort()[-15:][-1]

    topic_dict = sorted(model.cluster_word_distribution[top_index].items(
    ), key=lambda k: k[1], reverse=True)[:n_words]

    return {k: v for k, v in topic_dict}

def wordcloud(topic_dict):
    wordcloud = WordCloud(background_color='#fcf2ed',
                          width=1800,
                          height=700,
                          colormap='flag').generate_from_frequencies(topic_dict)

    fig, ax = plt.subplots(figsize=[20, 10])
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()


def test():
    text_data = []
    text = parsefile("samples/number_system.json")
    tokens = preprocess2(text)
    text_data.append(tokens)
    d = gsd(text_data)
    print(d)
    wordcloud(d)


if __name__ == "__main__":
    test()
