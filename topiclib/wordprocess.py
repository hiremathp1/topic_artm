# https://towardsdatascience.com/short-text-topic-modelling-lda-vs-gsdmm-20f1db742e14

import gensim
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
from gsdmm import MovieGroupProcess
from wordcloud import WordCloud

from .preprocess import flatten, preprocess2


def gsd(text: [str], n_words=20):
    text_data = []
    tokens = preprocess2(text)
    text_data.append(tokens)
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


def wordcloud(topic_dict, width=600, height=600, limit=100) -> bytes:
    """Returns bytes of wordcloud image"""
    img = WordCloud(background_color='#fcf2ed',
                    width=width,
                    height=height,
                    max_words=limit,
                    colormap='flag').generate_from_frequencies(topic_dict)

    fig, ax = plt.subplots(figsize=[20, 10])
    plt.imshow(img, interpolation='bilinear')
    plt.axis("off")
    b = BytesIO()
    plt.savefig(b, format='png')
    b.seek(0)
    return b.read()
