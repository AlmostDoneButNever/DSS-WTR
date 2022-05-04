# New version (Angel edits)

from collections import defaultdict
from sqlalchemy.inspection import inspect
import pandas as pd
from dss.models import (User, Materials, Giveoutwaste,TechnologyDB)

def matching_algorithm(giveoutwasteId):

    wasteID = Giveoutwaste.query.filter_by(id=giveoutwasteId).first().questionCode
    wastematerialID = Giveoutwaste.query.filter_by(id=giveoutwasteId).first().materialId

    if wastematerialID ==1:

        homogeneity=wasteID[1]
        wCHNType=wasteID[2]
        wCRatio=wasteID[3:5]
        wHRatio=wasteID[5:7]
        wNRatio=wasteID[7:9]
        wproteinType=wasteID[9]
        wproteinRatio=wasteID[10:12]
        wcellulosic=wasteID[12]
        wshellAndBones=wasteID[13:15]
        wmoistureType=wasteID[15]
        wmoistureContent=wasteID[16:18]
        wsaltType=wasteID[18]
        wsaltContent=wasteID[19:21]
        wpHType=wasteID[21]
        wphValue=wasteID[22:24]
        wparticleSize=wasteID[24]

        query = TechnologyDB.query.filter(TechnologyDB.CRatiomin <= wCRatio, TechnologyDB.CRatiomax >= wCRatio, TechnologyDB.NRatiomin <= wNRatio, TechnologyDB.NRatiomax >= wNRatio, TechnologyDB.pHmin <= wphValue, TechnologyDB.pHmax >= wphValue)

        result = []
        index = 1
        for row in query:
            supplier=(User.query.filter_by(id=row.userId).first().username)
            result.append([index, row.description, supplier, row.date[:10], row.url])
            index +=1

    else:

        waste_tech_dict = {'1':[14], '2':[20,21,22,23,24,25,26], '3':27}

        tech_materialid = waste_tech_dict[str(wastematerialID)]

        query = TechnologyDB.query.filter(TechnologyDB.materialId == tech_materialid)

        result = []
        index = 1
        for row in query:
            supplier=(User.query.filter_by(id=row.userId).first().username)
            result.append([index, row.description, supplier, row.date[:10], row.url])
            index +=1

        print("matching results")

    print(result)
    return result