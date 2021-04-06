import scrapy


class OpenrouteserviceSpider(scrapy.Spider):
    name = 'OpenRouteService'
    allowed_domains = ['openrouteservice.org']
    start_urls = ['http://openrouteservice.org/']

    def parse(self, response):
        pass
