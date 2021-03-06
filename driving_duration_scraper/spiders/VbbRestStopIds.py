import scrapy
import csv
import json
from urllib.parse import urlencode


def validate_csv_fields(row):
    keys = row.keys()
    return 'lat' in keys and 'lng' and 'address' in keys

def read_csv(file):
    with open(file) as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
        if not rows:
            raise ValueError('The provided CSV file is empty')
        if not validate_csv_fields(rows[0]):
            raise ValueError('Make sure the provided CSV file contains the columns `lat` and `lng` and `address` (for example the city name)')
        return rows

class VbbRestStopIdsSpider(scrapy.Spider):
    name = 'VbbRestStopIds'
    api_url = 'https://v5.vbb.transport.rest/'

    def __init__(self,
                 source_csv=None,
                 excluded_products='',
                 *args, **kwargs):
        super(VbbRestStopIdsSpider, self).__init__(*args, **kwargs)

        if not source_csv:
            raise ValueError('Please provide a CSV file containing trip starting points using `-a source_csv=...`')

        self.sources = read_csv(source_csv)
        self.start_urls = []
        self.excluded_products = excluded_products.split(',')

    def start_requests(self):
        # this is where we build the cartesian product of source and dest and
        # construct all requests. what we need is a stop_id for source and dest.
        for source in self.sources:
            request_params = {
                'address': source.get('address'),
                'latitude': source.get('lat'),
                'longitude': source.get('lng')
            }

            for product in self.excluded_products:
                request_params[product] = False

            yield scrapy.Request(self.api_url + 'stops/reachable-from?'  + urlencode(request_params),
                                 callback=self.handle_stops,
                                 cb_kwargs={'location': source})

    def handle_stops(self, response, location):
        # see https://v5.vbb.transport.rest/api.html#get-stopsreachable-from
        body = json.loads(response.text)

        # these are grouped by duration
        for item in body:
            for stop in item['stations']:
                location.update(**{
                    'stop_id': stop['id'],
                    'stop_duration': item['duration'],
                    'stop_name': stop['name'],
                    'stop_lat': stop['location']['latitude'],
                    'stop_lng': stop['location']['longitude'],
                    'stop_products': ','.join([product for product, is_offered in stop['products'].items() if is_offered])
                })
                break

            # break out of outer loop
            if location.get('stop_id'):
                break

        # make it explicit if we didn't find any stop that matches our expectations
        if not location.get('stop_id'):
            location.update(**{
                'stop_id': None,
                'stop_name': None,
                'stop_lat': None,
                'stop_lng': None,
                'stop_distance': None,
                'stop_products': None
            })

        yield location
