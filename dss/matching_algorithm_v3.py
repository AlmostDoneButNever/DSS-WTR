# New version (Angel edits)

from collections import defaultdict
from operator import contains, or_, and_
from sqlalchemy.inspection import inspect
import pandas as pd
from dss.models import (User, MaterialsDB, WasteDB,TechnologyDB)
from dss.wasteIdGenerator import breakId
from sqlalchemy.sql.functions import coalesce


###########################################       Matching Algorithm for Waste Sellers      ############################


def matching_algorithm_seller(giveoutwasteId):

    waste = WasteDB.query.filter_by(id=giveoutwasteId).first()

 
    query = TechnologyDB.query.filter(TechnologyDB.materialId == str(waste.materialID),
                                        or_(and_(coalesce(TechnologyDB.CN_min, 0) <= waste.CNratio, coalesce(TechnologyDB.CN_max, 999) >= waste.CNratio), waste.CNratio == None),
                                        or_(and_(coalesce(TechnologyDB.pH_min, 0) <= waste.pH, coalesce(TechnologyDB.pH_max, 14) >= waste.pH), waste.pH == None),
                                        or_(and_(coalesce(TechnologyDB.cellulose_min, 0) <= waste.cellulosicValue, coalesce(TechnologyDB.cellulose_max, 100) >= waste.cellulosicValue), waste.cellulosicValue == None),
                                        or_(TechnologyDB.size.contains(coalesce(waste.size,'')), or_(TechnologyDB.size == None, waste.size == None)),
                                        or_(TechnologyDB.homogeneity.contains(coalesce(waste.homogeneityType,'')), or_(TechnologyDB.homogeneity == None, waste.homogeneityType == None)),
                                        or_(TechnologyDB.moisture.contains(coalesce(waste.moistureType,'')), or_(TechnologyDB.moisture == None, waste.moistureType == None)),
                                    )


    result = []
    index = 1
    for row in query:
        supplier=(User.query.filter_by(id=row.userId).first().username)
        result.append([index, row.description, supplier, row.date[:10]])
        index +=1

    return result


###########################################       Matching Algorithm for Recycling Service Providers      ############################

def matching_algorithm_rsp(processwasteId):

    first_tech = TechnologyDB.query.filter_by(id=processwasteId).first()
    all_tech = TechnologyDB.query.filter_by(description = first_tech.description).all()
   
    result = []

    index = 1

    for tech in all_tech:

        tech_homogeneity = tech.homogeneity.split(',')

        query = WasteDB.query.filter(WasteDB.materialID == int(tech.materialId),
                                        or_(and_(coalesce(tech.CN_min, 0) <= WasteDB.CNratio, coalesce(tech.CN_max, 999) >= WasteDB.CNratio), tech.CN_max == None),
                                        or_(and_(coalesce(tech.pH_min, 0) <= WasteDB.pH, coalesce(tech.pH_max, 14) >= WasteDB.pH), tech.pH_max == None),
                                        or_(and_(coalesce(tech.cellulose_min, 0) <= WasteDB.cellulosicValue, coalesce(tech.cellulose_max, 100) >= WasteDB.cellulosicValue), tech.cellulose_max == None),
                                        #or_(or_((coalesce(WasteDB.size,'')).in_(coalesce(tech.size,'')), tech.size == None), WasteDB.size == None),
                                        or_(or_((coalesce(WasteDB.homogeneityType,'')).in_(tech_homogeneity), tech.homogeneity == None), tech_homogeneity == None),
                                        #or_(or_((coalesce(WasteDB.moistureType,'')).in_(coalesce(tech.moisture,'')), tech.moisture == None), WasteDB.moistureType == None),
                                    )

        for entry in query:

            supplier=(User.query.filter_by(id=entry.userId).first().username)
            date=str(entry.date)[:10]

            result.append([index, entry.description, supplier, date])

            index += 1
    
    print('tech',tech.homogeneity.split(','))
    print('waste',WasteDB.homogeneityType)

    return result
