from dss import db
from dss.models import (User,Dispatchmatchingresults, Dispatchmatchingsupply, Dispatchmatchingdemand, Technology, Waste)
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from flask_login import current_user
import json

def getHistoricalData():

    def DataByTime(query_result, time_list):

        month_dict = {1	:'JAN', 2:'FEB', 3:'MAR', 4	:'APR', 5:'MAY',
        6:'JUN', 7:'JUL',8:'AUG',9:'SEP',10:'OCT',11:'NOV',12:'DEC'
        }

        waste_list = []
        month_list = []
        trading_sum = {}
        trading_count = {}

        for waste, quantity, date in time_list:
            if waste not in waste_list:
                waste_list.append(waste)
                trading_sum[waste] = {}
                trading_count[waste] = {}

            if date.month not in month_list:
                month_list.append(date.month)

        month_list_name = []
        for month in month_list:
            m = month_dict[month]
            month_list_name.append(m)

            for waste in waste_list:
                trading_sum[waste][m] = 0
                trading_count[waste][m] = 0


        for waste, quantity, date in time_list:

            for month in month_list:
                m = month_dict[month]

                if date.month == month:
                    trading_sum[waste][m] += quantity
                    trading_count[waste][m] += 1


        trading_sum_final = []
        trading_count_final = []

        for item in waste_list:
            trading_sum_final.append(list(trading_sum[item].values()))
            trading_count_final.append(list(trading_count[item].values()))

        return month_list_name, waste_list, trading_sum_final, trading_count_final
    
    
    #~~~~~~~~~~~ Compute timeframe
    timeframe = [3, 6, 12]  #months
    end_date = datetime.today()
    start_date = {}
    for t in timeframe:
        start_date[t] = end_date + relativedelta(months=-t)
  
    
    #~~~~~~~~~~~ SQL query to get raw data for material sales and purchase
    result_time_sold = db.session.query(
            User, Waste, Dispatchmatchingresults, 
        ).filter(
            User.id == Waste.userId,
        ).filter(
            Waste.id == Dispatchmatchingresults.supplyId,
        ).filter(
            User.id != 0,
        ).all()

    result_time_purchased = db.session.query(
            User, Technology, Dispatchmatchingresults, 
        ).filter(
            User.id == Technology.userId,
        ).filter(
            Technology.id == Dispatchmatchingresults.demandId,
        ).filter(
            User.id != 0,
        ).all()

    #~~~~~~~~~~~ SQL query to get raw data for material sales and purchase (grouped by material type)
    result_total_sold = db.session.query(
            User, Waste, Dispatchmatchingresults, db.func.sum(Dispatchmatchingresults.quantity), db.func.count(Dispatchmatchingresults.quantity)
        ).filter(
            User.id == Waste.userId,
        ).filter(
            Waste.id == Dispatchmatchingresults.supplyId,
        ).filter(
            User.id != 0,
        ).group_by(Dispatchmatchingresults.materialId).all()

    result_total_purchased = db.session.query(
            User, Technology, Dispatchmatchingresults, db.func.sum(Dispatchmatchingresults.quantity), db.func.count(Dispatchmatchingresults.quantity)
        ).filter(
            User.id == Technology.userId,
        ).filter(
            Technology.id == Dispatchmatchingresults.demandId,
        ).filter(
            User.id != 0,
        ).group_by(Dispatchmatchingresults.materialId).all()
    
    def getData(result_time, result_total):

        #~~~~~~~~~~~ Group records by defined timeframe
        listed_date = {}
        for t in timeframe:
            listed_date[t] = []
            for user,waste,dispatch, *_ in result_time:
                record_date = datetime.strptime(dispatch.date.strip(), '%d/%m/%Y')

                if record_date > start_date[t]:
                    listed_date[t].append([waste.materialType, dispatch.quantity, record_date])

        data_bytime = {}
        for t in timeframe:
            data_bytime[t] = {}
            data_bytime[t]['xvalue'], data_bytime[t]['legend'], data_bytime[t]['yvalue_sum'], \
                            data_bytime[t]['yvalue_count'] = DataByTime(result_time, listed_date[t])

        #~~~~~~~~~~~ Group records by material type 
        data_bylife = {}
        data_bylife['yvalue_sum'] = []
        data_bylife['yvalue_count'] = []
        data_bylife['legend'] = []

        for user,waste,dispatch, amount, count in result_total:
            data_bylife['legend'].append(str(waste.materialType).replace("'",'"'))
            data_bylife['yvalue_sum'].append(amount)
            data_bylife['yvalue_count'].append(count)
        
        return data_bytime, data_bylife



    #~~~~~~~~~~~ Retreive data
    data = {}
    data['bytime_sold'], data['bylife_sold'] = getData(result_time_sold, result_total_sold)
    data ['bytime_purchased'], data ['bylife_purchased'] = getData(result_time_purchased, result_total_purchased)


    #~~~~~~~~~~~ SQL query to get total sales and purchase
    result_total_sold_all = db.session.query(
            db.func.sum(Dispatchmatchingresults.quantity), db.func.count(Dispatchmatchingresults.quantity)
        ).filter(
            User.id == Waste.userId,
        ).filter(
            Waste.id == Dispatchmatchingresults.supplyId,
        ).filter(
            User.id != 0,
        ).all()
    
    result_total_purchased_all = db.session.query(
            db.func.sum(Dispatchmatchingresults.quantity), db.func.count(Dispatchmatchingresults.quantity)
        ).filter(
            User.id == Technology.userId,
        ).filter(
            Technology.id == Dispatchmatchingresults.demandId,
        ).filter(
            User.id != 0,
        ).all()

    data['sold_sum'], data['sold_count'] = result_total_sold_all[0]
    data['purchased_sum'], data['purchased_count'] = result_total_purchased_all[0]

    data['sold_sum'] = data['sold_sum'] if data['sold_sum'] else 0
    data['sold_count'] = data['sold_count'] if data['sold_count'] else 0
    data['purchased_sum'] = data['purchased_sum'] if data['purchased_sum'] else 0
    data['purchased_count'] = data['purchased_count'] if data['purchased_count'] else 0

    data['total_sum'] =  data['sold_sum'] + data['purchased_sum']
    data['total_count'] = data['sold_count'] + data['purchased_count']


    #~~~~~~~~~~~ Get trading result

    def getMaterial(waste_type):
        if '{' in waste_type:

            dict = json.loads(waste_type.replace("'","\""))

            biggest_value = 0
            biggest_key = ""

            for key,value in dict.items():
                if key != "None":
                    if float(value) > biggest_value:
                        biggest_key = key
            
            material_main = biggest_key
            material_breakdown = [key for key in dict.keys() if key != "None" ]

        else:
            material_main = waste_type
            material_breakdown = waste_type

        return material_main, material_breakdown


    result_trading = db.session.query(
            Waste, Dispatchmatchingresults
        ).filter(
            User.id == Technology.userId,
        ).filter(
            Waste.id == Dispatchmatchingresults.supplyId,
        ).filter(
            User.id != None,
        ).all()

   
    waste_list = []
    waste_breakdown_list = []
    trading_price = {}

    for waste,_ in result_trading:
        material_main, material_breakdown = getMaterial(waste.type)

        if waste.materialType not in waste_list:
            waste_list.append(waste.materialType)
            trading_price[waste.materialType] = {}

        if material_main not in waste_breakdown_list:
            waste_breakdown_list.append(material_main)
            trading_price[waste.materialType][material_main] = []



    for waste, dispatch in result_trading:

        material_main, material_breakdown = getMaterial(waste.type)
        trading_price[waste.materialType][material_main].append((dispatch.date,dispatch.quantity))   

    data['trading'] = trading_price

    print(trading_price)
    return data