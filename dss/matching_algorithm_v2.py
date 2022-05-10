# New version (Angel edits)

from collections import defaultdict
from sqlalchemy.inspection import inspect
import pandas as pd
from dss.models import (User, Materials, Giveoutwaste,TechnologyDB)
from dss.wasteIdGenerator import breakId


def matching_algorithm_seller(giveoutwasteId):

    wasteID = Giveoutwaste.query.filter_by(id=giveoutwasteId).first().questionCode
    wastematerialID = Giveoutwaste.query.filter_by(id=giveoutwasteId).first().materialId

    waste_tech_dict = {'1':14, '2':[20,21,22,23,24,25,26], '3':27, '12':15, '4':16}

    tech_materialid = waste_tech_dict[str(wastematerialID)]

    if wastematerialID ==1:
 
        waste = breakId(wastematerialID, wasteID)

        query = TechnologyDB.query.filter(TechnologyDB.materialId == tech_materialid, TechnologyDB.CRatiomin <= waste.wCRatio, TechnologyDB.CRatiomax >= waste.wCRatio, 
                                            TechnologyDB.NRatiomin <= waste.wNRatio, TechnologyDB.NRatiomax >= waste.wNRatio, 
                                            TechnologyDB.pHmin <= waste.wphValue, TechnologyDB.pHmax >= waste.wphValue)


    elif wastematerialID == 4:

        waste = breakId(wastematerialID, wasteID)

        query = TechnologyDB.query.filter(TechnologyDB.materialId == tech_materialid, TechnologyDB.Moisturemin <= waste.moistureContent, TechnologyDB.Moisturemax >= waste.moistureContent)



    elif wastematerialID == 12:

        waste = breakId(wastematerialID, wasteID)

        query = TechnologyDB.query.filter(TechnologyDB.materialId == tech_materialid, TechnologyDB.Moisturemin <= waste.moistureContent, TechnologyDB.Moisturemax >= waste.moistureContent)


    else:

        query = TechnologyDB.query.filter(TechnologyDB.materialId == tech_materialid)

    result = []
    index = 1
    for row in query:
        supplier=(User.query.filter_by(id=row.userId).first().username)
        result.append([index, row.description, supplier, row.date[:10], row.url])
        index +=1

    return result

def matching_algorithm_rsp(processwasteId):

    techmaterialID = TechnologyDB.query.filter_by(id=processwasteId).first().materialId
    techmaterialID = int(techmaterialID)

    tech = TechnologyDB.query.filter_by(id=processwasteId).first()

    tech_waste_dict = {'14':[1], '27':[3], '15':[12], '16':[4]}

    wastematerialID = tech_waste_dict[str(techmaterialID)]
    result = []

    #for item in wastematerialID:
    query = Giveoutwaste.query.filter(Giveoutwaste.materialId.in_(wastematerialID)).all()

    index = 1

    for entry in query:
        wasteID = entry.questionCode
        waste = breakId(entry.materialId, wasteID) 


        if techmaterialID == 14:           
            if int(waste.wCRatio)>= tech.CRatiomin and int(waste.wCRatio) <= tech.CRatiomax and \
                int(waste.wNRatio)>= tech.NRatiomin and int(waste.wNRatio) <= tech.NRatiomax:
                 #int(waste.moistureContent)>= tech.Moisturemin and int(waste.moistureContent) <= tech.Moisturemax and \
                    #int(waste.wphValue)>= tech.pHmin and int(waste.wphValue) <= tech.pHmax
                        #int(waste.homogeneity)>= tech.Homogeneitymin and int(waste.homogeneity) <= tech.Homogeneitymax:
                
                supplier=(User.query.filter_by(id=entry.userId).first().username)
                date=str(entry.date)[:10]

                result.append([index, entry.description, supplier, date])

                index += 1
    

        if techmaterialID == 15:           
            if int(waste.moistureContent)>= tech.Moisturemin and int(waste.moistureContent) <= tech.Moisturemax and \
                    int(waste.size)>= tech.particleSizemin and int(waste.size) <= tech.particleSizemax:
                        #int(waste.homogeneity)>= tech.Homogeneitymin and int(waste.homogeneity) <= tech.Homogeneitymax:
                
                supplier=(User.query.filter_by(id=entry.userId).first().username)
                date=str(entry.date)[:10]

                result.append([index, entry.description, supplier, date])

                index += 1


        if techmaterialID == 16:           
            if int(waste.moistureContent)>= tech.Moisturemin and int(waste.moistureContent) <= tech.Moisturemax:
                        #int(waste.homogeneity)>= tech.Homogeneitymin and int(waste.homogeneity) <= tech.Homogeneitymax:
                
                supplier=(User.query.filter_by(id=entry.userId).first().username)
                date=str(entry.date)[:10]

                result.append([index, entry.description, supplier, date])

                index += 1

    return result