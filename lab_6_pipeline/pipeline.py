"""
Pipeline for CONLL-U formatting
"""
import json
from pathlib import Path
from typing import List
import pymystem3
import json
import re

from core_utils.article.article import SentenceProtocol, \
    get_article_id_from_filepath, split_by_sentence
from core_utils.article.ud import OpencorporaTagProtocol, TagConverter
from core_utils.constants import ASSETS_PATH
from core_utils.article.io import from_raw, to_cleaned, to_conllu

class InconsistentDatasetError(Exception):
    """
    Raised if IDs contain slips, number of meta
    and raw files is not equal, files are empty
    """

class EmptyDirectoryError(Exception):
    """
    Raised if directory is empty
    """

# pylint: disable=too-few-public-methods
class CorpusManager:
    """
    Works with articles and stores them
    """

    def __init__(self, path_to_raw_txt_data: Path):
        """
        Initializes CorpusManager
        """
        self.path_to_raw_txt_data = path_to_raw_txt_data
        self.json_files = list(self.path_to_raw_txt_data.glob('*_meta.json'))
        self.txt_files = list(self.path_to_raw_txt_data.glob('*_raw.txt'))
        self._validate_dataset()
        self._storage = {}
        self._scan_dataset()

    def _validate_dataset(self) -> None:
        """
        Validates folder with assets
        """
        if not self.path_to_raw_txt_data.exists():
            raise FileNotFoundError('file does not exist')
        if not self.path_to_raw_txt_data.is_dir():
            raise NotADirectoryError('path does not lead to directory')
        if not self.json_files or not self.txt_files:
            raise EmptyDirectoryError('directory is empty')
        len_json, len_txt = len(self.json_files), len(self.txt_files)
        if len_json != len_txt:
            raise InconsistentDatasetError('number of meta and raw files is not equal')
        for json, txt in zip(self.json_files, self.txt_files):
            if not json.stat().st_size or not txt.stat().st_size:
                raise InconsistentDatasetError("files are empty")
        try:
            json_max = max(map(get_article_id_from_filepath, self.json_files))
            txt_max = max(map(get_article_id_from_filepath, self.txt_files))
        except ValueError:
            raise InconsistentDatasetError('files have no IDs in their names')
        if len_json != json_max != txt_max:
            raise InconsistentDatasetError("files' IDs contain slips")

    def _scan_dataset(self) -> None:
        """
        Register each dataset entry
        """
        for file in self.txt_files:
            idx = get_article_id_from_filepath(file)
            self._storage[idx] = from_raw(file)

    def get_articles(self) -> dict:
        """
        Returns storage params
        """
        return self._storage


class MorphologicalTokenDTO:
    """
    Stores morphological parameters for each token
    """

    def __init__(self, lemma: str = "", pos: str = "", tags: str = ""):
        """
        Initializes MorphologicalTokenDTO
        """
        self.lemma = lemma
        self.pos = pos
        self.tags = tags


class ConlluToken:
    """
    Representation of the CONLL-U Token
    """

    def __init__(self, text: str):
        """
        Initializes ConlluToken
        """
        self._text = text
        self._position = 0
        self._morphological_parameters = MorphologicalTokenDTO()

    def set_position(self, position: int) -> None:
        """
        Stores token's position in a sentence
        """
        self._position = position

    def set_morphological_parameters(self, parameters: MorphologicalTokenDTO) -> None:
        """
        Stores the morphological parameters
        """
        self._morphological_parameters = parameters

    def get_morphological_parameters(self) -> MorphologicalTokenDTO:
        """
        Returns morphological parameters from ConlluToken
        """
        return self._morphological_parameters

    def get_conllu_text(self, include_morphological_tags: bool) -> str:
        """
        String representation of the token for conllu files
        """
        if not include_morphological_tags:
            return f'{self._position}\t{self._text}\t' \
               f'{self._morphological_parameters.lemma}\t' \
               f'{self._morphological_parameters.pos}\t' \
               f'_\t_\t0\troot\t_\t_'
        return ''

    def get_cleaned(self) -> str:
        """
        Returns lowercase original form of a token
        """
        return re.sub(r'[^\w\s]', '',  self._text.lower())


class ConlluSentence(SentenceProtocol):
    """
    Representation of a sentence in the CONLL-U format
    """

    def __init__(self, position: int, text: str, tokens: list[ConlluToken]):
        """
        Initializes ConlluSentence
        """
        self._position = position
        self._text = text
        self._tokens = tokens

    def _format_tokens(self, include_morphological_tags: bool) -> str:
        """
        Formats each token in a sentence
        to a token for a conllu file
        """
        return '\n'.join([token.get_conllu_text(include_morphological_tags) for token in self._tokens])

    def get_conllu_text(self, include_morphological_tags: bool) -> str:
        """
        Creates string representation of the sentence
        """
        return f'# sent_id = {self._position}\n' \
               f'# text = {self._text}\n' \
               f'{self._format_tokens(include_morphological_tags)}\n'

    def get_cleaned_sentence(self) -> str:
        """
        Returns the lowercase representation of the sentence
        """
        sentence_list = [token.get_cleaned() for token in self._tokens
                         if token.get_cleaned()]
        return ' '.join(sentence_list)

    def get_tokens(self) -> list[ConlluToken]:
        """
        Returns sentences from ConlluSentence
        """



class MystemTagConverter(TagConverter):
    """
    Mystem Tag Converter
    """

    def convert_morphological_tags(self, tags: str) -> str:  # type: ignore
        """
        Converts the Mystem tags into the UD format
        """

    def convert_pos(self, tags: str) -> str:  # type: ignore
        """
        Extracts and converts the POS from the Mystem tags into the UD format
        """
        return self._tag_mapping['POS'][tags]


class OpenCorporaTagConverter(TagConverter):
    """
    OpenCorpora Tag Converter
    """

    def convert_pos(self, tags: OpencorporaTagProtocol) -> str:  # type: ignore
        """
        Extracts and converts POS from the OpenCorpora tags into the UD format
        """

    def convert_morphological_tags(self, tags: OpencorporaTagProtocol) -> str:  # type: ignore
        """
        Converts the OpenCorpora tags into the UD format
        """


class MorphologicalAnalysisPipeline:
    """
    Preprocesses and morphologically annotates sentences into the CONLL-U format
    """

    def __init__(self, corpus_manager: CorpusManager):
        """
        Initializes MorphologicalAnalysisPipeline
        """
        self._corpus = corpus_manager
        mapping_dir = Path(__file__).parent / 'data'
        if not mapping_dir.exists():
            mapping_dir.mkdir(parents=True)
        mapping_file = mapping_dir / 'mystem_tags_mapping.json'
        if not mapping_file.exists():
            mapping_file.touch()
        if not mapping_file.stat().st_size:
            ud_mapping = {'POS': {'S': 'NOUN',
                                  'SPRO': 'PRON',
                                  'A': 'ADJ',
                                  'ANUM': 'ADJ',
                                  'APRO': 'ADJ',
                                  'COM': 'ADJ',
                                  'V': 'VERB',
                                  'NUM': 'NUM',
                                  'ADV': 'ADV',
                                  'ADVPRO': 'ADV',
                                  'PR': 'ADP',
                                  'CONJ': 'CCONJ',
                                  'PART': 'PART',
                                  'INTJ': 'INTJ'}}
            with open(mapping_file, 'w', encoding='utf-8') as json_file:
                json.dump(ud_mapping, json_file)
        self._tag_converter = MystemTagConverter(mapping_file)

    def _process(self, text: str) -> List[ConlluSentence]:
        """
        Returns the text representation as the list of ConlluSentence
        """
        sentences = split_by_sentence(text)
        conllu_sentences = []
        for idx, sent in enumerate(sentences):
            sent_analyzed = pymystem3.Mystem().analyze(sent)
            conllu_wordlist = []
            index = 1
            for word in sent_analyzed:
                try:
                    tags_list = re.findall(r'\w+', word['analysis'][0]['gr'])
                except KeyError:
                    if re.findall(r'\s+', word['text']):
                        continue
                    conllu_token = ConlluToken(word['text'])
                    conllu_token.set_position(index)
                    index += 1
                    if patterns := re.findall(r'\d+', word['text']):
                        conllu_token.set_morphological_parameters(
                            MorphologicalTokenDTO(patterns[0], 'NUM'))
                    elif patterns := re.findall(r'\.', word['text']):
                        conllu_token.set_morphological_parameters(
                            MorphologicalTokenDTO(patterns[0], 'PUNCT'))
                    conllu_wordlist.append(conllu_token)
                    continue
                except IndexError:
                    if patterns := re.findall(r'[A-Za-z]+', word['text']):
                        conllu_token = ConlluToken(patterns[0])
                        conllu_token.set_position(index)
                        index += 1
                        conllu_token.set_morphological_parameters(
                            MorphologicalTokenDTO(patterns[0], 'X'))
                        conllu_wordlist.append(conllu_token)
                        continue
                    continue
                ud_tag = self._tag_converter.convert_pos(tags_list[0])
                conllu_token = ConlluToken(word['text'])
                conllu_token.set_position(index)
                index += 1
                conllu_token.set_morphological_parameters(
                    MorphologicalTokenDTO(word['analysis'][0]['lex'], ud_tag))
                conllu_wordlist.append(conllu_token)
            conllu_sentences.append(ConlluSentence(idx, sent, conllu_wordlist))
        return conllu_sentences

    def run(self) -> None:
        """
        Performs basic preprocessing and writes processed text to files
        """
        articles = self._corpus.get_articles()
        for id in articles:
            sentences = self._process(articles[id].text)
            articles[id].set_conllu_sentences(sentences)
            to_cleaned(articles[id])
            to_conllu(articles[id])


class AdvancedMorphologicalAnalysisPipeline(MorphologicalAnalysisPipeline):
    """
    Preprocesses and morphologically annotates sentences into the CONLL-U format
    """

    def __init__(self, corpus_manager: CorpusManager):
        """
        Initializes MorphologicalAnalysisPipeline
        """

    def _process(self, text: str) -> List[ConlluSentence]:
        """
        Returns the text representation as the list of ConlluSentence
        """

    def run(self) -> None:
        """
        Performs basic preprocessing and writes processed text to files
        """


def main() -> None:
    """
    Entrypoint for pipeline module
    """
    manager = CorpusManager(ASSETS_PATH)
    pipeline = MorphologicalAnalysisPipeline(manager)
    pipeline.run()


if __name__ == "__main__":
    main()
