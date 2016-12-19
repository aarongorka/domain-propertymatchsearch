#!/usr/bin/env python
import os
import urllib, json
import cPickle as pickle
from flask import Flask,jsonify

dummy = True

app = Flask(__name__)

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

def get_listings():
    """Returns a list of listings on the first page"""
    file_exists = False
    if dummy:
        try:
            file_exists = os.stat("domain.pkl")
        except:
            pass
    if dummy == True and file_exists:
        r = pickle.load(open('domain.pkl'))
    else:
        result = urllib.urlopen('https://rest.domain.com.au/searchservice.svc/search?regions=Sydney%20Region&state=NSW&pcodes=2000')
        r = json.load(result.fp)
        result.close()
        save_object(r, 'domain.pkl')
    listings = r['ListingResults']['Listings']
    return listings

def get_standard_info(Listing):
    """Filters standard listing info to desired items"""
    infos = []
    infos = {k: v for k, v in Listing.items() if k in ['AdId', 'Bathrooms','Bedrooms','Carspaces','Headline','DateUpdated','Latitude','Longitude','Region']}
    return infos

def get_detailed_info(AdId):
    """Returns extended detail set for a given AdId"""
    file_exists = False
    if dummy:
        try:
            file_exists = os.stat("domain_{}.pkl".format(AdId))
        except:
            pass
    if dummy and file_exists:
        description_result_r = pickle.load(open("domain_{}.pkl".format(AdId)))
    else:
        description_result = urllib.urlopen('https://rest.domain.com.au/propertydetailsservice.svc/propertydetail/{}'.format(AdId))
        description_result_r = json.load(description_result.fp)
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

def build_response():
    return_object = []
    for Listing in get_listings():
        AdId = Listing['AdId']
        standard_info = get_standard_info(Listing)
        description_result_r = get_detailed_info(AdId)
        description_string = get_description(description_result_r)
        inspection_string = get_inspections(description_result_r)
        listing_dict = {}
        for d in (standard_info, {u'Description': description_string, u'Inspections': inspection_string}):
            listing_dict.update(d)
        return_object.append(listing_dict)
    return return_object

@app.route('/PropertyMatchSearch', methods=['GET'])
def get_property_match_search():
    return jsonify(build_response())

if __name__ == '__main__':
    app.run(debug=True)
