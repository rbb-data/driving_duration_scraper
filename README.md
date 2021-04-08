# Driving Duration Scraper

This is a generic scraper for driving durations using open APIs.

## How to use it

To use this scraper:

1. Install [poetry](https://github.com/python-poetry/poetry) to manage the python dependencies (see the link for instructions).
2. From within the project root, run `poetry install` which fetches all required dependencies.
3. Interact with the scrapers below by running `poetry run scrapy runspider …` (see the different scrapers for details)

## OpenRouteService

OpenRouteService can perform different kinds of distance calculations if you are looking to estimate distances by car, by foot, in a wheelchair, or by bike. If you need public transit, see the section on VbbRest below.

The scraper works by providing the paths of two CSV files when invoking it. It will build the cartesian product of all items in the two files and return routing information from [OpenRouteService](https://openrouteservice.org/).

### Usage

We need two CSV files, each **require** the fields `lat` and `lng`. Any other field will be kept around but is not required.

`examples/sources.csv`:

```
id,lat,lng,name
1,52.5033,13.3848,Berlin
```

`examples/destinations.csv`

```
id,lat,lng,name
1,51.7784,14.3875,Cottbus
```

Invocation:

``` bash
poetry run scrapy crawl OpenRouteService \
  -a api_key=YOUR_API_TOKEN \
  -a source_csv=examples/sources.csv \
  -a destination_csv=examples/destinations.csv \
  -o output.json
```

The `api_key` can be copy-and-pasted from the OpenRouteService UI. The two CSV files are the paths given above. `-o output.json` determines the name and format of the file that stores all scraper results.

You can also pass `-a profile=...` to customize the way the driving duration and distance are calculated (more in the [api documentation](https://openrouteservice.org/dev/#/api-docs/v2/directions/{profile}/get)). Interesting profiles might be `driving-car`, `cycling-regular`, `wheelchair` or `foot-walking`.

The response is an array of GeoJSON features. Each feature represents one trip. The most important properties are `properties.summary`, `properties.source` and `properties.destination`.

Read the comments below that aim to help understanding the result:

``` js
[
  {
    "bbox": [
      13.383565,
      51.722495,
      14.388388,
      52.503489
    ],
    "type": "Feature",
    "properties": {
      "segments": [
        {
          "distance": 130873.1, // segment distance driven in meters; may be less than total distance (see "summary" below)
          "duration": 6042.1, // segment duration in seconds
          "steps": [
            {
              "distance": 19.9,
              "duration": 4.8,
              "type": 11,
              "instruction": "Head southwest",
              "name": "-",
              "way_points": [
                0,
                1
              ]
            },
            // many more steps with durations, distances and instructions
          ]
        }
      ],
      "summary": {
        "distance": 130873.1, // ← !! total distance driven in meters
        "duration": 6042.1 // ← !! total trip duration in seconds
      },
      "way_points": [
        0,
        1171
      ],
      "source": {
        // contains the complete source row of your csv for matching
        "id": "1",
        "lat": "52.5033",
        "lng": "13.3848",
        "name": "Berlin"
      },
      "destination": {
        // contains the complete destination row of your csv for matching
        "id": "1",
        "lat": "51.7784",
        "lng": "14.3875",
        "name": "Cottbus"
      }
    },
    "geometry": {
      "coordinates": [
        [
          13.384808,
          52.503294
        ],
        // many more coordinates so you can draw a detailed shape
      ],
      "type": "LineString"
    }
  }
]

```

## VBB-Rest

- https://v5.vbb.transport.rest/

### Usage

The VBB Rest API needs stop ids to calculate trips. These are provided, as above, in a designated row of the input and output CSV files. If your CSV contains only `lat` and `lng`, you can call `VbbRestStopIds` to fetch the closest stop for you.

If you CSVs already contain a `stop_id` column that can be consumed by the VBB Rest API, you can skip the next section.

#### Figuring Out The Closest Stop

Given the same `source.csv` as above:

``` bash
poetry run scrapy crawl VbbRestStopIds \
  -a source_csv=examples/sources.csv \
  -o source_stops.csv
```

Results in the following CSV:

```
id,lat,lng,name,stop_id,stop_name,stop_lat,stop_lng,stop_distance,stop_products
1,52.5033,13.3848,Berlin,900000012101,S Anhalter Bahnhof,52.504537,13.38208,230,"suburban,bus"
```

You can also tell the scraper to exclude some transit types (separated with `,`) when considering the closest stop. Available transit types are `suburban`, `subway`, `tram`, `bus`, `ferry`, `express` and `regional` (you can [read the API documentation](https://v5.vbb.transport.rest/api.html#get-journeys) for more information about what exactly these types mean):

``` bash
poetry run scrapy crawl VbbRestStopIds \
  -a source_csv=examples/sources.csv \
  -a excluded_products=suburban,bus \
  -o source_stops.csv
```

Results in the following result, because Möckernbrücke offers a subway:

```
id,lat,lng,name,stop_id,stop_name,stop_lat,stop_lng,stop_distance,stop_products
1,52.5033,13.3848,Berlin,900000017104,U Möckernbrücke,52.498945,13.383257,495,"subway,bus"
```

The CSV just generated can be used as input for the next scraper.

#### Journey Information

The following invocation will calculate trips from any row in `sources.csv` to any row in `destinations.csv`.

``` bash
poetry run scrapy crawl VbbRestJourneys \
  -a source_csv=examples/sources.csv \
  -o source_stops.csv
```

Additional, optional arguments are:

- Either `-a departure=...` or `-a arrival=...`
  - By default it will assume that you want to depart now, and date / time parameters can be passed like [described in the API documentation](https://v5.vbb.transport.rest/api.html#datetime-parameters) (e.g. `today 2pm`, `2020-04-29T19:30:00+02:00` or any unix timestamp).
- `-a excluded_products`, which is a comma-separated list as described in the previous section

##### Example

Given two CSVs, each with a column `stop_id`:

`sources.csv`:

```
id,lat,lng,name,stop_id,stop_name,stop_lat,stop_lng,stop_distance,stop_products
1,52.5033,13.3848,Berlin,900000012101,S Anhalter Bahnhof,52.504537,13.38208,230,"suburban,bus"
```

`destinations.csv`:

```
id,lat,lng,name,stop_id,stop_name,stop_lat,stop_lng,stop_distance,stop_products
1,52.5033,13.3848,Berlin,900000017104,U Möckernbrücke,52.498945,13.383257,495,"subway,bus"
```

You can find out information about trips that started at S Anhalter Bahnhof and arrived at 10am today like so:

``` bash
poetry run scrapy crawl VbbRestJourneys -a source_csv=source_stops.csv -a destination_csv=source_stops_excluded.csv -a arrival='today 10am' -o trips_today_10am.jl
```

Where the last trip returned looks like this (the order is as you'd expect in your public transit app, with the last trip is the one immediately before your deadline):

``` js
{
  "type": "journey",
  "legs": [
    // a leg is a single stop in the joruney
    {
      "origin": {
        "type": "stop",
        "id": "900000012101",
        "name": "S Anhalter Bahnhof",
        "location": {
          "type": "location",
          "id": "900012101",
          "latitude": 52.504537,
          "longitude": 13.38208
        },
        "products": {
          "suburban": true,
          "subway": false,
          "tram": false,
          "bus": true,
          "ferry": false,
          "express": false,
          "regional": false
        }
      },
      "destination": {
        "type": "stop",
        "id": "900000012151",
        "name": "Willy-Brandt-Haus",
        "location": {
          "type": "location",
          "id": "900012151",
          "latitude": 52.500411,
          "longitude": 13.387437
        },
        "products": {
          "suburban": false,
          "subway": false,
          "tram": false,
          "bus": true,
          "ferry": false,
          "express": false,
          "regional": false
        }
      },
      "departure": "2021-04-08T09:50:00+02:00",
      "plannedDeparture": "2021-04-08T09:50:00+02:00",
      "departureDelay": null,
      "arrival": "2021-04-08T09:51:00+02:00",
      "plannedArrival": "2021-04-08T09:51:00+02:00",
      "arrivalDelay": null,
      "reachable": true,
      "tripId": "1|22282|23|86|8042021",
      "line": {
        "type": "line",
        "id": "m41",
        "fahrtNr": "36959",
        "name": "M41",
        "public": true,
        "adminCode": "BVB",
        "mode": "bus",
        "product": "bus",
        "operator": {
          "type": "operator",
          "id": "berliner-verkehrsbetriebe",
          "name": "Berliner Verkehrsbetriebe"
        },
        "symbol": "M",
        "nr": 41,
        "metro": true,
        "express": false,
        "night": false
      },
      "direction": "Sonnenallee/Baumschulenstr.",
      "arrivalPlatform": null,
      "plannedArrivalPlatform": null,
      "departurePlatform": null,
      "plannedDeparturePlatform": null,
      "cycle": {
        "min": 540,
        "max": 600,
        "nr": 13
      }
    }, // ... followed by other stops in the journey
  ],
  // this token can be used to continuously refresh information about the trip,
  // so you can keep the delay information up-to-date
  // the endpoint is described here: https://v5.vbb.transport.rest/api.html#get-journeysref
  "refreshToken": "¶HKI¶T$A=1@O=S Anhalter Bahnhof (Berlin)@L=900012101@a=128@$A=1@O=Willy-Brandt-Haus (Berlin)@L=900012151@a=128@$202104080950$202104080951$     M41$$1$$$$§G@F$A=1@O=Willy-Brandt-Haus (Berlin)@L=900012151@a=128@$A=1@O=U Möckernbrücke (Berlin)@L=900017104@a=128@$202104080951$202104081000$$$1$$$$¶GP¶ft@0@2000@120@0@100@1@@0@@@@@false@0@-1@0@-1@-1@$f@$f@$f@$f@$f@$§bt@0@2000@120@0@100@1@@0@@@@@false@0@-1@0@-1@-1@$f@$f@$f@$f@$f@$§tt@0@250000@120@0@100@1@@0@@@@@false@0@-1@0@-1@-1@$t@0@250000@120@0@100@1@@0@@@@@false@0@-1@0@-1@-1@$t@0@0@0@0@100@-1@0@0@@@@@false@0@-1@0@-1@-1@$f@$f@$f@$§",
  // how often does this type of journey repeat?
  "cycle": {
    "min": 540
  },
  "tickets": [
    // you can even get information about ticket offers
    {
      "name": "Berlin Kurzstrecke (Via: Kurzstrecke): Kurzstrecke – Regeltarif",
      "price": 2,
      "tariff": "Berlin",
      "coverage": "short trip",
      "variant": "adult",
      "amount": 1,
      "shortTrip": true
    },
    // … followed by more ticket information
  ],
  "source": {
    // this can be used to match the row in your source csv
    "id": "1",
    "lat": "52.5033",
    "lng": "13.3848",
    "name": "Berlin",
    "stop_id": "900000012101",
    "stop_name": "S Anhalter Bahnhof",
    "stop_lat": "52.504537",
    "stop_lng": "13.38208",
    "stop_distance": "230",
    "stop_products": "suburban,bus"
  },
  "destination": {
    // this can be used to match the row in your destination csv
    "id": "1",
    "lat": "52.5033",
    "lng": "13.3848",
    "name": "Berlin",
    "stop_id": "900000017104",
    "stop_name": "U Möckernbrücke",
    "stop_lat": "52.498945",
    "stop_lng": "13.383257",
    "stop_distance": "495",
    "stop_products": "subway,bus"
  }
}
```

If you want to calculate the total trip time for example, you can use the following code in Python 3.7:

``` python
# assume that the journey above is available as `journey`
import datetime

start_time = datetime.datetime.strptime(journey['legs'][0]['departure'], "%Y-%m-%dT%H:%M:%S%z")
end_time = datetime.datetime.strptime(journey['legs'][-1]['arrival'], "%Y-%m-%dT%H:%M:%S%z")

end_time - start_time
# → datetime.timedelta(seconds=600)
```
