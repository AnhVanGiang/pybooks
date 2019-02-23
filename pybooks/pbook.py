import requests
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
from typing import List, Tuple
from structures import Source, UrlRules, HtmlRules
import json
from errors import *
import logging
from math import e
from pprint import pprint
from sdebugger import Decorators
import time
import argparse

SOURCES_FILE = "sources.json"


@Decorators.typecheck
class Pbooks:
    # TODO: Add different type of scraping: Lazy and Thorough
    def __init__(self, author: str or None, title: str,
                 file_name: str = SOURCES_FILE,
                 weights: Tuple[float or int, float or int] = (1, 1),
                 show_result: bool = False,
                 threshold: float = 0,
                 log: bool = True,
                 break_at: float = 0.9,
                 delay: float = 0.8,
                 method: str = "lazy"):
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
        :param method: Decide which method to evaluate books.
        Lazy: as soon as a book with accuracy higher than break_at is found, stop and return immediately
        Thorough: Find all books available and return the one with highest accuracy
        """
        assert method in ("lazy", "thorough"), "Method should be 'lazy' or 'thorough'"
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
        self.chosen_url = ''
        self.weights = weights
        self.show_result = show_result
        self.threshold = threshold
        self.break_at = break_at
        self.log = log
        self.delay = delay
        self.method = method
        self.chosen_title = ''
        self.highest_acc = 0

    def parse(self) -> None:
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
                if not rows:
                    logging.info("Found no books or the tags and attributes are incorrect")
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

                    if accuracy[0] > self.highest_acc:
                        self.highest_acc = accuracy[0]
                        self.chosen_title = title
                        self.chosen_url = url

                    logging.info('Number of books found so far: {}'.format(count))

                    if self.method == "lazy":
                        logging.info("Found book with \n"
                                     "Title: {} \n"
                                     "Title accuracy: {}, Author accuracy: {} \n"
                                     "Overall accuracy: {} \n".format(title,
                                                                      accuracy[1],
                                                                      accuracy[2],
                                                                      accuracy[0]))
                        logging.info('Highest accuracy so far: {}. \n'
                                     'Title: {} \n'.format(self.highest_acc,
                                                           self.chosen_title))

                        if self.highest_acc >= self.break_at:
                            logging.info("Book with accuracy higher than or equal to breaking condition is: \n"
                                         "Title: {} \n"
                                         "Author: {} \n"
                                         "Overall accuracy: {}".format(title,
                                                                       author,
                                                                       accuracy[0]))
                            return
                        if self.log:
                            time.sleep(self.delay)

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
            next_ = page + 1
            next_url = get_page(source.url,
                                source.url_rules.request + request_str,
                                source.url_rules.concat,
                                source.url_rules.pagination,
                                str(next_))

            if self.check_duplicate(next_url, page_url):
                logging.info('Reached all pages of source: {}'.format(source.url))
                yield next_url
                break
            else:
                yield page_url
                page += 1

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
        # TODO: Find a better way to format actual title and author strings
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
        logging.info("\n "
                     "Chosen URL is: {} \n"
                     "Title: {} \n"
                     "Accuracy: {}".format(self.chosen_url,
                                           self.chosen_title,
                                           self.highest_acc))
        if self.show_result:
            pprint(self.result)


if __name__ == '__main__':
    def weights(cmd):
        try:
            x, y = map(float, cmd.split(','))
            return x, y
        except (TypeError, AttributeError):
            raise argparse.ArgumentTypeError("Weights must be x: float or int, y: float or int")
    parser = argparse.ArgumentParser()
    parser.add_argument("-a",
                        "--author",
                        help="Author of the book you want to find",
                        type=str,
                        required=True)
    parser.add_argument("-t",
                        "--title",
                        help="Title of the book you want to find",
                        type=str,
                        required=True)
    parser.add_argument("-w",
                        "--weights",
                        help="Assign author and title weight to the final accuracy calculation",
                        default=(1, 1),
                        type=weights)
    parser.add_argument("-th",
                        "--threshold",
                        help="Only get results above the threshold amount",
                        type=float,
                        default=0.5)
    parser.add_argument("-l",
                        "--log",
                        help="Print out the process",
                        default=True,
                        type=bool)
    parser.add_argument("-s",
                        "--show",
                        help="Show result at the end of running")
    parser.add_argument("-br",
                        "--break-at",
                        help="Choose a book evaluation method",
                        type=float,
                        default=0.9)
    parser.add_argument("-m",
                        "--method",
                        help="Choose a book evaluation method",
                        type=str,
                        default="lazy")
    args = parser.parse_args()
    if args.method not in ("lazy", "thorough"):
        raise argparse.ArgumentTypeError("METHOD argument should be either 'lazy' or 'thorough'")
    pbook = Pbooks(author=args.author,
                   title=args.title,
                   weights=args.weights,
                   threshold=args.threshold,
                   show_result=args.show,
                   log=args.log,
                   break_at=args.break_at,
                   method=args.method)
    pbook.main()
