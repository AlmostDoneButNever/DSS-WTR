# New version (Angel edits)

from collections import defaultdict
from operator import contains, or_, and_
from sqlalchemy.inspection import inspect
import pandas as pd
from dss.models import (User, MaterialDB, Waste,Technology)
from dss.wasteIdGenerator import breakId
from sqlalchemy.sql.functions import coalesce


###########################################       Matching Algorithm for Waste Sellers      ############################


def matching_algorithm_seller(giveoutwasteId, techId = None):

    waste = Waste.query.filter_by(id=int(giveoutwasteId)).first()

    if techId:
        techId = int(techId)
  
    query = Technology.query.filter(  or_(Technology.id == techId, techId == None), 
                                        Technology.materialId == str(waste.materialId), Technology.userId != waste.userId,
                                        or_(and_(coalesce(Technology.CN_min, 0) <= coalesce(waste.CNratio, 0), coalesce(Technology.CN_max, 999) >= coalesce(waste.CNratio, 0)),Technology.CN_criteria != '1'),
                                        or_(and_(coalesce(Technology.pH_min, 0) <= coalesce(waste.pH, 0), coalesce(Technology.pH_max, 14) >= coalesce(waste.pH, 0)), Technology.pH_criteria != '1'),
                                        or_(and_(coalesce(Technology.cellulose_min, 0) <= coalesce(waste.cellulosicValue, 0), coalesce(Technology.cellulose_max, 100) >= coalesce(waste.cellulosicValue, 0)), Technology.cellulose_criteria != '1'),
                                        or_(Technology.size.contains(coalesce(waste.size,'')), or_(Technology.size == None, Technology.size_criteria != '1')),
                                        or_(Technology.homogeneity.contains(coalesce(waste.homogeneityType,'')), or_(Technology.homogeneity == None, Technology.homogeneity_criteria != '1')),
                                        or_(Technology.moisture.contains(coalesce(waste.moistureType,'')), or_(Technology.moisture == None, Technology.moisture_criteria != '1')),
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

    first_tech = Technology.query.filter_by(id=processwasteId).first()
    all_tech = Technology.query.filter_by(description = first_tech.description).all()
   
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

        query = Waste.query.filter(Waste.materialId == tech.materialId, Waste.userId != tech.userId,
                                        or_(and_(coalesce(tech.CN_min, 0) <= coalesce(Waste.CNratio, 0), coalesce(tech.CN_max, 999) >= coalesce(Waste.CNratio, 0)), tech.CN_criteria != '1'),
                                        or_(and_(coalesce(tech.pH_min, 0) <= Waste.pH, coalesce(tech.pH_max, 14) >= Waste.pH), tech.pH_criteria != '1'),
                                        or_(and_(coalesce(tech.cellulose_min, 0) <= coalesce(Waste.cellulosicValue,0), coalesce(tech.cellulose_max, 100) >= coalesce(Waste.cellulosicValue,0)), tech.cellulose_criteria != '1'),
                                        or_((coalesce(Waste.moistureType,'')).in_(tech_moisture), tech.moisture_criteria != '1'),
                                        or_((coalesce(Waste.homogeneityType,'')).in_(tech_homogeneity), tech.homogeneity_criteria != '1'),
                                        or_((coalesce(Waste.size,'')).in_(tech_size), tech.size_criteria != '1'),
                                    )

        for entry in query:

            supplier=(User.query.filter_by(id=entry.userId).first().username)
            date=str(entry.date)[:10]

            result.append([index, entry.description, supplier, entry.id, entry.userId, date])

            index += 1
    

    return result
