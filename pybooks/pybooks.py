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
from sdebugger import Decorators
import time
import argparse

SOURCES_FILE = os.path.dirname(__file__) + '\\sources.json'


@Decorators.typecheck
class Pbooks:
    def __init__(self, author: str or None, title: str,
                 file_name: str = SOURCES_FILE,
                 weights: Tuple[float or int, float or int] = (1, 1),
                 show_result: bool = False,
                 threshold: float = 0,
                 log: bool = True,
                 break_at: float = 0.9,
                 delay: float = 0.8):
        """
        Search through all available sources and find a book with the highest accuracy based on author and title input
        :param author: string Author of the book you want to find
        :param title: string Title of the book you want to find
        :param file_name: string JSON file contains all the sources and rules
        :param weights: Tuple[float, float] contain the weight values for accuracy calculation
        :param show_result: bool Print the result at the end or not
        :param threshold: float Only show the result above the threshold
        :param log: bool Print during run or not
        :param break_at: float Stop if encounter a title with accuracy higher or equal than this number
        :param delay: Time gap between printing each books and their attributes
        """
        assert type(weights[0]) in (float, int) and type(weights[1]) in (float, int), \
            "Weights should be of type int or float"
        assert break_at > 0, 'break_at should be higher than 0'
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
        self.break_at = break_at
        self.log = log
        self.delay = delay

    def parse(self) -> None:
        max_acc = 0
        max_title = ''
        count = 0
        for source in self.sources:
            logging.info(msg='Scraping URL: {}'.format(source.url))
            all_pages = self.get_pagination(source, self.title)
            for page in all_pages:
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
                # TODO: Find a shorter, more efficient method for the try-except
                for row in rows:
                    try:
                        if AUTHOR.position is not None:
                            author = row.find_all(AUTHOR.tag, AUTHOR.attribute)[AUTHOR.position].text \
                                .replace('\n', '').strip()
                        else:
                            author = row.find(AUTHOR.tag, AUTHOR.attribute).text.replace('\n', '').strip()
                    except (TypeError, AttributeError):
                        author = "NotFound"

                    try:
                        if TITLE.position is not None:
                            title = row.find_all(TITLE.tag, TITLE.attribute)[TITLE.position].text \
                                .replace('\n', '').strip()
                            url = source.url + row.find_all(TITLE.tag, TITLE.attribute)[TITLE.position] \
                                .find('a')['href'].replace('\n', '').strip()
                        else:
                            title = row.find(TITLE.tag, TITLE.attribute).text.replace('\n', '').strip()
                            url = source.url + row.find(TITLE.tag, TITLE.attribute).find('a')['href']\
                                .replace('\n', '').strip()
                    except (TypeError, AttributeError):
                        title = "NotFound"
                        url = "NotFound"

                    try:
                        if YEAR.position is not None:
                            year = row.find_all(YEAR.tag, YEAR.attribute)[YEAR.position].text \
                                         .replace('\n', '').strip()
                        else:
                            year = row.find(YEAR.tag, YEAR.attribute).text.replace('\n', '').strip()
                    except (TypeError, AttributeError):
                        year = "NotFound"

                    try:
                        if EXTENSION.position is not None:
                            extension = row.find_all(EXTENSION.tag, EXTENSION.attribute)[EXTENSION.position].text \
                                              .replace('\n', '').strip()
                        else:
                            extension = row.find(EXTENSION.tag, EXTENSION.attribute).text \
                                              .replace('\n', '').strip()
                    except (TypeError, AttributeError):
                        extension = "NotFound"

                    accuracy = self.get_accuracy(self.author, author, self.title, title)

                    if accuracy[0] >= self.threshold:
                        self.result.append({
                            'author': author,
                            'title': title,
                            'url': url,
                            'year': year,
                            'extension': extension,
                            'accuracy': accuracy
                        })

                    count += 1

                    if accuracy[0] > max_acc:
                        max_acc = accuracy[0]
                        max_title = title
                        self.chosen = url

                    logging.info('Number of books found so far: {}'.format(count))
                    logging.info("Found book with \n"
                                 "Title: {} \n"
                                 "Title accuracy: {}, Author accuracy: {} \n"
                                 "Overall accuracy: {} \n".format(title,
                                                                  accuracy[1],
                                                                  accuracy[2],
                                                                  accuracy[0]))
                    logging.info('Highest accuracy so far: {}. \n'
                                 'Title: {} \n'.format(max_acc,
                                                       max_title))

                    if max_acc >= self.break_at:
                        logging.info("Book with accuracy higher than or equal to breaking condition is: \n"
                                     "Title: {} \n"
                                     "Author: {} \n"
                                     "Overall accuracy: {}".format(title,
                                                                   author,
                                                                   accuracy[0]))
                        break
                    if self.log:
                        time.sleep(self.delay)

    def get_pagination(self, source: Source, request: str) -> List[str]:
        """
        Get URL for each page number in a source
        :param source: Source
        :param request: str
        :return: str
        """
        page = 1

        results = []

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
            next_ = page + 1
            next_url = get_page(source.url,
                                source.url_rules.request + request_str,
                                source.url_rules.concat,
                                source.url_rules.pagination,
                                str(next_))

            if self.check_duplicate(next_url, page_url):
                logging.info('Reached all pages of source: {}'.format(source.url))
                results.append(next_url)
                break
            else:
                results.append(page_url)
            return results

    def check_duplicate(self, url1: str, url2: str) -> bool:
        """
        Check if two different urls lead to the same page
        :param url1: string URL of the first page
        :param url2: string URL of the second page
        :return: bool Two pages are the same or not
        """
        html1 = BeautifulSoup(requests.get(url1, timeout=30).content, 'lxml')
        html2 = BeautifulSoup(requests.get(url2, timeout=30).content, 'lxml')
        body1, body2 = self.get_source(url1).html_rules.body, self.get_source(url2).html_rules.body
        return html1.find(body1.tag, body1.attribute) == html2.find(body2.tag, body2.attribute)

    def get_accuracy(self, author1: str, author2: str, title1: str, title2: str) -> Tuple[float, float, float]:
        # TODO: New algorithm for matching authors
        """
        Get the sigmoided weighted sum of accuracy of the actual authors and titles found and the target items
        :param author1: target author
        :param author2: actual author
        :param title1: target title
        :param title2: actual title
        :return: Tuple[float: overall accuracy, float: author accuracy, float: title accuracy]
        """
        # Split a string with multiple authors separated by ","
        author1 = author1.lower().split(',')
        author2 = author2.lower().split(',')
        title1 = title1.lower()
        title2 = title2.lower()
        title_acc = SequenceMatcher(None, title1, title2).ratio()
        if author1[0].strip() != '':
            author_acc = max([SequenceMatcher(None, a1.lstrip().rstrip(), a2.lstrip().rstrip()).ratio()
                              for a1 in author1 for a2 in author2])
            acc = (author_acc * self.weights[0] + title_acc * self.weights[1])
        else:
            author_acc = 0
            acc = title_acc
        return 1 / (1 + e ** (-acc)), author_acc, title_acc

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("author", help="Author of the book you want to find")
    args = parser.parse_args()
    print(args)
    # pbook = Pbooks(author='barry posner',
    #                title='the leadership',
    #                weights=(1, 1),
    #                threshold=0.4,
    #                show_result=False,
    #                log=True,
    #                break_at=0.8)
    # pbook.main()
