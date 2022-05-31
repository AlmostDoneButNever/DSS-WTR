import math
from dss import db
from dss.models import WasteDB, Sample, ManureDB, TechnologyDB
from flask_login import current_user
from datetime import datetime

from dss.standards import FoodStandard, ManureStandard, WoodStandard

def AddTechToDB(materialId, request):

    description = request.form['description']
    technology = request.form['technology']

    product_list_name = request.form.getlist("product_name")
    product_list_yield = request.form.getlist("product_yield")
    product_list = dict(zip(product_list_name, product_list_yield))


    if '1' in materialId:

        suffix = '_food'

        data = {}

        list_parameters = ['moisture_level', 'homogeneity_level', 'size_level' ]

        scalar_parameters = ['CN_yesno', 'CN_min', 'CN_max', 'pH_yesno', 'pH_min', 'pH_max', 'cellulose_yesno', 'cellulose_min', 
                                'cellulose_max', 'moisture_yesno',  'homogeneity_yesno', 'size_yesno']

        for par in list_parameters:

            data[par] = None

            try:

                value = request.form.getlist(par + suffix)

                if value:
                    data[par] = str(value)
            except:
                pass
               
        for par in scalar_parameters:
            data[par] = None

            try:
                value = request.form[par + suffix]
                
                if value:
                    data[par] = value

            except:
                pass


        tech = TechnologyDB(
                    materialId='1', userId=int(current_user.id), description=description, technology = technology, 
                    product_list = str(product_list), CN_min = data['CN_min'], CN_max = data['CN_max'], pH_min = data['pH_min'], pH_max = data['pH_max'], 
                    cellulose_min = data['cellulose_min'], cellulose_max = data['cellulose_max'], moisture = data['moisture_level'], 
                    homogeneity = data['homogeneity_level'], size = data['size_level'], date=str(datetime.now())[0:19]
                    )

        db.session.add(tech)
        db.session.commit()

    if '2' in materialId:

        suffix = '_manure'

        data = {}

        list_parameters = ['moisture_level', 'homogeneity_level', 'size_level' ]

        scalar_parameters = ['CN_yesno', 'CN_min', 'CN_max', 'pH_yesno', 'pH_min', 'pH_max', 'cellulose_yesno', 'cellulose_min', 
                                'cellulose_max', 'moisture_yesno',  'homogeneity_yesno', 'size_yesno']

        for par in list_parameters:

            data[par] = None

            try:

                value = request.form.getlist(par + suffix)

                if value:
                    data[par] = str(value)
            except:
                pass
               
        for par in scalar_parameters:
            data[par] = None

            try:
                value = request.form[par + suffix]
                
                if value:
                    data[par] = value

            except:
                pass


        tech2 = TechnologyDB(
                    materialId='2', userId=int(current_user.id), description=description, technology = technology, 
                    product_list = str(product_list), CN_min = data['CN_min'], CN_max = data['CN_max'], pH_min = data['pH_min'], pH_max = data['pH_max'], 
                    cellulose_min = data['cellulose_min'], cellulose_max = data['cellulose_max'], moisture = data['moisture_level'], 
                    homogeneity = data['homogeneity_level'], size = data['size_level'], date=str(datetime.now())[0:19]
                    )

        db.session.add(tech2)
        db.session.commit()

    if '3' in materialId:

        suffix = '_wood'

        data = {}

        list_parameters = ['moisture_level', 'homogeneity_level', 'size_level' ]

        scalar_parameters = ['CN_yesno', 'CN_min', 'CN_max', 'pH_yesno', 'pH_min', 'pH_max', 'cellulose_yesno', 'cellulose_min', 
                                'cellulose_max', 'moisture_yesno',  'homogeneity_yesno', 'size_yesno']

        for par in list_parameters:

            data[par] = None

            try:

                value = request.form.getlist(par + suffix)

                if value:
                    data[par] = str(value)
            except:
                pass
                
        for par in scalar_parameters:
            data[par] = None

            try:
                value = request.form[par + suffix]
                
                if value:
                    data[par] = value

            except:
                pass


        tech3 = TechnologyDB(
                    materialId='3', userId=int(current_user.id), description=description, technology = technology, 
                    product_list = str(product_list), CN_min = data['CN_min'], CN_max = data['CN_max'], pH_min = data['pH_min'], pH_max = data['pH_max'], 
                    cellulose_min = data['cellulose_min'], cellulose_max = data['cellulose_max'], moisture = data['moisture_level'], 
                    homogeneity = data['homogeneity_level'], size = data['size_level'], date=str(datetime.now())[0:19]
                    )

        db.session.add(tech3)
        db.session.commit()



   

    return materialId
    