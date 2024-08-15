import time
import logging
import tldextract

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from pricepolicebot.parser import PARSER

LOGGER = logging.getLogger(__name__)
#we make a logger to get track of logging of result from different modules so we have data of when, how things went wrong
#exception handling

#we use chromeoptions class instead of chrome because it makes uses of extensions in chrome
#extensions we mean here are like blocking popups, incognito mode, headless mode etc
DRIVEROPTS  = webdriver.ChromeOptions()

#headless mode is the mode where the browser doesnt open with any UI and GUI, perfect for web scrapping
DRIVEROPTS.add_argument("--headless")


def store_domain(url):
    """ext will store data in form of ExtractResult which contains data in form of (subdomain='www', domain='amazon', suffix='in')"""
    ext = tldextract.extract(url)
    return '.'.join([ext.domain, ext.suffix])

class MyProduct():

    # used to store the list of elements in parser
    stores = list(PARSER.keys())

    # parametrized constructor
    def __init__(self, product_url, max_price): 
        '''constructor in python'''
        self.url = product_url

        #self store will store the url extracted using tldextract library
        self.store = store_domain(product_url)

        LOGGER.info("New Product: %s at %s", self.url, self.store)

        if self.store not in MyProduct.stores:
            raise ValueError(f"Store not implemented: {self.store}")
            # valueerror is a error which means the datatype of the infromation is correct but value is different

        self.update_product_info(self)
        self.unreachable_count = 0
        self.max_price = max_price

        LOGGER.info("Product %s created with success.", self.name)
        """Logs provide developers with an extra set of eyes that are constantly looking at the flow that an
        application is going through. They can store information, like which user or IP accessed the application. If an error
        occurs, then they can provide more insights than a stack trace by telling you what the state of the program 
        was before it arrived at the line of code where the error occurred.
        By logging useful data from the right places, you can not only debug errors easily but also use the data to analyze 
        the performance of the application to plan for scaling or look at usage patterns to plan for marketing."""
        
    def update_product_info(self):
        html = self.get_html()

        # parser[amazon.in](html) = amazon_parser(html)
        info  = PARSER[self.store](html)

        self.name = info["name"]
        self.price = info["price"]
        self.available = info["available"]
        info["url"] = self.url

        return info

    def get_html(self):
        with webdriver.Chrome(options=DRIVEROPTS) as driver:
            driver.set_page_load_timeout(20) #inbuilt function

            # exception handling
            try:
                driver.get(self.url)
                #to get webpage using get method 
                time.sleep(3)

            except TimeoutException as exc:
                self.unreachable_count +=1
                raise TimeoutException("Timeout for the data.") from exc

            # to get html page source code in terminal
            html = driver.page_source
            return html

    def get_product_info(self):
        return{
            "name": self.name,
            "price": self.price,
            "available": self.available,
            "url": self.url
        }

