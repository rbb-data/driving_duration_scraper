# Driving Duration Scraper

This is a generic scraper for driving durations using open APIs.

## How to use it

To use this scraper:

1. Install [poetry](https://github.com/python-poetry/poetry) to manage the python dependencies (see the link for instructions).
2. From within the project root, run `poetry install` which fetches all required dependencies.
3. Interact with the scrapers below by running `poetry run scrapy runspider …` (see the different scrapers for details)

## OpenRouteService

The scraper works by providing the paths of two CSV files when invoking it. It will build the cartesian product of all items in the two files and return routing information from [OpenRouteService](https://openrouteservice.org/).

### Usage

We need two CSV files, each **require** the fields `lat` and `lng`. Any other field will be kept around but is not required.

`sources.csv`:

```
id,lat,lng,name
1,52.5033,13.3848,Berlin
```

`destinations.csv`

```
id,lat,lng,name
1,51.7784,14.3875,Cottbus
```

Invocation:

``` bash
poetry run scrapy crawl OpenRouteService \
  -a api_key=YOUR_API_TOKEN \
  -a source_csv=sources.csv \
  -a destination_csv=destinations.csv \
  -o output.json
```

The `api_key` can be copy-and-pasted from the OpenRouteService UI. The two CSV files are the paths given above. `-o output.json` determines the name and format of the file that stores all scraper results.

You can also pass `-a profile=...` to customize the way the driving duration and distance are calculated (more in the [api documentation](https://openrouteservice.org/dev/#/api-docs/v2/directions/{profile}/get)).

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
