"""
Crawler implementation
"""
import datetime
import json
import random
import re
import shutil
import time
from pathlib import Path
from typing import Pattern, Union

import requests
from bs4 import BeautifulSoup

from core_utils.article.article import Article
from core_utils.article.io import to_meta, to_raw
from core_utils.config_dto import ConfigDTO
from core_utils.constants import (ASSETS_PATH, CRAWLER_CONFIG_PATH,
                                  NUM_ARTICLES_UPPER_LIMIT,
                                  TIMEOUT_LOWER_LIMIT, TIMEOUT_UPPER_LIMIT)


class IncorrectSeedURLError(TypeError):
    '''
    Raised when seed URLs are in incorrect form
    '''

class NumberOfArticlesOutOfRangeError(Exception):
    '''
    Raised when the number of articles is
    out of range from 1 to 150
    '''

class IncorrectNumberOfArticlesError(Exception):
    '''
    Raised when the number of articles is not int
    '''

class IncorrectHeadersError(Exception):
    '''
    Raised when headers are in incorrect form
    '''

class IncorrectEncodingError(Exception):
    '''
    Raised when encoding is in incorrect form
    '''

class IncorrectTimeoutError(Exception):
    '''
    Raised when timeout is in incorrect form
    '''

class IncorrectVerifyError(Exception):
    '''
    Raise when verify certificate is in incorrect form
    '''


class Config:
    """
    Unpacks and validates configurations
    """

    def __init__(self, path_to_config: Path) -> None:
        """
        Initializes an instance of the Config class
        """
        self.path_to_config = path_to_config
        self.config = Config._extract_config_content(self)
        self._validate_config_content()

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
            config_dict = json.load(path)
        return ConfigDTO(**config_dict)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters
        are not corrupt
        """
        if not isinstance(self.config.seed_urls, list):
            raise IncorrectSeedURLError('seed URL is not a list')
        regex = re.compile(r'https?://')
        for url in self.config.seed_urls:
            if not isinstance(url, str):
                raise IncorrectSeedURLError('seed URL is not str')
            if not re.match(regex, url):
                raise IncorrectSeedURLError('seed URL does not match standard pattern')
        if not isinstance(self.config.total_articles, int) or \
                self.config.total_articles <= 0:
            raise IncorrectNumberOfArticlesError('total number of articles to parse is not integer')
        if not 1 <= self.config.total_articles <= NUM_ARTICLES_UPPER_LIMIT:
            raise NumberOfArticlesOutOfRangeError('total number of articles is out of range')
        if not isinstance(self.config.headers, dict):
            raise IncorrectHeadersError('headers are not in a form of dictionary')
        if not isinstance(self.config.encoding, str):
            raise IncorrectEncodingError('encoding must be specified as a string')
        if not isinstance(self.config.timeout, int) or \
                not TIMEOUT_LOWER_LIMIT <= self.config.timeout <= TIMEOUT_UPPER_LIMIT:
            raise IncorrectTimeoutError('timeout value must be a positive integer less than 60')
        if not isinstance(self.config.should_verify_certificate, bool):
            raise IncorrectVerifyError('verify certificate value must either be True or False')
        if not isinstance(self.config.headless_mode, bool):
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
    time.sleep(random.randint(1, 6))
    response = requests.get(url,
                        headers=config.get_headers(),
                        timeout=config.get_timeout())
    response.encoding = config.get_encoding()
    return response


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
        url: Union[str, list, None] = article_bs.get('href')
        if isinstance(url, str) and \
                'https://www.interfax-russia.ru/volga/news/' in url:
            return url
        return ''

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
        # IT DOESN'T WORK FOR NO APPARENT REASONS...
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
                # button_find = main_bs.find_all('a',
        #               {'class': 'btn btn-show-more w-100 font-weight-bold'})[0]
                # print(button_find)
            #     num_feed_lines += len(feed_lines)
            # feed_lines += feed_lines[:self.config.get_num_articles()]
            # for line in feed_lines:
            #     self.urls.append(self._extract_url(line))

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
        self.article: Article = Article(full_url, article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Finds text of article
        """
        article = article_soup.find('div', {'itemprop': 'articleBody'})
        article_list = article.find_all('p')
        paragraphs = [par.text for par in article_list]
        self.article.text = '\n'.join(paragraphs)

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Finds meta information of article
        """
        article = article_soup.find('div', {'itemprop': 'headline'})
        article_title = article.find('h1')
        self.article.title = article_title.text
        article_authors = article_soup.find_all('span',
                        {'itemprop': 'author'})[0].find('meta', itemprop='name')
        authors = article_authors.get('content')
        if authors:
            self.article.author = [authors]
        else:
            self.article.author = ['NOT FOUND']
        try:
            article_tags = article_soup.find('ul', {'itemprop': 'keywords'})
            article_tags_li = article_tags.find_all('li')
            self.article.topics = [tag.text.replace('"', '&quot;')
                                   for tag in article_tags_li]
        except IndexError:
            self.article.topics = []
        article_date = article_soup.find('meta', {'itemprop': 'datePublished'}).get('content')
        if isinstance(article_date, str):
            self.article.date = self.unify_date_format(article_date)

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unifies date format
        """
        return datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')

    def parse(self) -> Union[Article, bool, list]:
        """
        Parses each article
        """
        response = requests.get(self.full_url,
                                headers=self.config.get_headers(),
                                timeout=self.config.get_timeout())
        response.encoding = self.config.get_encoding()
        b_s = BeautifulSoup(response.text, 'lxml')
        self._fill_article_with_text(b_s)
        self._fill_article_with_meta_information(b_s)
        return self.article


def prepare_environment(base_path: Union[Path, str]) -> None:
    """
    Creates ASSETS_PATH folder if no created and removes existing folder
    """
    if base_path.exists():
        shutil.rmtree(base_path)
    base_path.mkdir(parents=True)


def main() -> None:
    """
    Entrypoint for scrapper module
    """
    prepare_environment(ASSETS_PATH)
    configuration = Config(path_to_config=CRAWLER_CONFIG_PATH)
    crawler = Crawler(config=configuration)
    crawler.find_articles()
    for i, full_url in enumerate(crawler.urls, 1):
        parser = HTMLParser(full_url=full_url, article_id=i, config=configuration)
        article: Union[Article, bool, list] = parser.parse()
        if isinstance(article, Article):
            to_raw(article)
            to_meta(article)


if __name__ == "__main__":
    main()
