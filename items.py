# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class RightmoveItem(scrapy.Item):
    Address = scrapy.Field()
    Asking_Price = scrapy.Field()
    Last_Sold_Price = scrapy.Field()
    Last_Sold_v_Asking_Price = scrapy.Field()
    Description = scrapy.Field()
    Date_Listed = scrapy.Field()
    Last_Sold_Date = scrapy.Field()
    Property_URL = scrapy.Field()
    Bedrooms = scrapy.Field()
    Tenure = scrapy.Field()

    Postcode = scrapy.Field()
    PropertyID = scrapy.Field()
    Sale_History = scrapy.Field()
    Agent = scrapy.Field()
    Agent_Address = scrapy.Field()
    Agent_Phone_Number = scrapy.Field()
