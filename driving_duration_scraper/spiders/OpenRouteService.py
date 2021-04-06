import scrapy
import csv
import json
from urllib.parse import urlencode

def validate_csv_fields(row):
    keys = row.keys()
    return 'lat' in keys and 'lng' in keys

def read_csv(file):
    with open(file) as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
        if not rows:
            raise ValueError('The provided CSV file is empty')

        if not validate_csv_fields(rows[0]):
            raise ValueError('Make sure the provided CSV file contains the columns `lat` and `lng`')
        return rows


class OpenrouteserviceSpider(scrapy.Spider):
    name = 'OpenRouteService'
    allowed_domains = ['openrouteservice.org']

    def __init__(self,
                 api_key=None,
                 profile='driving-car', # see https://openrouteservice.org/dev/#/api-docs/v2/directions/{profile}/get for details
                 source_csv=None,
                 destination_csv=None,
                 *args, **kwargs):
        super(OpenrouteserviceSpider, self).__init__(*args, **kwargs)

        if not api_key:
            raise ValueError('Please provide an API_Key via `-a api_key=...`')
        if not source_csv:
            raise ValueError('Please provide a CSV file containing trip starting points using `-a source_csv=...`')
        if not destination_csv:
            raise ValueError('Please provide a CSV file containing trip end points using `-a destination_csv=...`')

        self.api_url = 'https://api.openrouteservice.org/v2/directions/{}?api_key={}&'.format(profile, api_key)
        self.sources = read_csv(source_csv)
        self.destinations = read_csv(destination_csv)

        self.start_urls = []

    def start_requests(self):
        # this is where we build the cartesian product of source and dest and
        # construct all requests
        for source in self.sources:
            for dest in self.destinations:
                # https://openrouteservice.org/dev/#/api-docs/v2/directions/{profile}/get
                yield scrapy.Request(self.api_url + urlencode({
                    'start': source.get('lng') + ',' + source.get('lat'),
                    'end': dest.get('lng') + ',' + dest.get('lat'),
                }), callback=self.trip_result, cb_kwargs={'source': source, 'dest': dest})

    def trip_result(self, response, source, dest):
        # ors returns a featurecollection with one item when using the `GET` api
        trip = json.loads(response.text)
        feature = trip['features'][0]
        feature['properties'].update(**{
            'source': source,
            'destination': dest
        })
        return feature
