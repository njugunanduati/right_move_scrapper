import os
import sys
if getattr(sys, 'frozen', False):
    os.mkdir(sys._MEIPASS + '/scrapy')
    os.rename(sys._MEIPASS + '/VERSION', sys._MEIPASS + '/scrapy/VERSION')
    os.rename(sys._MEIPASS + '/mime.types', sys._MEIPASS + '/scrapy/mime.types')
    import logging

import requests
import random
from lxml import html
import logging
from requests.exceptions import HTTPError
from scrapy.crawler import CrawlerProcess
from rightmove import RightmoveSpider, H_SEARCH_URL, USER_AGENTS
import pickle
from more_itertools import unique_everseen



RESULT_COUNT_XPATH = '//span[@class="searchHeader-resultCount"]/text()'

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('mylog.log')
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

def headers():
    return {'User-Agent':random.choice(USER_AGENTS)}

def silentremove(filename):
    if os.path.exists(filename):
        os.remove(filename)

def get_locations(location, depth=0):

    try:
        r = requests.get(L_SEARCH_URL.format(location), headers=headers())
        # logging.debug(r.status_code)
        r.raise_for_status()
        tree = html.fromstring(r.text)
        location = tree.xpath(LOCATION_XPATH)
        options = tree.xpath(OPTIONS_XPATH.format('text()'))
        codes = tree.xpath(OPTIONS_XPATH.format('/@value'))
        return location, options, codes
    except HTTPError:
        if depth <= 5:
            return get_locations(location, depth=depth + 1)
        else:
            print('Error connecting to RightMove')
            raise HTTPError

def pick_location(location, options, codes):
    if options:
        title = 'Pick a more precise location: '
        i = pick(options, title, multi_select=False, min_selection_count=1)[1]
        # logger.debug('Location: {}, Code: {}'.format(options[i], codes[i]))
        return codes[i]
    elif location:
        # logger.debug('Code: {}'.format(location[0]))
        return location[0]

def get_page_count(code):
    r = requests.get(H_SEARCH_URL.format(code,0), headers=headers())
    # logging.debug(r.status_code)
    r.raise_for_status()
    tree = html.fromstring(r.text)
    result_count = int(tree.xpath(RESULT_COUNT_XPATH)[0].replace(',',''))
    page_count = int(result_count / 24) + (result_count % 24 > 0)
    if page_count > 42:
        page_count = 42
    return page_count

if __name__ == '__main__':

    with open('locations.pkl', 'rb') as f:
        codes = pickle.load(f)
    p_counts = [get_page_count(code) for code in codes]

    if getattr(sys, 'frozen', False):
        prefix = 'file:///' + sys.executable + '/../'
    else:
        prefix = ''

    settings = {'LOG_LEVEL' :'INFO',
                'ROBOTSTXT_OBEY' : False,
                'COOKIES_ENABLED' : False,
                'FEED_FORMAT' : 'csv',
                'DUPEFILTER_DEBUG' : True,
                'FEED_URI' : prefix + 'rightmove.csv',
                'FEED_EXPORT_FIELDS' : ["Property_URL", "Address", "Postcode", "Description",
                                   "Date_Listed", "Bedrooms", "Asking_Price",
                                   "Last_Sold_Price", "Last_Sold_v_Asking_Price",
                                        "Last_Sold_Date", "Tenure", "Agent", "Agent_Address", "Agent_Phone_Number"]}

    silentremove('rightmove.csv')
    process = CrawlerProcess(settings)
    if getattr(sys, 'frozen', False):
        loggers = ('scrapy.utils.log', 'scrapy.middleware', 'scrapy.spidermiddlewares.httperror', 'scrapy.extensions.feedexport', 'scrapy.statscollectors', 'scrapy.core.engine')
        for logger in loggers:
            logging.getLogger(logger).setLevel(logging.WARNING)
    for code, page_count in zip(codes, p_counts):
        process.crawl(RightmoveSpider, page_count=page_count, location_id=code)
    process.start()

    silentremove('rightmove results.csv')
    with open('rightmove.csv', 'r') as infile, open('rightmove results.csv', 'w') as outfile:
        lines = unique_everseen(infile)
        outfile.writelines(lines)
    silentremove('rightmove.csv')
