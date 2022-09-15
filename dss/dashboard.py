from dss import db
from dss.models import (User,Dispatchmatchingresults, Dispatchmatchingsupply, Dispatchmatchingdemand, Technology, Waste)
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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

    #~~~~~~~~~~~ SQL query to get raw data
    result_time = db.session.query(
            User, Waste, Dispatchmatchingresults, 
        ).filter(
            User.id == Waste.userId,
        ).filter(
            Waste.id == Dispatchmatchingresults.supplyId,
        ).filter(
            User.id != 0,
        ).all()

    #~~~~~~~~~~~ Compute timeframe
    end_date = datetime.today()
    start_date_3m = end_date + relativedelta(months=-3)
    start_date_6m = end_date + relativedelta(months=-6)
    start_date_1y =  end_date + relativedelta(months=-12)

    list_3m = []
    list_6m = []
    list_1y = []

    for user,waste,dispatch, *_ in result_time:
        record_date = datetime.strptime(dispatch.date.strip(), '%d/%m/%Y')
        if record_date > start_date_3m:
            list_3m.append([waste.materialType, dispatch.quantity, record_date])

        if record_date > start_date_6m:
            list_6m.append([waste.materialType, dispatch.quantity, record_date])

        if record_date > start_date_1y:
            list_1y.append([waste.materialType, dispatch.quantity, record_date])

    
    data_bytime = {}

    data_bytime['xvalue'], data_bytime['legend'], data_bytime['yvalue_sum'], data_bytime['yvalue_count'] = DataByTime(result_time, list_3m)


    result_total = db.session.query(
            User, Waste, Dispatchmatchingresults, db.func.sum(Dispatchmatchingresults.quantity), db.func.count(Dispatchmatchingresults.quantity)
        ).filter(
            User.id == Waste.userId,
        ).filter(
            Waste.id == Dispatchmatchingresults.supplyId,
        ).filter(
            User.id != 0,
        ).group_by(Dispatchmatchingresults.materialId).all()

    data_bylife = {}
    data_bylife['yvalue_sum'] = []
    data_bylife['yvalue_count'] = []
    data_bylife['legend'] = []

    for user,waste,dispatch, amount, count in result_total:
        data_bylife['legend'].append(str(waste.materialType).replace("'",'"'))
        data_bylife['yvalue_sum'].append(amount)
        data_bylife['yvalue_count'].append(count)



    return data_bytime, data_bylife