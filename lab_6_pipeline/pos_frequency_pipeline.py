"""
Implementation of POSFrequencyPipeline for score ten only.
"""
from typing import Optional
from pathlib import Path
import re
from collections import Counter
from core_utils.article.article import Article, ArtifactType
from lab_6_pipeline.pipeline import ConlluToken, CorpusManager, \
    ConlluSentence, MorphologicalTokenDTO
from core_utils.constants import ASSETS_PATH
from core_utils.article.ud import extract_sentences_from_raw_conllu

class EmptyFileError(Exception):
    """
    Raised when an article file is empty
    """

def from_conllu(path: Path, article: Optional[Article] = None) -> Article:
    """
    Populates the Article abstraction with all information from the conllu file
    """
    with open(path, 'r', encoding='utf-8') as file:
        conllu = file.read()
    article_dict = extract_sentences_from_raw_conllu(conllu)
    conllu_sentences = []
    sentences = []
    for sentence in article_dict:
        wordlist = [_parse_conllu_token(word) for word in sentence['tokens']]
        conllu_sentences.append(ConlluSentence(
            sentence['position'],
            sentence['text'],
            wordlist))
        sentences.append(sentence['text'])
    if not article:
        article = Article(url=None, article_id=re.findall(r'\d+', path.name)[0])
    article.set_conllu_sentences(conllu_sentences)
    return article


def _parse_conllu_token(token_line: str) -> ConlluToken:
    """
    Parses the raw text in the CONLLU format into the CONLL-U token abstraction

    Example:
    '2	произошло	происходить	VERB	_	Gender=Neut|Number=Sing|Tense=Past	0	root	_	_'
    """
    token_features = token_line.split('\t')
    token = ConlluToken(token_features[1])
    token.set_position(int(token_features[0]))
    token.set_morphological_parameters(MorphologicalTokenDTO(
        token_features[2],
        token_features[3],
        token_features[5]
    ))
    return token


# pylint: disable=too-few-public-methods
class POSFrequencyPipeline:
    """
    Counts frequencies of each POS in articles,
    updates meta information and produces graphic report
    """

    def __init__(self, corpus_manager: CorpusManager):
        """
        Initializes PosFrequencyPipeline
        """
        self._manager = corpus_manager

    def run(self) -> None:
        """
        Visualizes the frequencies of each part of speech
        """
        articles = self._manager.get_articles()
        for art in articles:
            if not art.url.stat().st_size:
                raise EmptyFileError('an article file is empty')
            path = art.get_file_path(ArtifactType.FULL_CONLLU)
            art = from_conllu(path, art)
            art.set_pos_info(self._count_frequencies(art))


    def _count_frequencies(self, article: Article) -> dict[str, int]:
        """
        Counts POS frequency in Article
        """
        sentences = article.get_conllu_sentences()
        tokens = []
        for sent in sentences:
            tokens.extend(sent.get_tokens())
        tokens_pos = [token.get_morphological_parameters().pos for token in tokens]
        return Counter(tokens_pos)


def main() -> None:
    """
    Entrypoint for the module
    """
    manager = CorpusManager(ASSETS_PATH)
    pipeline = POSFrequencyPipeline(manager)
    pipeline.run()


if __name__ == "__main__":
    main()
