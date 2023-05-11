"""
Pipeline for CONLL-U formatting
"""
from pathlib import Path
from typing import List
import pymystem3
import pymorphy2
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
            json_indices = map(get_article_id_from_filepath, self.json_files)
            txt_indices = map(get_article_id_from_filepath, self.txt_files)
        except ValueError:
            raise InconsistentDatasetError('files have no IDs in their names')
        if list(range(1, len_json+1)) != sorted(json_indices) or \
                list(range(1, len_txt+1)) != sorted(txt_indices):
            raise InconsistentDatasetError("files' IDs contain slips")

    def _scan_dataset(self) -> None:
        """
        Register each dataset entry
        """
        for file in self.txt_files:
            idx = get_article_id_from_filepath(file)
            article = from_raw(file)
            article.url = file.name
            self._storage[idx] = article

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
        position = str(self._position)
        lemma = self._morphological_parameters.lemma
        pos = self._morphological_parameters.pos
        xpos = '_'
        feats = self._morphological_parameters.tags \
            if include_morphological_tags else '_'
        head = '0'
        deprel = 'root'
        deps = '_'
        misc = '_'
        return '\t'.join([position, self._text, lemma, pos,
                          xpos, feats, head, deprel, deps, misc])

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
        sent_id = f'# sent_id = {self._position}'
        text = f'# text = {self._text}'
        tokens = self._format_tokens(include_morphological_tags)
        return '\n'.join([sent_id, text, tokens]) + '\n'

    def get_cleaned_sentence(self) -> str:
        """
        Returns the lowercase representation of the sentence
        """
        sentence_list = [token.get_cleaned()
                         for token in self._tokens
                         if token.get_cleaned()]
        return ' '.join(sentence_list)

    def get_tokens(self) -> list[ConlluToken]:
        """
        Returns sentences from ConlluSentence
        """
        return self._tokens



class MystemTagConverter(TagConverter):
    """
    Mystem Tag Converter
    """

    def convert_morphological_tags(self, tags: str) -> str:  # type: ignore
        """
        Converts the Mystem tags into the UD format
        """
        part_of_speech = self.convert_pos(re.findall(r'[A-Z]+', tags)[0])
        gramm_categories = {
            'NOUN': [self.gender, self.animacy, self.case, self.number],
            'ADJ': [self.gender, self.animacy, self.case, self.number],
            'VERB': [self.tense, self.number, self.gender],
            'PRON': [self.number, self.case],
            'NUM': [self.gender, self.case, self.animacy]
        }
        necessary_tags = tags.split('|')[0]
        tags_list = re.findall(r'[а-я]+', necessary_tags)
        ud_tags_list = []
        if part_of_speech not in gramm_categories:
            return '_'
        for categ in gramm_categories[part_of_speech]:
            ud_tags = [f'{categ}={self._tag_mapping[categ][tag]}'
                       for tag in tags_list
                       if tag in self._tag_mapping[categ]]
            ud_tags_list.extend(ud_tags)
        return '|'.join(sorted(ud_tags_list))


    def convert_pos(self, tags: str) -> str:  # type: ignore
        """
        Extracts and converts the POS from the Mystem tags into the UD format
        """
        pos = re.findall(r'\w+', tags)[0]
        return self._tag_mapping[self.pos][pos]


class OpenCorporaTagConverter(TagConverter):
    """
    OpenCorpora Tag Converter
    """

    def convert_pos(self, tags: OpencorporaTagProtocol) -> str:  # type: ignore
        """
        Extracts and converts POS from the OpenCorpora tags into the UD format
        """
        return self._tag_mapping[self.pos][tags.POS] if tags.POS else 'X'

    def convert_morphological_tags(self, tags: OpencorporaTagProtocol) -> str:  # type: ignore
        """
        Converts the OpenCorpora tags into the UD format
        """
        gramm_categories = {
            'NOUN': [self.gender, self.animacy, self.case, self.number],
                            'ADJ': [self.gender, self.animacy, self.case, self.number],
                            'VERB': [self.tense, self.number, self.gender],
                            'PRON': [self.number, self.case],
                            'NUM': [self.gender, self.case, self.animacy]
        }
        oc_to_ud = {
            self.gender: tags.gender,
            self.case: tags.case,
            self.animacy: tags.animacy,
            self.number: tags.number,
            self.tense: tags.tense
        }
        pos = self.convert_pos(tags)
        if pos not in gramm_categories:
            return '_'
        ud_tags_list = [f'{categ}={self._tag_mapping[categ][oc_to_ud[categ]]}'
                        for categ in gramm_categories[pos]
                        if oc_to_ud[categ]]
        return '|'.join(sorted(ud_tags_list))


class MorphologicalAnalysisPipeline:
    """
    Preprocesses and morphologically annotates sentences into the CONLL-U format
    """

    def __init__(self, corpus_manager: CorpusManager):
        """
        Initializes MorphologicalAnalysisPipeline
        """
        self._corpus = corpus_manager
        mapping_file = Path(__file__).parent / 'data' / 'mystem_tags_mapping.json'
        self._tag_converter = MystemTagConverter(mapping_file)
        self._analyzer = pymystem3.Mystem()

    def _process(self, text: str) -> List[ConlluSentence]:
        """
        Returns the text representation as the list of ConlluSentence
        """
        sentences = split_by_sentence(text)
        conllu_sentences = []
        for idx, sent in enumerate(sentences):
            sent_analyzed = self._analyzer.analyze(sent)
            conllu_wordlist = []
            index = 1
            for word in sent_analyzed:
                if 'analysis' in word and word['analysis']:
                    pos = self._tag_converter.convert_pos(word['analysis'][0]['gr'])
                elif patterns := re.findall(r'[A-Za-z]+', word['text']):
                    pos_tag = 'X'
                elif patterns := re.findall(r'\d+', word['text']):
                    pos_tag = 'NUM'
                elif patterns := re.findall(r'[.!?]', word['text'].replace(' ', '')):
                    pos_tag = 'PUNCT'
                else:
                    continue
                conllu_token = ConlluToken(word['text']) if word['text'] else ConlluToken(patterns[0].replace(' ', ''))
                conllu_token.set_position(index)
                index += 1
                if 'analysis' in word and word['analysis']:
                    morph_tags = self._tag_converter.convert_morphological_tags(word['analysis'][0]['gr'])
                    token = MorphologicalTokenDTO(word['analysis'][0]['lex'], pos, morph_tags)
                else:
                    token = MorphologicalTokenDTO(patterns[0].replace(' ', ''), pos_tag, '_')
                conllu_token.set_morphological_parameters(token)
                conllu_wordlist.append(conllu_token)
            conllu_sentences.append(ConlluSentence(idx, sent, conllu_wordlist))
        return conllu_sentences

    def run(self) -> None:
        """
        Performs basic preprocessing and writes processed text to files
        """
        articles = self._corpus.get_articles()
        for article in articles.values():
            sentences = self._process(article.text)
            article.set_conllu_sentences(sentences)
            to_cleaned(article)
            to_conllu(article)
            to_conllu(article, include_morphological_tags=True)


class AdvancedMorphologicalAnalysisPipeline(MorphologicalAnalysisPipeline):
    """
    Preprocesses and morphologically annotates sentences into the CONLL-U format
    """

    def __init__(self, corpus_manager: CorpusManager):
        """
        Initializes MorphologicalAnalysisPipeline
        """
        super().__init__(corpus_manager)
        mapping_file = Path(__file__).parent / 'data' / 'opencorpora_tags_mapping.json'
        self._backup_tag_converter = OpenCorporaTagConverter(mapping_file)
        self._backup_analyzer = pymorphy2.MorphAnalyzer()

    def _process(self, text: str) -> List[ConlluSentence]:
        """
        Returns the text representation as the list of ConlluSentence
        """
        sentences = split_by_sentence(text)
        conllu_sentences = []
        for idx, sent in enumerate(sentences):
            sent_analyzed = self._analyzer.analyze(sent)
            conllu_wordlist = []
            index = 1
            for word in sent_analyzed:
                if 'analysis' in word and word['analysis']:
                    pos = self._tag_converter.convert_pos(word['analysis'][0]['gr'])
                elif patterns := re.findall(r'[A-Za-z]+', word['text']):
                    pos_tag = 'X'
                elif patterns := re.findall(r'\d+', word['text']):
                    pos_tag = 'NUM'
                elif patterns := re.findall(r'[.!?]', word['text'].replace(' ', '')):
                    pos_tag = 'PUNCT'
                else:
                    continue
                if 'analysis' in word and word['analysis']:
                    if pos == 'NOUN':
                        oc_tag = self._backup_analyzer.tag(word['text'])[0]
                        pos_tag = self._backup_tag_converter.convert_pos(oc_tag)
                        morph_tag = self._backup_tag_converter.convert_morphological_tags(oc_tag)
                        token = MorphologicalTokenDTO(
                            self._backup_analyzer.normal_forms(word['text'])[0], pos_tag, morph_tag)
                    else:
                        morph_tag = self._tag_converter.convert_morphological_tags(word['analysis'][0]['gr'])
                        token = MorphologicalTokenDTO(word['analysis'][0]['lex'], pos, morph_tag)
                else:
                    token = MorphologicalTokenDTO(patterns[0].replace(' ', ''), pos_tag, '_')
                conllu_token = ConlluToken(word['text']) if word['text'] else ConlluToken(patterns[0])
                conllu_token.set_position(index)
                index += 1
                conllu_token.set_morphological_parameters(token)
                conllu_wordlist.append(conllu_token)
            conllu_sentences.append(ConlluSentence(idx, sent, conllu_wordlist))
        return conllu_sentences

    def run(self) -> None:
        """
        Performs basic preprocessing and writes processed text to files
        """
        articles = self._corpus.get_articles()
        for article in articles.values():
            sentences = self._process(article.text)
            article.set_conllu_sentences(sentences)
            to_conllu(article,
                      include_morphological_tags=True,
                      include_pymorphy_tags=True)


def main() -> None:
    """
    Entrypoint for pipeline module
    """
    manager = CorpusManager(ASSETS_PATH)
    pipeline = MorphologicalAnalysisPipeline(manager)
    pipeline.run()
    manager = CorpusManager(ASSETS_PATH)
    adv_pipeline = AdvancedMorphologicalAnalysisPipeline(manager)
    adv_pipeline.run()



if __name__ == "__main__":
    main()
