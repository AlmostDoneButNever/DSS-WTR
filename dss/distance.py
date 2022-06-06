import requests
import pandas as pd
from dss.matching_algorithm import matching_algorithm_seller

def getDistanceMatrix(seller_df, buyer_df):

    def getToken():

        # defining the api-endpoint
        API_ENDPOINT = "https://developers.onemap.sg/privateapi/auth/post/getToken"

        # data to be sent to api
        data = {
                "email": 'angelmah@nus.edu.sg',
                "password": 'wtrE2S2NUS2022'
                }

        # sending post request and saving response as response object
        r = requests.post(url = API_ENDPOINT, data = data)

        # extracting response text
        token = (r.json())['access_token']

        return token


    def getCoordinates(postal_code):

        parameters = {
            "searchVal": str(postal_code),
            "returnGeom": 'Y',
            "getAddrDetails": 'Y',
            "pageNum": '1',
        }

        response = requests.get("https://developers.onemap.sg/commonapi/search", params = parameters)

        lat = response.json()['results'][0]['LATITUDE']
        long = response.json()['results'][0]['LONGTITUDE']

        coord = lat + ',' + long
        
        return coord

    
    def getDistance(token, coord1, coord2):

        parameters = {
        "start": coord1,
        "end": coord2,
        "routeType": 'drive',
        "token": token,
        }

        response = requests.get("https://developers.onemap.sg/privateapi/routingsvc/route", params = parameters)

        if response.json()['status_message'] == 'Found route between points':

            distance = int(response.json()['route_summary']['total_distance'])/1000

            return distance

        else:
            
            return 'Error'


    potential_match = []

    for sell in seller_df.index:
        for buy in buyer_df.index:
            if (sell, buy) not in potential_match:
                potential_match.append((sell, buy))

    
    match_df = pd.DataFrame(index = pd.MultiIndex.from_tuples(potential_match, names = ['seller_id','buyer_id']), columns = ['waste_id', 'tech_id', 'seller_postal', 'buyer_postal', 'feasibility', 'distance'])
    
    for seller, buyer in match_df.index:

        match_df.loc[(seller, buyer), 'waste_id'] = seller_df.loc[seller, 'wasteId']
        match_df.loc[(seller, buyer), 'seller_postal'] = seller_df.loc[seller, 'postalCode']

        match_df.loc[(seller, buyer), 'tech_id'] = buyer_df.loc[buyer, 'techId']
        match_df.loc[(seller, buyer), 'buyer_postal'] = buyer_df.loc[buyer, 'postalCode']

        waste_id = seller_df.loc[seller, 'wasteId']
        tech_id = buyer_df.loc[buyer, 'techId']
        
        result = matching_algorithm_seller(waste_id, tech_id)

        if result:
            match_df.loc[(seller, buyer), 'feasibility'] = 1
        else:
            match_df.loc[(seller, buyer), 'feasibility'] = 0
        

    token = getToken()

    for match in match_df.index:
        if match_df.loc[match, 'feasibility'] == 1:

            seller_postal = match_df.loc[match, 'seller_postal']
            buyer_postal = match_df.loc[match, 'buyer_postal']

            if seller_postal == buyer_postal:
                match_df.loc[match, 'distance'] = 0

            else:

                coord1 = getCoordinates(seller_postal)
                coord2 = getCoordinates(buyer_postal)

                match_df.loc[match, 'distance'] = getDistance(token, coord1, coord2)

    return match_df




    


