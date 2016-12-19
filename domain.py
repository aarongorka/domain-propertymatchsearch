#!/usr/bin/env python
import os, sys
import urllib.request
import json
import pickle as pickle
from flask import Flask,jsonify,request
import gpxpy.geo
import logging
import argparse
import time
from functools import partial
from multiprocessing.dummy import Pool as ThreadPool
import itertools

# Cache results to prevent unintentional abuse of production API. Set "cache" to true to save results to disk and use them in subsequent requests.
cache = False
def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

def get_listings():
    """Returns a list of listings on the first page"""
    file_exists = False
    if cache:
        try:
            file_exists = os.stat("domain.pkl")
        except:
            pass
    if cache == True and file_exists:
        r = pickle.load(open('domain.pkl'))
    else:
        logging.info('Pulling 1st page of listings...')
        with urllib.request.urlopen('https://rest.domain.com.au/searchservice.svc/search?regions=Sydney%20Region&state=NSW&pcodes=2000') as url:
            result = url.read().decode('UTF-8') # .read().decode('UTF-8') required for python3 urllib
        r = json.loads(result)
        logging.debug('Listings: {}'.format(r))
        if cache:
            save_object(r, 'domain.pkl')
    listings = r['ListingResults']['Listings']
    return listings

def get_standard_info(Listing):
    """Filters standard listing info to desired properties"""
    infos = []
    # dict comprehension to filter to desired properties
    infos = {k: v for k, v in Listing.items() if k in ['AdId', 'Bathrooms','Bedrooms','Carspaces','Headline','DateUpdated','Latitude','Longitude','Region']}
    return infos

def get_detailed_info(AdId):
    """Returns extended detail set for a given AdId"""
    file_exists = False
    if cache:
        try:
            file_exists = os.stat("domain_{}.pkl".format(AdId))
        except:
            pass
    if cache and file_exists:
        description_result_r = pickle.load(open("domain_{}.pkl".format(AdId)))
    else:
        logging.info('Pulling detailed information for AdId: {}'.format(AdId))
        with urllib.request.urlopen('https://rest.domain.com.au/propertydetailsservice.svc/propertydetail/{}'.format(AdId)) as url:
            result = url.read().decode('UTF-8') # .read().decode('UTF-8') required for python3 urllib
        description_result_r = json.loads(result)
        logging.debug('Detailed information pulled: {}'.format(description_result_r))
        if cache:
            save_object(description_result_r, "domain_{}.pkl".format(AdId))
    return description_result_r
    
def get_description(description_result_r):
    """Extracts description string from the extended detail set"""
    description_string = description_result_r['Listings'][0]['Description']
    return description_string

def get_inspections(description_result_r):
    """Extracts inspections string from the extended detail set"""
    inspection_string = description_result_r['Listings'][0]['Inspections']
    return inspection_string

def build_listings(Listing, latitude=None, longitude=None):
    """Takes a listing and returns the listing with additional information added and unnecessary information removed"""
    AdId = Listing['AdId']
    logging.info('Building dict for AdId: {}'.format(AdId))
    standard_info = get_standard_info(Listing)
    description_result_r = get_detailed_info(AdId)
    description_string = get_description(description_result_r)
    inspection_string = get_inspections(description_result_r)
    if latitude != None and longitude != None and standard_info['Latitude'] != None and standard_info['Longitude'] != None:
        dist = {}
        try:
            dist = {u'Distance': gpxpy.geo.haversine_distance(float(standard_info['Latitude']), float(standard_info['Longitude']), float(latitude), float(longitude))} # calculate distance in meters
        except:
            logging.critical('Error occurred calculating distance with arguments {}, {}, {} and {} for AdId {}'.format(standard_info['Latitude'], standard_info['Longitude'], latitude, longitude, AdId))
            dist = {u'Distance': []}
        logging.debug('Updating standard_info with dist: {}'.format(dist))
        standard_info.update(dist)
    listing_dict = {}
    for d in (standard_info, {u'Description': description_string, u'Inspections': inspection_string}):
        logging.debug('Merging {} in to listing_dict'.format(d))
        listing_dict.update(d)
    logging.debug('Appending dict to return_object: {}'.format(listing_dict))
    logging.info('Dict built for AdId: {}'.format(AdId))
    return listing_dict

def build_response(**kwargs):
    """Returns a list of property listings as per required specification"""
    start = time.time()
    logging.info('Building response object')
    return_object = []
    # parallel downloads for faster response; brings the total time from ~16s to ~1s
    listings = get_listings()
    pool = ThreadPool(len(listings))
    if 'latitude' in kwargs and 'longitude' in kwargs:
        logging.info('latitude and longitude arguments passed')
        return_object = pool.starmap(build_listings, zip(listings, itertools.repeat(kwargs['latitude']), itertools.repeat(kwargs['longitude'])))
    else:
        logging.info('latitude and longitude absent')
        return_object = pool.starmap(build_listings, zip(listings))
    pool.close()
    pool.join() # wait for parallel requests to complete
    logging.info('Return object build in {}.'.format(time.time() - start))
    return return_object

app = Flask(__name__)
@app.route('/PropertyMatchSearch', methods=['GET'])
def get_property_match_search():
    try:
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')
    except:
        pass
    if latitude and longitude:
        return jsonify(build_response(latitude=latitude, longitude=longitude))
    else:
        return jsonify(build_response())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # pass --debug to enable flask debug and debug logging
    parser.add_argument('--debug', '-d', action='store_true', dest='debug_enabled', help='Enable verbose output')
    args = parser.parse_args()
    if args.debug_enabled:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
        logging.info('Starting up...')
        app.run(host='0.0.0.0', debug=True)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        logging.info('Starting up...')
        app.run(host='0.0.0.0')
