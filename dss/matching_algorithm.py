# Old version

from collections import defaultdict
from sqlalchemy.inspection import inspect
import pandas as pd
from dss.models import (User, Materials, Giveoutwaste,TechnologyDB)

def matching_algorithm(giveoutwasteId):

    wasteID = Giveoutwaste.query.filter_by(id=giveoutwasteId).first().questionCode
    wastematerialID = Giveoutwaste.query.filter_by(id=giveoutwasteId).first().materialId
    rset = TechnologyDB.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    df = pd.DataFrame(result)
    rset = Materials.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    materialsdf = pd.DataFrame(result)

    print('Technology_df')
    print(df)

    print('Material_df')
    print(materialsdf)

    counter=0
    result=[]
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

    for i in range(len(df)):
        techmaterialID=int(df.loc[i,'materialId'])      
        if wastematerialID==1 and techmaterialID==14:

            attrib=['materialId',
                    'CRatiomin',
                    'CRatiomax',
                    'NRatiomin',
                    'NRatiomax',
                    'Moisturemin',
                    'Moisturemax',
                    'pHmin',
                    'pHmax',
                    'cellulosicmin',
                    'cellulosicmax',
                    'particleSizemin',
                    'particleSizemax',
                    'unacceptableshells',
                    'unacceptableshells',
                    'unacceptableshellspercent',
                    'unacceptablebones',
                    'unacceptablebonespercent',
                    'unacceptablebamboo',
                    'unacceptablebamboopercent',
                    'unacceptablebanana',
                    'unacceptablebananapercent',
                    'unacceptableothers',
                    'unacceptableotherspercent',
                    'TechnologyName',
                    'byproductBiogas',
                    'byproductBiogasEfficiency',
                    'byproductBiogasCHFour',
                    'byproductBiogasCOTwo',
                    'ByproductChemical',
                    'ByproductChemicalEfficiency',
                    'ByproductMetal',
                    'ByproductMetalEfficiency',
                    'ByproductBiochar',
                    'ByproductBiocharEfficency',
                    'ByproductDigestate',
                    'ByproductDigestateEfficiency',
                    'ByproductOil',
                    'ByproductOilEfficiency',
                    'ByproductOthers',
                    'ByproductOthersEfficiency',
                    'TechnologyName',
                    'AdditionalInformation',
                    'url']
            techID = {}
            #print(df.loc[i,'description'])
            #print(techID)
            for at in attrib:
                techID[at]=df.loc[i,at]
            
            if (wCRatio=='__' or (int(wCRatio)>=int(techID['CRatiomin']) and int(wCRatio)<=int(techID['CRatiomax']))) and ((wNRatio)=='__' or (int(wNRatio)>=int(techID['NRatiomin']) and int(wNRatio)<=int(techID['NRatiomax']))) and ((wphValue)=='__' or (int(wphValue)>=int(techID['pHmin']) and int(wphValue)<=int(techID['pHmax']))):
                counter+=1
                index=(counter)
                desc=(df.loc[i,'description'])
                supplier=(User.query.filter_by(id=int(df.loc[i,'userId'])).first().username)
                #print(supplier)
                rawdate=str(df.loc[i,'date'])
                rawdate=rawdate[:10]
                url = df.loc[i,'url']
                result.append([index,desc,supplier,rawdate,url])
        else:
            counter=0
            print(techmaterialID)
            print(materialsdf.loc[wastematerialID-1,'material'])
            print(materialsdf.loc[int(techmaterialID)-1,'material'][0:len(materialsdf.loc[wastematerialID-1,'material'])])
            if materialsdf.loc[wastematerialID-1,'material'] == materialsdf.loc[int(techmaterialID)-1,'material'][0:len(materialsdf.loc[wastematerialID-1,'material'])]:
                counter+=1
                index=(counter)
                desc=(df.loc[i,'description'])
                supplier=(User.query.filter_by(id=int(df.loc[i,'userId'])).first().username)
                #print(supplier)
                rawdate=str(df.loc[i,'date'])
                rawdate=rawdate[:10]
                url = df.loc[i,'url']
                result.append([index,desc,supplier,rawdate,url])
    print(result)
    return result