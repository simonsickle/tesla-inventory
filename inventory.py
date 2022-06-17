#!/usr/bin/env python3
import argparse
from ast import parse
import json
import requests

# Constants - to be updated on new cars
baseUrl = 'https://www.tesla.com/inventory/api/v1/inventory-results'
models = ['S', '3', 'X', 'Y']
conditions = ['new', 'used']

# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', metavar="", type=str, required=True, help=f"Model {models}")
parser.add_argument('-c', '--condition', metavar="", type=str, required=True, help=f"Condition of vehicle (new/used)")
parser.add_argument('-l', '--limit', metavar="", type=int, default=100, help='Max number of cars to return')
parser.add_argument('-lat', '--latitude', metavar="", type=float, help='Latitude to use for search')
parser.add_argument('-lng', '--longitude', metavar="", type=float, help='Longitude to use for search')
parser.add_argument('-dist', '--distance', metavar="", type=int, help='Max distance in miles from coordinates')
parser.add_argument('-v', '--verbose', help='Print more detailed information, useful for debugging', action='store_true')
args = parser.parse_args()

# Validation
if args.model.upper() not in models:
    exit(f"Model ${args.model} is not a valid Tesla model.")
if args.condition not in conditions:
    exit(f"Only these conditions are allowed {conditions}")
if (args.latitude is not None and args.longitude is None) or (args.latitude is None and args.longitude is not None):
    exit('Lat / Lng must be provided together')
if args.distance is not None and args.distance > 200:
    exit('Max distance can only be set to 200mi at most')

def get_cars_with_offset(model, offset = 0):
    query = {
        'query': {
            'model': f"m{model.upper()}",
            'condition': args.condition.lower(),
            'market': 'US',
            'language': 'en',
            'super_region': "north america"
        },
        'offset': offset,
        'count': 50,
    }

    # Geolocation queries for relevance
    query['query']['lat'] = args.latitude if args.latitude is not None else None
    query['query']['lng'] = args.longitude if args.longitude is not None else None
    query['query']['range'] = args.distance if args.distance is not None else None

    req = requests.get(baseUrl, params= {'query': json.dumps(query)})
    if req.status_code != 200:
        exit(f"Got bad status on API request ${req.status_code}")

    resp = req.json()
    
    areMoreAvailable = len(resp['results']) < int(resp['total_matches_found'])
    return areMoreAvailable, resp

def get_all_cars(model):
    cars = []
    more_available = True
    current_offset = 0

    while more_available:
        more_available, resp = get_cars_with_offset(model, offset = current_offset)
        current_offset += len(resp['results'])
        
        if len(resp['results']) > 0:
            cars += resp['results']

        if (len(cars) >= args.limit):
            more_available = False
    
    return cars

def print_car_details(car):
    output = []

    # Type and location
    output.append(car['TrimName'])

    # Detect pickup location
    if 'SalesMetro' in car:
        output.append(f" in {car['SalesMetro']}, {car['StateProvince']}\n")
    else:
        output.append('needing transfer\n')
        
    # Price
    output.append(f"is selling for {car['TotalPrice']} with {car['Odometer']}mi")

    # Tell people that it is a demo car, and not TRUELY new
    output.append(' and is a demo.\n' if car['IsDemo'] else '.\n')

    # Purchase URL for easy clicking
    output.append(f"https://www.tesla.com/m3/order/{car['VIN']}")

    # Separate with a line
    output.append(f"\n{'-'*80}")

    print(''.join(output))

def main():
    cars = get_all_cars(args.model)

    for car in cars:
        print_car_details(car)

    if args.verbose:
        print(f"\n\nFound {len(cars)} available in your search (limited to {args.limit})")

if __name__ == "__main__":
    main()