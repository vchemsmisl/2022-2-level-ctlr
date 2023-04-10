"""
Crawler implementation
"""
from typing import Pattern, Union
from core_utils.config_dto import ConfigDTO
from core_utils.article.article import Article
from core_utils.article.io import to_raw, to_meta
from core_utils import constants
from pathlib import Path
import requests, json, re, shutil
from bs4 import BeautifulSoup
import datetime

class IncorrectSeedURLError(TypeError):
    pass
class NumberOfArticlesOutOfRangeError(Exception):
    pass
class IncorrectNumberOfArticlesError(Exception):
    pass
class IncorrectHeadersError(Exception):
    pass
class IncorrectEncodingError(Exception):
    pass
class IncorrectTimeoutError(Exception):
    pass
class IncorrectVerifyError(Exception):
    pass

class Config:
    """
    Unpacks and validates configurations
    """

    def __init__(self, path_to_config: Path) -> None:
        """
        Initializes an instance of the Config class
        """
        self.path_to_config = path_to_config
        self._validate_config_content()
        self.config = Config._extract_config_content(self)

        self._seed_urls = self.config.seed_urls
        self._num_articles = self.config.total_articles
        self._headers = self.config.headers
        self._encoding = self.config.encoding
        self._timeout = self.config.timeout
        self._should_verify_certificate = self.config.should_verify_certificate
        self._headless_mode = self.config.headless_mode

    def _extract_config_content(self) -> ConfigDTO:
        """
        Returns config values
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as path:
            self.config_dict = json.load(path)
        return ConfigDTO(self.config_dict['seed_urls'],
                         self.config_dict['total_articles_to_find_and_parse'],
                                self.config_dict['headers'],
                                self.config_dict['encoding'],
                                self.config_dict['timeout'],
                                self.config_dict['should_verify_certificate'],
                                self.config_dict['headless_mode'])

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters
        are not corrupt
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as path:
            self.config_dict = json.load(path)
        if not isinstance(self.config_dict['seed_urls'], list):
            raise IncorrectSeedURLError('seed URL is not a list')
        regex = re.compile(r'https?://w?w?w?.')
        for url in self.config_dict['seed_urls']:
            if not isinstance(url, str):
                raise IncorrectSeedURLError('seed URL is not str')
            if not re.match(regex, url):
                raise IncorrectSeedURLError('seed URL does not match standard pattern "https?://w?w?w?."')
        if not isinstance(self.config_dict['total_articles_to_find_and_parse'], int) or \
                self.config_dict['total_articles_to_find_and_parse'] <= 0:
            raise IncorrectNumberOfArticlesError('total number of articles to parse is not integer')
        if not 1 <= self.config_dict['total_articles_to_find_and_parse'] <= 150:
            raise NumberOfArticlesOutOfRangeError('total number of articles is out of range from 1 to 150')
        if not isinstance(self.config_dict['headers'], dict):
            raise IncorrectHeadersError('headers are not in a form of dictionary')
        if not isinstance(self.config_dict['encoding'], str):
            raise IncorrectEncodingError('encoding must be specified as a string')
        if not isinstance(self.config_dict['timeout'], int) or not 0 <= self.config_dict['timeout'] <= 60:
            raise IncorrectTimeoutError('timeout value must be a positive integer less than 60')
        if not isinstance(self.config_dict['should_verify_certificate'], bool):
            raise IncorrectVerifyError('verify certificate value must either be True or False')
        if not isinstance(self.config_dict['headless_mode'], bool):
            raise IncorrectVerifyError('headless mode value must either be True or False')

    def get_seed_urls(self) -> list[str]:
        """
        Retrieve seed urls
        """
        return self._seed_urls

    def get_num_articles(self) -> int:
        """
        Retrieve total number of articles to scrape
        """
        return self._num_articles

    def get_headers(self) -> dict[str, str]:
        """
        Retrieve headers to use during requesting
        """
        return self._headers

    def get_encoding(self) -> str:
        """
        Retrieve encoding to use during parsing
        """
        return self._encoding

    def get_timeout(self) -> int:
        """
        Retrieve number of seconds to wait for response
        """
        return self._timeout

    def get_verify_certificate(self) -> bool:
        """
        Retrieve whether to verify certificate
        """
        return self._should_verify_certificate

    def get_headless_mode(self) -> bool:
        """
        Retrieve whether to use headless mode
        """
        return self._headless_mode


def make_request(url: str, config: Config) -> requests.models.Response:
    """
    Delivers a response from a request
    with given configuration
    """
    return requests.get(url, headers=config.get_headers())


class Crawler:
    """
    Crawler implementation
    """

    url_pattern: Union[Pattern, str]

    def __init__(self, config: Config) -> None:
        """
        Initializes an instance of the Crawler class
        """
        self.config = config
        self.urls = []
        self._seed_urls = self.config.get_seed_urls()


    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Finds and retrieves URL from HTML
        """
        return article_bs.get('href')

    def find_articles(self) -> None:
        """
        Finds articles
        """
        num_arts = self.config.get_num_articles()
        for url in self._seed_urls:
            response = make_request(f'{url}?per-page={num_arts}', self.config)
            if response.status_code != 200:
                continue
            main_bs = BeautifulSoup(response.text, 'lxml')
            feed_lines = main_bs.find_all('a', {'class': 'd-block mb-0'})
            for line in feed_lines[:num_arts]:
                self.urls.append(self._extract_url(line))

        # WAS JUST TRYING ANOTHER WAY OF DYNAMIC SITE CRAWLING, I'LL DELETE IT LATER
        # art_num = 0
        # num_feed_lines = 0
        # for url in self._seed_urls:
        #     while num_feed_lines <= self.config.get_num_articles():
        #         self.driver.get(url)
        #         self.driver.implicitly_wait(10)
        #         button = wait.WebDriverWait(self.driver, 10).until(
        #             expected_conditions.presence_of_element_located((By.CLASS_NAME,
        #                  "btn btn-show-more w-100 font-weight-bold")))
                # button = [button for button in self.driver.find_elements(By.CLASS_NAME,
                #          "btn btn-show-more w-100 font-weight-bold")][0]
                # button.click()
                # main_bs = BeautifulSoup(self.driver.page_source, 'lxml')
                # feed_lines = main_bs.find_all('a', {'class': 'd-block mb-0'})
                # button_find = main_bs.find_all('a', {'class': 'btn btn-show-more w-100 font-weight-bold'})[0]
                # print(button_find)
            #     num_feed_lines += len(feed_lines)
            # feed_lines += feed_lines[:self.config.get_num_articles()]
            # for line in feed_lines:
            #     self.urls.append(self._extract_url(line))
                # art_num += 1
                # if art_num >= self.config.get_num_articles():
                #     break

    def get_search_urls(self) -> list:
        """
        Returns seed_urls param
        """
        return self._seed_urls


class HTMLParser:
    """
    ArticleParser implementation
    """

    def __init__(self, full_url: str, article_id: int, config: Config) -> None:
        """
        Initializes an instance of the HTMLParser class
        """
        self.full_url = full_url
        self.article_id = article_id
        self.config = config
        self.article = Article(full_url, article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Finds text of article
        """
        article = article_soup.find_all('div', {'itemprop': 'articleBody'})[0]
        article_list = article.find_all('p')
        paragraphs = [par.text for par in article_list]
        self.article.text = '\n'.join(paragraphs)

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Finds meta information of article
        """
        article = article_soup.find_all('div', {'itemprop': 'headline'})[0]
        article_title = article.find_all('h1')[0]
        self.article.title = article_title.text
        article_authors = article_soup.find_all('span', {'itemprop': 'author'})[0]
        authors = article_authors.find_all('span', {'itemprop': 'name'})
        if authors:
            self.article.author = [author.text for author in authors]
        else:
            self.article.author = ['NOT FOUND']
        try:
            article_tags = article_soup.find_all('ul', {'itemprop': 'keywords'})[0]
            article_tags_li = article_tags.find_all('li')
            self.article.topics = [tag.find_all('a')[0].text.replace('"', '&quot;') for tag in article_tags_li]
            print(self.article.topics)
        except IndexError:
            self.article.topics = []
        article_date = article_soup.find_all('span', {'class': 'news-datetime mb-10 mr-20'})[0]
        self.article.date = self.unify_date_format(article_date.text)

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unifies date format
        """
        mounths_dict = {
            'января': 'January',
            'февраля': 'February',
            'марта': 'March',
            'апреля': 'April',
            'мая': 'May',
            'июня': 'June',
            'июля': 'July',
            'августа': 'August',
            'сентября': 'September',
            'октября': 'October',
            'ноября': 'November',
            'декабря': 'December'
        }
        date_list = date_str.split()
        date_list[1] = mounths_dict[date_list[1]]
        date_str = ' '.join(date_list)
        return datetime.datetime.strptime(date_str, '%d %B %Y г. %H:%M')

    def parse(self) -> Union[Article, bool, list]:
        """
        Parses each article
        """
        response = requests.get(self.full_url)
        bs = BeautifulSoup(response.text, 'lxml')
        self._fill_article_with_text(bs)
        self._fill_article_with_meta_information(bs)
        return self.article


def prepare_environment(base_path: Union[Path, str]) -> None:
    """
    Creates ASSETS_PATH folder if no created and removes existing folder
    """
    if base_path.exists():
        shutil.rmtree(base_path)
    new_path = Path(__file__).parent / base_path
    new_path.mkdir(exist_ok=True, parents=True)


def main() -> None:
    """
    Entrypoint for scrapper module
    """
    prepare_environment(constants.ASSETS_PATH)
    configuration = Config(path_to_config=constants.CRAWLER_CONFIG_PATH)
    crawler = Crawler(config=configuration)
    crawler.find_articles()
    search_urls = crawler.urls
    for i, full_url in enumerate(search_urls, 1):
        parser = HTMLParser(full_url=full_url, article_id=i, config=configuration)
        article = parser.parse()
        to_raw(article)
        to_meta(article)


if __name__ == "__main__":
    main()
