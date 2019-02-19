import requests
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
from typing import List, Tuple
from pybooks.structures import Source, UrlRules, HtmlRules
import json
from pybooks.errors import *
import logging
from math import e
import os
from pprint import pprint

SOURCES_FILE = os.path.dirname(__file__) + '\\sources.json'


class Pbooks:
    def __init__(self, author: str, title: str,
                 file_name: str = SOURCES_FILE,
                 weights: Tuple[float, float] = (1, 1),
                 show_result: bool = False,
                 threshold: float = 0,
                 log: bool = True):
        """
        Search through all available sources and find a book with the highest accuracy based on author and title input
        :param author: string Author of the book you want to find
        :param title: string Title of the book you want to find
        :param file_name: string JSON file contains all the sources and rules
        :param weights: Tuple[float, float] contain the weight values for accuracy calculation
        :param show_result: bool Print the result at the end or not
        :param threshold: float Only show the result above the threshold
        :param log: bool Print during run or not
        """
        if log:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.WARNING)
            logging.warning('YOU TURNED OFF INFO LOGGING. CHOSEN URL WILL NOT BE PRINTED')
        try:
            self.sources = self.convert_to_struct(file_name)
        except FileNotFoundError:
            raise SourcesNotFoundError('JSON sources file not found')
        self.author = author
        self.title = title
        self.result = []
        self.chosen = ''
        self.weights = weights
        self.show_result = show_result
        self.threshold = threshold

    def parse(self) -> None:
        max_acc = 0
        max_title = ''
        count = 0
        for source in self.sources:
            logging.info(msg='Scraping URL: {}'.format(source.url))
            for page in self.get_pagination(source, self.title):
                logging.info(msg='Searching through page: {}'.format(page))
                html = BeautifulSoup(requests.get(page).content, 'lxml')
                hrules = source.html_rules
                BODY = hrules.body
                ROW = hrules.row
                TITLE = hrules.title
                EXTENSION = hrules.extension
                YEAR = hrules.year
                AUTHOR = hrules.author
                body = html.find(BODY.tag, BODY.attribute)
                rows = body.find_all(ROW.tag, ROW.attribute)[ROW.position:]
                authors, titles, urls, years, extensions = [], [], [], [], []
                # TODO: Find a shorter, more efficient method for the try-except
                for row in rows:
                    try:
                        if AUTHOR.position is not None:
                            authors.append(row.find_all(AUTHOR.tag, AUTHOR.attribute)[AUTHOR.position].text
                                           .replace('\n', '').strip())
                        else:
                            authors.append(row.find(AUTHOR.tag, AUTHOR.attribute).text.replace('\n', '').strip())
                    except (TypeError, AttributeError):
                        authors.append('NotFound')

                    try:
                        if TITLE.position is not None:
                            titles.append(row.find_all(TITLE.tag, TITLE.attribute)[TITLE.position].text
                                          .replace('\n', '').strip())
                            urls.append(source.url +
                                        row.find_all(TITLE.tag, TITLE.attribute)[TITLE.position]
                                        .find('a')['href'].replace('\n', '').strip())
                        else:
                            titles.append(row.find(TITLE.tag, TITLE.attribute).text.replace('\n', '').strip())
                            urls.append(source.url +
                                        row.find(TITLE.tag, TITLE.attribute)
                                        .find('a')['href'].replace('\n', '').strip())
                    except (TypeError, AttributeError):
                        titles.append('NotFound')
                        urls.append('NotFound')

                    try:
                        if YEAR.position is not None:
                            years.append(row.find_all(YEAR.tag, YEAR.attribute)[YEAR.position].text
                                         .replace('\n', '').strip())
                        else:
                            years.append(row.find(YEAR.tag, YEAR.attribute).text.replace('\n', '').strip())
                    except (TypeError, AttributeError):
                        years.append('NotFound')

                    try:
                        if EXTENSION.position is not None:
                            extensions.append(row.find_all(EXTENSION.tag, EXTENSION.attribute)[EXTENSION.position].text
                                              .replace('\n', '').strip())
                        else:
                            extensions.append(row.find(EXTENSION.tag, EXTENSION.attribute).text
                                              .replace('\n', '').strip())
                    except (TypeError, AttributeError):
                        extensions.append('NotFound')

                for a, t, u, y, e in zip(authors, titles, urls, years, extensions):
                    accuracy = self.get_accuracy(self.author, a, self.title, t)
                    if accuracy >= self.threshold:
                        self.result.append({
                            'author': a,
                            'title': t,
                            'url': u,
                            'year': y,
                            'extension': e,
                            'accuracy': accuracy
                        })
                    count += 1
                    if accuracy > max_acc:
                        max_acc = accuracy
                        max_title = t
                        self.chosen = u
                logging.info('Number of books found so far: {}'.format(count))
                logging.info('Highest accuracy so far: {} with title {}'.format(max_acc,
                                                                                max_title))

    def get_pagination(self, source: Source, request: str) -> str:
        """
        Get URL for each page number in a source
        :param source: Source
        :param request: str
        :return: str
        """
        page = 1

        def get_page(url, req, conc, pagination_r, pag):
            return "{main_url}{request_str}{concat}{pagi}".format(
                main_url=url,
                request_str=req,
                concat=conc,
                pagi=pagination_r + str(pag))

        while True:
            logging.info('Found {} pages... with main url: {}'.format(page, source.url))
            request_str = request.replace(' ', '+')
            page_url = get_page(source.url,
                                source.url_rules.request + request_str,
                                source.url_rules.concat,
                                source.url_rules.pagination,
                                str(page))
            previous = page + 1
            previous_url = get_page(source.url,
                                    source.url_rules.request + request_str,
                                    source.url_rules.concat,
                                    source.url_rules.pagination,
                                    str(previous))

            if self.check_duplicate(previous_url, page_url):
                logging.info('Reached all pages of source: {}'.format(source.url))
                yield previous_url
                break
            else:
                page += 1
                yield page_url

    def check_duplicate(self, url1: str, url2: str) -> bool:
        """
        Check if two different urls lead to the same page
        :param url1: string URL of the first page
        :param url2: string URL of the second page
        :return: bool Two pages are the same or not
        """
        html1 = BeautifulSoup(requests.get(url1).content, 'lxml')
        html2 = BeautifulSoup(requests.get(url2).content, 'lxml')
        body1, body2 = self.get_source(url1).html_rules.body, self.get_source(url2).html_rules.body
        return html1.find(body1.tag, body1.attribute) == html2.find(body2.tag, body2.attribute)

    def get_accuracy(self, author1: str, author2: str, title1: str, title2: str) -> float:
        """
        Get the sigmoided weighted sum of accuracy of the actual authors and titles found and the target items
        :param author1: string actual or target author
        :param author2: string actual or target author
        :param title1: string actual or target title
        :param title2: string actual or target title
        :return: float average accuracy
        """
        author_acc = SequenceMatcher(None, author1, author2).ratio()
        title_acc = SequenceMatcher(None, title1, title2).ratio()
        acc = (author_acc*self.weights[0] + title_acc*self.weights[1])
        return 1 / (1 + e**(-acc))

    # def func_wrap(self, func: Callable) -> Callable:
    #     """
    #     Decorator for Beautifulsoup find and find_all function to replace NoneType value with "NotFound" string
    #     :param func: function Beautifulsoup finc and finc_all
    #     :return: function or string
    #     """
    #     @wraps(func)
    #     def wrap_bs(*args, **kwargs):
    #         if func(*args, **kwargs) is None:
    #             return 'NotFound'
    #         else:
    #             return func(*args, **kwargs)
    #     return wrap_bs

    def get_source(self, p_url: str) -> Source:
        """
        Find out a Source of a pagination URL
        :param p_url: str
        :return: Source
        """
        for source in self.sources:
            if p_url.startswith(source.url):
                return source
        else:
            raise InvalidUrlError('URL does not seem to belong to any listed sources, please change url or source.')

    def convert_to_struct(self, json_file: str) -> List[Source]:
        """
        Convert JSON nested dictionaries to Source-type class
        :param json_file: str
        :return: List[Source]
        """
        assert json_file.endswith('.json')
        json_sources = json.load(open(json_file, 'r+'))
        lst = []
        for dic in json_sources:
            source = Source(
                url=dic['URL'],
                url_rules=UrlRules(
                    request=dic['URL_RULES']['REQUEST'],
                    delimiter=dic['URL_RULES']['DELIMITER'],
                    concat=dic['URL_RULES']['CONCAT'],
                    pagination=dic['URL_RULES']['PAGINATION']
                ),
                html_rules=HtmlRules(
                    title=HtmlRules.TagRules(
                        tag=dic['HTML_RULES']['TITLE']['TAG'],
                        attribute=dic['HTML_RULES']['TITLE']['ATTRIBUTE'],
                        position=dic['HTML_RULES']['TITLE']['POSITION']
                    ),
                    body=HtmlRules.TagRules(
                        tag=dic['HTML_RULES']['BODY']['TAG'],
                        attribute=dic['HTML_RULES']['BODY']['ATTRIBUTE'],
                        position=dic['HTML_RULES']['BODY']['POSITION']
                    ),
                    row=HtmlRules.TagRules(
                        tag=dic['HTML_RULES']['ROW']['TAG'],
                        attribute=dic['HTML_RULES']['ROW']['ATTRIBUTE'],
                        position=dic['HTML_RULES']['ROW']['POSITION']
                    ),
                    author=HtmlRules.TagRules(
                        tag=dic['HTML_RULES']['AUTHOR']['TAG'],
                        attribute=dic['HTML_RULES']['AUTHOR']['ATTRIBUTE'],
                        position=dic['HTML_RULES']['AUTHOR']['POSITION']
                    ),
                    year=HtmlRules.TagRules(
                        tag=dic['HTML_RULES']['YEAR']['TAG'],
                        attribute=dic['HTML_RULES']['YEAR']['ATTRIBUTE'],
                        position=dic['HTML_RULES']['YEAR']['POSITION']
                    ),
                    extension=HtmlRules.TagRules(
                        tag=dic['HTML_RULES']['EXTENSION']['TAG'],
                        attribute=dic['HTML_RULES']['EXTENSION']['ATTRIBUTE'],
                        position=dic['HTML_RULES']['EXTENSION']['POSITION']
                    )
                )
            )
            lst.append(source)
        return lst

    def main(self):
        self.parse()
        logging.info("Chosen URL is: {}".format(self.chosen))
        if self.show_result:
            pprint(self.result)


# if __name__ == '__main__':
#     pbook = Pbooks(file_name='sources.json', author='jerome',
#                    title='elements of statistic',
#                    weights=(1, 1),
#                    threshold=0.4,
#                    show_result=True,
#                    log=True)
#     pbook.main()
