# https://aclanthology.org/P15-2057.pdf
# https://github.com/harangju/wikinet
# https://radimrehurek.com/gensim/corpora/wikicorpus.html#module-gensim.corpora.wikicorpus

import wikinet as wiki

path_xml = "/home/matheus/Jobs/topic_artm/dumps/enwiki-latest-pages-articles-multistream.xml.bz2"
path_index = "/home/matheus/Jobs/topic_artm/dumps/enwiki-latest-pages-articles-multistream-index.txt.bz2"

# Reading zipped Wikipedia XML dumps

dump = wiki.Dump(path_xml, path_index)
page = dump.load_page('Science')

# Then, you can view the page and information about the page.

print(page)
print(dump.page)
print(dump.links)  # all links
print(dump.article_links)  # just links to articles
print(dump.years)  # years in article (intro & history sections)

# Creating a network of Wikipedia articles

network = wiki.Net.build_graph(
    name='my network', dump=dump, nodes=['Science', 'Mathematics', 'Philosophy']
)

# Optionally, for edge weights with cosine distance between tf-idf vectors of articles

network = wiki.Net.build_graph(
    name='my network', dump=dump, nodes=['Science', 'Mathematics', 'Philosophy'],
    model=tfidf,  # gensim.models
    dct=dct,  # gensim.corpora.Dictionary
)
