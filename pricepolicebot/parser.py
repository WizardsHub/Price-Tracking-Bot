import re
import json

""" a web scrapping library which is used to parse a HTML web page """
from bs4 import BeautifulSoup 

def ruppees_converter(string):
    """Convert a INDIAN price (XXXX.XX) to a float."""
    return float(string.strip("₹").replace(',', ''))

def amazon_parser(html):    
    item = {} #they are used to define a data structure called dictionary

    soup = BeautifulSoup(html, "lxml") 
    """a soup variable which will store data parsed by Beautiful function from html using lxml parser already installed in 
        beautiful soup library"""

    name = soup.find("span", id = "productTitle").string

    price_span =  soup.find("span", id = {"class": "priceToPay"})
    if price_span is None:
        price_span = soup.find("span", {"class": "apexPriceToPay"})
    price_str = price_span.find("span", {"class": "a-offscreen"}) \
        if price_span is not None else None
    #A NavigableString object holds the text within an HTML or an XML tag.
    
    item = {
        #key : map
        "name": name.strip(),
        "price": ruppees_converter(price_str.string) if price_str else 0.0,
        "available": bool(price_str),
    }

def flipkart_parser(html):
    item ={}

    soup = BeautifulSoup(html, "lxml")

    name = soup.find("span", {"class": "B_NuCI"}).string
    price_str = soup.find("div", {"class": "_30jeq3 _16Jk6d"})
    
    item = {
        "name" : name.strip(),
        "price": ruppees_converter(price_str.string) if price_str else 0.0,
        "available": bool(price_str)
    }

PARSER = {
    ".amazon.in" : amazon_parser,
    ".flipkart.in" : flipkart_parser,
}