# New version (Angel edits)

from collections import defaultdict
from operator import contains, or_, and_
from sqlalchemy.inspection import inspect
import pandas as pd
from dss.models import (User, MaterialsDB, WasteDB,TechnologyDB)
from dss.wasteIdGenerator import breakId
from sqlalchemy.sql.functions import coalesce


###########################################       Matching Algorithm for Waste Sellers      ############################


def matching_algorithm_seller(giveoutwasteId, techId = None):

    waste = WasteDB.query.filter_by(id=int(giveoutwasteId)).first()

    if techId:
        techId = int(techId)
  
    query = TechnologyDB.query.filter(  or_(TechnologyDB.id == techId, techId == None), 
                                        TechnologyDB.materialId == str(waste.materialId), TechnologyDB.userId != waste.userId,
                                        or_(and_(coalesce(TechnologyDB.CN_min, 0) <= coalesce(waste.CNratio, 0), coalesce(TechnologyDB.CN_max, 999) >= coalesce(waste.CNratio, 0)),TechnologyDB.CN_criteria != '1'),
                                        or_(and_(coalesce(TechnologyDB.pH_min, 0) <= coalesce(waste.pH, 0), coalesce(TechnologyDB.pH_max, 14) >= coalesce(waste.pH, 0)), TechnologyDB.pH_criteria != '1'),
                                        or_(and_(coalesce(TechnologyDB.cellulose_min, 0) <= coalesce(waste.cellulosicValue, 0), coalesce(TechnologyDB.cellulose_max, 100) >= coalesce(waste.cellulosicValue, 0)), TechnologyDB.cellulose_criteria != '1'),
                                        or_(TechnologyDB.size.contains(coalesce(waste.size,'')), or_(TechnologyDB.size == None, TechnologyDB.size_criteria != '1')),
                                        or_(TechnologyDB.homogeneity.contains(coalesce(waste.homogeneityType,'')), or_(TechnologyDB.homogeneity == None, TechnologyDB.homogeneity_criteria != '1')),
                                        or_(TechnologyDB.moisture.contains(coalesce(waste.moistureType,'')), or_(TechnologyDB.moisture == None, TechnologyDB.moisture_criteria != '1')),
                                    )


    result = []
    index = 1
    for row in query:
        supplier=(User.query.filter_by(id=row.userId).first().username)
        result.append([index, row.description, supplier, row.id, row.userId, row.date[:10]])
        index +=1

    return result


###########################################       Matching Algorithm for Recycling Service Providers      ############################

def matching_algorithm_rsp(processwasteId):

    first_tech = TechnologyDB.query.filter_by(id=processwasteId).first()
    all_tech = TechnologyDB.query.filter_by(description = first_tech.description).all()
   
    result = []

    index = 1

    for tech in all_tech:

        tech_homogeneity = []
        tech_moisture = []
        tech_size = []

        if tech.homogeneity != None:
            tech_homogeneity = tech.homogeneity.split(',')
            
        if tech.moisture != None:
            tech_moisture = tech.moisture.split(',')

        if tech.size != None:
            tech_size = tech.size.split(',')

        query = WasteDB.query.filter(WasteDB.materialId == tech.materialId, WasteDB.userId != tech.userId,
                                        or_(and_(coalesce(tech.CN_min, 0) <= coalesce(WasteDB.CNratio, 0), coalesce(tech.CN_max, 999) >= coalesce(WasteDB.CNratio, 0)), tech.CN_criteria != '1'),
                                        or_(and_(coalesce(tech.pH_min, 0) <= WasteDB.pH, coalesce(tech.pH_max, 14) >= WasteDB.pH), tech.pH_criteria != '1'),
                                        or_(and_(coalesce(tech.cellulose_min, 0) <= coalesce(WasteDB.cellulosicValue,0), coalesce(tech.cellulose_max, 100) >= coalesce(WasteDB.cellulosicValue,0)), tech.cellulose_criteria != '1'),
                                        or_((coalesce(WasteDB.moistureType,'')).in_(tech_moisture), tech.moisture_criteria != '1'),
                                        or_((coalesce(WasteDB.homogeneityType,'')).in_(tech_homogeneity), tech.homogeneity_criteria != '1'),
                                        or_((coalesce(WasteDB.size,'')).in_(tech_size), tech.size_criteria != '1'),
                                    )

        for entry in query:

            supplier=(User.query.filter_by(id=entry.userId).first().username)
            date=str(entry.date)[:10]

            result.append([index, entry.description, supplier, entry.id, entry.userId, date])

            index += 1
    

    return result
