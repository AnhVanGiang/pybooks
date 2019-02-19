from dataclasses import dataclass
from typing import List, Dict


@dataclass
class UrlRules:
    request: str
    delimiter: str
    concat: str
    pagination: str


@dataclass
class HtmlRules:
    @dataclass
    class TagRules:
        tag: str
        attribute: List[Dict[str, str]]
        position: int or None
    body: TagRules
    row: TagRules
    title: TagRules
    author: TagRules
    year: TagRules
    extension: TagRules


@dataclass
class Source:
    """
    Create a class like structure from JSON dictionary in sources.json
    """
    url: str
    url_rules: UrlRules
    html_rules: HtmlRules
