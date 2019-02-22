from typing import List, Dict


class UrlRules:
    def __init__(self,
                 request: str,
                 delimiter: str,
                 concat: str,
                 pagination: str):
        self.request = request
        self.delimiter = delimiter
        self.concat = concat
        self.pagination = pagination


class HtmlRules:
    class TagRules:
        def __init__(self, tag: str, attribute: List[Dict[str, str]], position: int or None):
            self.tag = tag
            self.attribute = attribute
            self.position = position

    def __init__(self,
                 body: TagRules,
                 row: TagRules,
                 title: TagRules,
                 author: TagRules,
                 year: TagRules,
                 extension: TagRules):
        self.body = body
        self.row = row
        self.title = title
        self.author = author
        self.year = year
        self.extension = extension


class Source:
    """
    Create a class like structure from JSON dictionary in sources.json
    """
    def __init__(self,
                 url: str,
                 url_rules: UrlRules,
                 html_rules: HtmlRules):
        self.url = url
        self.url_rules = url_rules
        self.html_rules = html_rules
