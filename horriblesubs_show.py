import scrapy
from scrapy.loader.processors import TakeFirst


class Show(scrapy.Item):
    """scrapy Item that describes a show from HorribleSubs"""
    name = scrapy.Field(output_processor=TakeFirst())
    url_extension = scrapy.Field(output_processor=TakeFirst())
