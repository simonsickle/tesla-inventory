#!/usr/bin/env python3
import argparse
import sys
import json

import requests

# Constants - to be updated on new cars
baseUrl = 'https://www.tesla.com/inventory/api/v1/inventory-results'
models = ["S", "3", "X", "Y"]
conditions = ["new", "used"]

# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', metavar="", type=str, required=True, help=f"Model {models}")
parser.add_argument('-c', '--condition', metavar="", type=str, required=True, help=f"Condition of vehicle (new/used)")
parser.add_argument('-l', '--limit', metavar="", type=int, default=100, help='Max number of cars to return')
parser.add_argument('-lat', '--latitude', metavar="", type=float, help='Latitude to use for search')
parser.add_argument('-lng', '--longitude', metavar="", type=float, help='Longitude to use for search')
parser.add_argument('-dist', '--distance', metavar="", type=int, help='Max distance in miles from coordinates')
args = parser.parse_args()

# Validation
if args.model.upper() not in models:
    sys.exit(f"Model ${args.model} is not a valid Tesla model.")
if args.condition not in conditions:
    sys.exit(f"Only these conditions are allowed {conditions}")
if args.latitude is not None and args.longitude is None:
    sys.exit("Lat / Lng must be provided together")
if args.latitude is None and args.longitude is not None:
    sys.exit("Lat / Lng must be provided together")
if args.distance is not None and args.latitude is None and args.longitude is None:
    sys.exit("Lat / Lng must be provided with max distance")
if args.distance is not None and args.distance > 200:
    sys.exit("Max distance can only be set to 200mi at most")

def getCarsWithOffset(model, offset = 0):
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
    if args.latitude is not None:
        query['query']['lat'] = args.latitude
    if args.longitude is not None:
        query['query']['lng'] = args.longitude
    if args.distance is not None:
        query['query']['range'] = args.distance

    r = requests.get(baseUrl, params= {'query': json.dumps(query)})
    if r.status_code != 200:
        sys.exit(f"Got bad status on API request ${r.status_code}")

    resp = r.json()
    
    areMoreAvailable = len(resp['results']) < int(resp['total_matches_found'])
    return areMoreAvailable, resp

def getAllCars(model):
    cars = []
    moreAvailable = True
    currentOffset = 0

    while moreAvailable:
        moreAvailable, resp = getCarsWithOffset(model, offset= currentOffset)
        currentOffset += len(resp['results'])
        
        if len(resp['results']) > 0:
            cars += resp['results']

        if (len(cars) >= args.limit):
            moreAvailable = False
    
    return cars

def printCarDetails(car):
    # Type and location
    output = f"{car['TrimName']}"

    # Detect pickup location
    if 'SalesMetro' in car:
        output += f" in {car['SalesMetro']}, {car['StateProvince']}\n"
    else:
        output += " needing transfer\n"
        
    # Price
    output += f"is selling for {car['TotalPrice']} with {car['Odometer']}mi"
    # Tell people that it is a demo car, and not TRUELY new
    if car['IsDemo']:
        output += " and is a demo.\n"
    else:
        output += ".\n"

    # Purchase URL for easy clicking
    output += f"https://www.tesla.com/m3/order/{car['VIN']}"

    # Separate with a line
    output += f"\n{'-'*80}"

    print(output)

def main():
    cars = getAllCars(args.model)

    for car in cars:
        printCarDetails(car)

    print(f"\n\nFound {len(cars)} available in your search (limited to {args.limit})")

if __name__ == "__main__":
    main()