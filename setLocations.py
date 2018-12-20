import os
import sys
from pick import pick
import requests
import random
from lxml import html
from requests.exceptions import HTTPError
import pickle

L_SEARCH_URL = 'http://www.rightmove.co.uk/property-for-sale/search.html?searchLocation={}'

OPTIONS_XPATH = "//select[@id='locationIdentifier']/option/{}"
LOCATION_XPATH = "//input[@id='locationIdentifier']/@value"

USER_AGENTS = (
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:59.0) Gecko/20100101 Firefox/59.0',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
)


def silentremove(filename):
    if os.path.exists(filename):
        os.remove(filename)

def headers():
    return {'User-Agent':random.choice(USER_AGENTS)}

def get_locations(location, depth=0):

    try:
        r = requests.get(L_SEARCH_URL.format(location), headers=headers())
        # logging.debug(r.status_code)
        r.raise_for_status()
        tree = html.fromstring(r.text)
        location = tree.xpath(LOCATION_XPATH)
        options = tree.xpath(OPTIONS_XPATH.format('text()'))
        codes = tree.xpath(OPTIONS_XPATH.format('/@value'))
        # print(location, options, codes)
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

if __name__ =='__main__':

    keep_trying = True
    crawl_codes = []
    locations = []
    while keep_trying:
        loc_name = input('Please enter a search location: ')
        location, options, codes  = get_locations(loc_name)
        if (location, options, codes) == ([''], [], []):
            title = 'Sorry no locations matching "{}"'.format(loc_name) + '\nWould you like to add more locations?'
            options = ['Yes', 'No']
            response = pick(options, title, multi_select=False, min_selection_count=1)[0]
            if response == 'Yes':
                continue
            else:
                break
        # logger.debug('Options: {}'.format(options))
        # logger.debug('Codes: {}'.format(codes))

        code = pick_location(location, options, codes)
        locations.append(loc_name)
        crawl_codes.append(code)
        title = 'Would you like to add more locations?'
        options = ['Yes', 'No']
        response = pick(options, title, multi_select=False, min_selection_count=1)[0]
        keep_trying = True if response == 'Yes' else False

    print('Locations to be scraped: ', *locations)

    crawl_codes = [c for c in crawl_codes if '^' in c]

    if getattr(sys, 'frozen', False):
        prefix = sys.executable +'/../'
    else:
        prefix = ''

    silentremove(prefix + 'locations.pkl')
    with open(prefix + 'locations.pkl', 'wb') as f:
        # print(crawl_codes)
        pickle.dump(crawl_codes, f, protocol=pickle.HIGHEST_PROTOCOL)
