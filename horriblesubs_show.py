import scrapy
from scrapy.loader.processors import TakeFirst


class Show(scrapy.Item):
    name = scrapy.Field(output_processor=TakeFirst())
    url_extension = scrapy.Field(output_processor=TakeFirst())
