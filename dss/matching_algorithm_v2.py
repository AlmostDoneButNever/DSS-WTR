# New version (Angel edits)

from collections import defaultdict
from sqlalchemy.inspection import inspect
import pandas as pd
from dss.models import (User, Materials, Giveoutwaste,TechnologyDB)
from dss.wasteIdGenerator import breakId


def matching_algorithm(giveoutwasteId):

    wasteID = Giveoutwaste.query.filter_by(id=giveoutwasteId).first().questionCode
    wastematerialID = Giveoutwaste.query.filter_by(id=giveoutwasteId).first().materialId

    if wastematerialID ==1:
 
        waste = breakId(wastematerialID, wasteID)

        query = TechnologyDB.query.filter(TechnologyDB.CRatiomin <= waste.wCRatio, TechnologyDB.CRatiomax >= waste.wCRatio, 
                                            TechnologyDB.NRatiomin <= waste.wNRatio, TechnologyDB.NRatiomax >= waste.wNRatio, 
                                            TechnologyDB.pHmin <= waste.wphValue, TechnologyDB.pHmax >= waste.wphValue)


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

    return result