from .corpus_expansion import IDocumentProvider, provider

from mediawiki import MediaWiki, exceptions


@provider(name="wikipedia")
class WikiCorpus(IDocumentProvider):
    pages = {}
    def __init__(self):
        self.wikipedia = self._gen_wiki()

    def content(self, page: str) -> str:
        return self._wikipage(page).content

    def categories(self, page: str) -> [str]:
        return self._wikipage(page).categories

    def _gen_wiki(self):
        return MediaWiki()

    def _wikisearch(self, query: str) -> [str]:
        return self.wikipedia.search(query)

    def _wikipage(self, title: str):
        if title not in self.pages:
            self.pages[title] = self.wikipedia.page(title)
        return self.pages[title]

    def search(self, search: str) -> [str]:
        pages = self._wikisearch(search)
        for title in pages:
            try:
                # This is so that the exception can be raised
                self._wikipage(title)
                yield title
            except exceptions.DisambiguationError:
                continue
