import scrapy
import csv
import json
from urllib.parse import urlencode


def validate_csv_fields(row):
    keys = row.keys()
    # FIXME: Alternately we can accept `lat`, `lng` and `address`
    return 'stop_id' in keys

def read_csv(file):
    with open(file) as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
        if not rows:
            raise ValueError('The provided CSV file is empty')
        if not validate_csv_fields(rows[0]):
            raise ValueError('Make sure the provided CSV file contains a column `stop_id`')
        return rows

class VbbRestJourneysSpider(scrapy.Spider):
    name = 'VbbRestJourneys'
    api_url = 'https://v5.vbb.transport.rest/'

    def __init__(self,
                 source_csv=None,
                 destination_csv=None,
                 departure=None,
                 arrival=None,
                 excluded_products='',
                 *args, **kwargs):
        super(VbbRestJourneysSpider, self).__init__(*args, **kwargs)

        if not source_csv:
            raise ValueError('Please provide a source CSV file containing trip starting points using `-a source_csv=...`')
        if not destination_csv:
            raise ValueError('Please provide a destination CSV file containing trip starting points using `-a destination_csv=...`')
        if departure and arrival:
            raise ValueError('Departure and arrival are mutually exclusive! Only one can be used at a time')

        self.sources = read_csv(source_csv)
        self.destinations = read_csv(destination_csv)
        self.departure = departure
        self.arrival = arrival
        self.start_urls = []

        self.excluded_products = excluded_products.split(',')

    def start_requests(self):
        # this is where we build the cartesian product of source and dest and
        # construct all requests. what we need is a stop_id for source and dest.
        for source in self.sources:
            for destination in self.destinations:
                # see https://v5.vbb.transport.rest/api.html#get-journeys for
                # documentation on the available parameters
                request_params = {
                    'from': source.get('stop_id'),
                    'to': destination.get('stop_id'),
                    'tickets': True
                }

                if self.departure:
                    request_params['departure'] = self.departure
                elif self.arrival:
                    request_params['arrival'] = self.arrival

                for product in self.excluded_products:
                    request_params[product] = False

                yield scrapy.Request(self.api_url + 'journeys?'  + urlencode(request_params),
                                     callback=self.handle_journeys,
                                     cb_kwargs={'source': source,
                                                'dest': destination})

    def handle_journeys(self, response, source, dest):
        # again, see the api docs at https://v5.vbb.transport.rest/api.html#get-journeys
        body = json.loads(response.text)
        for journey in body['journeys']:
            journey.update(**{
                'source': source,
                'destination': dest
            })
            yield journey
