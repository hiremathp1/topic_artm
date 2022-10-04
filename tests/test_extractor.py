from parser import parsefile
from topiclib import TopicExtractor


def test_extractor():
    def vect(file: str, *args):
        t = TopicExtractor(parsefile(file))
        assert t.count().most_common(20) == args[0]
        assert t.count_vectorizer(2).most_common(20) == args[1]


    vect("samples/number_system.json",
        [('number', 26), ('natural number', 18), ('number natural number', 13), ('natural number natural', 12), ('rational number', 12), ('multiplication', 11), ('property', 11), ('number rational number', 10), ('equal', 10), ('example', 9), ('give', 9), ('addition', 8), ('communicative associative property', 7), ('associative property respect', 7), ('rational number rational', 7), ('subtraction', 7), ('natural number example', 6), ('rational number close', 6), ('call', 6), ('mean', 6)],
        [('natural number', 49), ('rational number', 40), ('number natural', 13), ('number close', 11), ('associative property', 11)],
    )
    vect('samples/Basic Math - Lesson 1 - Complex Numbers.json',
        [('number', 11), ('complex number', 4), ('real', 4), ('negative', 4), ('number line', 3), ('square root', 3), ('imaginary number', 3), ('number real', 3), ('imagine number', 3), ('line', 3), ('root', 3), ('case', 3), ('example', 3), ('number number', 2), ('low case', 2), ('yeah', 2), ('inside', 2), ('mention', 2), ('like', 2), ('little', 2)],
        [('complex number', 4), ('number line', 3), ('imaginary number', 3), ('number real', 3), ('imagine number', 3)]
    )
