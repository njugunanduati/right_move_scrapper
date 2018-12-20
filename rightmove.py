# -*- coding: utf-8 -*-
import scrapy
import random
from items import RightmoveItem
import json
import re
from datetime import datetime

LINKS_XPATH = '//div[@class="propertyCard-details"]/a[@class="propertyCard-link"]/@href'
HISTORY_URL = 'https://www.rightmove.co.uk/ajax/house-prices/sold-history.html?propertyId={}'


SPARQL = """prefix rdf: <https://www.w3.org/1999/02/22-rdf-syntax-ns#>
prefix rdfs: <https://www.w3.org/2000/01/rdf-schema#>
prefix owl: <https://www.w3.org/2002/07/owl#>
prefix xsd: <https://www.w3.org/2001/XMLSchema#>
prefix sr: <http://data.ordnancesurvey.co.uk/ontology/spatialrelations/>
prefix ukhpi: <http://landregistry.data.gov.uk/def/ukhpi/>
prefix lrppi: <http://landregistry.data.gov.uk/def/ppi/>
prefix skos: <https://www.w3.org/2004/02/skos/core#>
prefix lrcommon: <http://landregistry.data.gov.uk/def/common/>

SELECT ?paon ?saon ?street ?town ?county ?postcode ?amount ?date ?category
WHERE
{{
  VALUES ?postcode {{"{}"^^xsd:string}}

  ?addr lrcommon:postcode ?postcode.

  ?transx lrppi:propertyAddress ?addr ;
          lrppi:pricePaid ?amount ;
          lrppi:transactionDate ?date ;
          lrppi:transactionCategory/skos:prefLabel ?category.

  OPTIONAL {{?addr lrcommon:county ?county}}
  OPTIONAL {{?addr lrcommon:paon ?paon}}
  OPTIONAL {{?addr lrcommon:saon ?saon}}
  OPTIONAL {{?addr lrcommon:street ?street}}
  OPTIONAL {{?addr lrcommon:town ?town}}
}}
ORDER BY ?amount"""

LANDREG_URL = 'http://landregistry.data.gov.uk/landregistry/sparql'

H_SEARCH_URL = ('https://www.rightmove.co.uk/property-for-sale/find.html'
                '?searchType=SALE'
                '&locationIdentifier={}'
                '&insId=1'
                '&radius=0.0'
                '&index={}'
                '&sortType=6'
                '&_includeSSTC=on'
                '&auction=false')

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

def price(t):
    return int(t['price'].replace('£','').replace(',',''))

class RightmoveSpider(scrapy.Spider):
    name = 'rightmove'
    allowed_domains = ['rightmove.co.uk', 'data.gov.uk']

    custom_settings = {
        'USER_AGENT' : random.choice(USER_AGENTS)
        }


    def __init__(self, page_count, location_id, *args, **kwargs):
        super(RightmoveSpider, self).__init__(*args, **kwargs)
        self.pages = range(1, int(page_count) + 1)
        self.location_id = location_id

    def start_requests(self):
        for page in self.pages:
            url = H_SEARCH_URL.format(self.location_id, (page - 1) * 24)
            yield scrapy.Request(url, callback=self.get_properties)

    def get_properties(self,response):
        int_links = [link for link in response.xpath(LINKS_XPATH).extract() if link != '']
        links = ('https://www.rightmove.co.uk{}'.format(link) for link in int_links)
        for link in links:
            yield scrapy.Request(link, callback=self.get_details)

    def get_details(self, response):
        item = RightmoveItem()
        item['Address'] = response.xpath('//meta[@itemprop="streetAddress"]/@content').extract_first().strip()
        item['Asking_Price'] = response.xpath('//p[@id="propertyHeaderPrice"]/strong/text()').extract_first().strip().replace('£', '').replace(',','')

        item['Description'] = response.xpath('//h1[@itemprop="name"]/text()').extract_first().replace(' for sale', '')
        item['Date_Listed'] = response.xpath('//div[@id="firstListedDateValue"]/text()').extract_first()

        item['Property_URL'] = response.request.url
        item['Bedrooms'] = item['Description'].split(' ')[0]
        if item['Bedrooms'] != 'Studio':
            try:
                int(item['Bedrooms'])
            except ValueError:
                s = re.search('[0-9]{1,2}', item['Description'])
                if s:
                    item['Bedrooms'] = s.group(0)
                else:
                    item['Bedrooms'] = ''

        item['Tenure'] = response.xpath('//span[@id="tenureType"]/text()').extract_first()
        item['Agent'] = response.xpath('//a[@id="aboutBranchLink"]/strong/text()').extract_first()
        # item['Agent_Address'] = response.xpath('//div[@class="agent-details-display"]/address/text()').extract_first()
        item['Agent_Phone_Number'] = response.xpath('//div[@id="requestdetails"]/p/a/strong/text()').extract_first()
        plink = response.xpath('//a[@id="soldPriceGoTo"]/@href').extract_first()
        if plink is None:
            plink = response.xpath('//div[@class="clearfix main"]/script[3]/text()').extract_first()
            item['Postcode'] = re.search('"postcode":"([A-Z]{1,2}[0-9]{1,2}[A-Z]{0,1} [0-9][A-Z][A-Z])"', plink).group(1)
        else:
            item['Postcode'] = re.search('/house-prices/([A-Z]{1,2}[0-9]{1,2}[A-Z]{0,1}-[0-9][A-Z][A-Z]).html', plink).group(1)
            item['Postcode'] = item['Postcode'].replace('-', ' ')
        prefix = 'https://www.rightmove.co.uk/property-for-sale/property-'
        suffix = '.html'
        item['PropertyID'] = item['Property_URL'].replace(prefix, '').replace(suffix, '')
        yield scrapy.Request(HISTORY_URL.format(item['PropertyID']),
                             callback=self.get_history,
                             meta=dict(item=item),
                             dont_filter=True)

    def get_history(self, response):
        item = response.meta['item']
        jsonresponse = json.loads(response.body_as_unicode())
        trans = jsonresponse['saleHistoryItems']
        if not trans:
            yield item
            return
        item['Sale_History'] = [(t['dateSold'], price(t)) for t in trans]
        item['Last_Sold_Date'] = item['Sale_History'][0][0]
        item['Last_Sold_Price'] = item['Sale_History'][0][1]
        yield scrapy.FormRequest(LANDREG_URL,
                                 formdata={'query': SPARQL.format(item['Postcode'])},
                                 # headers={'Content-Type': 'application/sparql-results+json; charset=utf-8'},
                                 callback=self.get_address,
                                 meta=dict(item=item), dont_filter=True)

    def get_address(self, response):
        item = response.meta['item']
        jsonresponse = json.loads(response.body_as_unicode())
        trans = jsonresponse['results']['bindings']
        addresses = dict()
        for tran in trans:
            try:
                street = tran.get('street').get('value')
            except AttributeError:
                street = item['Address']
            paon = tran.get('paon')
            paon = paon.get('value') if paon else ''
            saon = tran.get('saon')
            saon = saon.get('value') if saon else ''
            address = paon, saon, street
            for part in address:
                part.strip()
            price = int(tran.get('amount').get('value'))
            date = tran.get('date').get('value')
            transaction = date, price
            addresses[address] = addresses.get(address, []) + [transaction]
        for add, trans in addresses.items():
            trans.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'))
            year_ts = {(t[0].split('-')[0] , t[1]) for t in trans}
            if set(item['Sale_History']) == year_ts:
                item['Address'] = ' '.join(add).title()
                item['Last_Sold_Date'] = trans[-1][0]
                item['Last_Sold_Price'] = trans[-1][1]
                item['Sale_History'] = trans
        if item['Asking_Price'] not in ('Coming Soon', 'POA'):
            item['Last_Sold_v_Asking_Price'] = int(item['Asking_Price']) - item['Last_Sold_Price']
        return item
