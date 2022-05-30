import math
from dss import db
from dss.models import WasteDB, Sample, ManureDB, TechnologyDB
from flask_login import current_user
from datetime import datetime

from dss.standards import FoodStandard, ManureStandard, WoodStandard



def AddWasteToDB(materialId, request):

    def classify(data, target):
        for key, (_, lb, ub) in data:
            if int(target) <= ub and int(target) > lb:
                result = key
                break
        return result

    if materialId == '1':
        description = request.form['description']
        lab = request.form['lab_analysis']
        size = request.form['approx_size']
        impurities = request.form['impurities']

        food_list_id = []
        food_list_wt = []

        for key, value in request.form.items():
            
            if 'food_content_id_' in key:
                food_list_id.append(value)

            if 'food_content_wt_' in key:
                food_list_wt.append(value)

        food_breakdown = dict(zip(food_list_id, food_list_wt))

        foodref = FoodStandard()

        homogeneityValue = max(food_list_wt)

        homogeneityType = classify(foodref.homogeneity.items(), homogeneityValue)
        
        # Lab

        if lab == '1':

            CHN = list(map(int,request.form['lab_chn'].split(':')))
            C_content = CHN[0]
            H_content = CHN[1]
            N_content = CHN[2]

            CN_ratio = round(C_content/N_content,2)

            moisture = request.form['lab_moisture']

            cellulose = request.form['lab_cellulose']

            pH = request.form['lab_pH']


            moistureType = classify(foodref.moisture.items(), moisture)

            # insert into database
            waste = WasteDB(materialID=int(materialId), wasteID = 'test', userId=int(current_user.id), description=request.form['description'], type = str(food_breakdown),
                            size = size, impurities = impurities, lab = lab, moistureType = 'dry', moistureValue = moisture, cellulosicValue = cellulose, homogeneityType = homogeneityType, homogeneityValue =homogeneityValue, pH = pH,  CNratio = CN_ratio, date=datetime.now())


        # Approximation

        elif lab == '0':
            record = Sample.query.filter(Sample.FoodItem.in_(food_list_id)).all()

            weights = 0
            C_product = 0
            N_product = 0
            cellulose_product = 0
            Hion_product = 0
            moisture_product = 0

            for row in record:

                weights += int(food_breakdown[row.FoodItem])
                C_product += row.C * int(food_breakdown[row.FoodItem])
                N_product += row.N * int(food_breakdown[row.FoodItem])
                cellulose_product += row.cellulose * int(food_breakdown[row.FoodItem])

                Hion = pow(10,-row.pH)
                Hion_product += Hion * int(food_breakdown[row.FoodItem])

                moisture_product += row.moisture * int(food_breakdown[row.FoodItem])

            C_approx = C_product/weights
            N_approx = N_product/weights

            CN_ratio = round(C_approx/N_approx,2)

            moistureType = request.form['approx_moisture']

            cellulose = round(cellulose_product/weights,2)

            pH = round(-math.log10(Hion_product/weights),2)

            moisture = moisture_product/weights
            
            # insert into database
            if moistureType == 'not sure':
                waste = WasteDB(materialID=int(materialId), wasteID = 'test', userId=int(current_user.id), description=description, type = str(food_breakdown),
                                size = size, impurities = impurities, lab = lab, moistureType = moistureType, moistureValue = moisture, cellulosicValue = cellulose, homogeneityType = homogeneityType, pH = pH, CNratio = CN_ratio, date=datetime.now())
            else:    
                waste = WasteDB(materialID=int(materialId), wasteID = 'test', userId=int(current_user.id), description=description, type = str(food_breakdown),
                                size = size, impurities = impurities, lab = lab, moistureType = moistureType, cellulosicValue = cellulose, homogeneityType = homogeneityType, pH = pH, CNratio = CN_ratio, date=datetime.now())
            
        db.session.add(waste)
        db.session.commit()



    elif materialId == '2':
        description = request.form['description']
        lab = request.form['lab_analysis']
        impurities = request.form['impurities']
        type =  request.form['type']
       
        # Approximation

        if lab == '1':

            CHN = list(map(int,request.form['lab_chn'].split(':')))
            C_content = CHN[0]
            H_content = CHN[1]
            N_content = CHN[2]

            CN_ratio = round(C_content/N_content,2)

            moisture = request.form['lab_moisture']

            cellulose = request.form['lab_cellulose']

            pH = request.form['lab_pH']

            homogeneityValue = request.form['lab_homogeneity']

            manureref = ManureStandard()

            homogeneityType = classify(manureref.homogeneity.items(), homogeneityValue)
            moistureType = classify(manureref.moisture.items(), moisture)


            # insert into database
            waste = WasteDB(materialID=int(materialId), wasteID = 'test', userId=int(current_user.id), description=request.form['description'], type = type,
                             impurities = impurities, lab = lab, moistureType = moistureType, moistureValue = moisture, cellulosicValue = cellulose, homogeneityType = homogeneityType, homogeneityValue =homogeneityValue, pH = pH,  CNratio = CN_ratio, date=datetime.now())


        # Approximation

        elif lab == '0':
            record = ManureDB.query.filter(ManureDB.ManureType == type).first()
            C_approx = record.C
            N_approx = record.N

            CN_ratio = round(C_approx/N_approx,2)

            moistureType = request.form['approx_moisture']
            moisture = record.moisture

            cellulose = record.cellulose

            pH = record.pH

            homogeneityType = request.form['approx_homogeneity']

            
            
            # insert into database
            if moistureType == 'not sure':
                waste = WasteDB(materialID=int(materialId), wasteID = 'test', userId=int(current_user.id), description=description, type = type,
                                impurities = impurities, lab = lab, moistureType = moistureType, moistureValue = moisture, cellulosicValue = cellulose, homogeneityType =homogeneityType,  pH = pH, CNratio = CN_ratio, date=datetime.now())
            else:    
                waste = WasteDB(materialID=int(materialId), wasteID = 'test', userId=int(current_user.id), description=description, type = type,
                                impurities = impurities, lab = lab, moistureType = moistureType,  cellulosicValue = cellulose, homogeneityType =homogeneityType, pH = pH, CNratio = CN_ratio, date=datetime.now())


        db.session.add(waste)
        db.session.commit()



    elif materialId == '3':
        description = request.form['description']
        lab = request.form['lab_analysis']
        impurities = request.form['impurities']
        size = request.form['approx_size']
        type =  request.form['type']
       
        # Approximation

        if lab == '1':

            CHN = list(map(int,request.form['lab_chn'].split(':')))
            C_content = CHN[0]
            H_content = CHN[1]
            N_content = CHN[2]

            CN_ratio = round(C_content/N_content,2)

            moisture = request.form['lab_moisture']

            cellulose = request.form['lab_cellulose']

            homogeneityValue = request.form['lab_homogeneity']

            woodref = WoodStandard()

            homogeneityType = classify(woodref.homogeneity.items(), homogeneityValue)
            moistureType = classify(woodref.moisture.items(), moisture)


            # insert into database
            waste = WasteDB(materialID=int(materialId), wasteID = 'test', userId=int(current_user.id), description=request.form['description'], type = type, size = size,
                             impurities = impurities, lab = lab, moistureType = moistureType, moistureValue = moisture, cellulosicValue = cellulose, homogeneityType =homogeneityType, homogeneityValue =homogeneityValue,  CNratio = CN_ratio, date=datetime.now())


        # Approximation

        elif lab == '0':
            
            moistureType = request.form['approx_moisture']
   
            homogeneityType = request.form['approx_homogeneity']

            
            
            # insert into database
            waste = WasteDB(materialID=int(materialId), wasteID = 'test', userId=int(current_user.id), description=description, type = type, size = size,
                                impurities = impurities, lab = lab, moistureType = moistureType, homogeneityType =homogeneityType, date=datetime.now())


        db.session.add(waste)
        db.session.commit()



def AddTechtoDB(materialId, request):

    description = request.form['description']
    technology = request.form['technology']

    product_list_name = []
    product_list_yield = []

    for key, value in request.form.items():
        
        if 'product_name_' in key:
            product_list_name.append(value)

        if 'product_yield_' in key:
            product_list_yield.append(value)

    product_list = dict(zip(product_list_name, product_list_yield))

    '''
    # Initialize

    CN_min = None
    CN_max  = None

    pH_min = None
    pH_max = None

    cellulose_min = None
    cellulose_max = None

    moisture = None
    homogeneity = None
    size = None
    '''

    if '1' in materialId:

        parameters = ['CN_yesno', 'CN_min', 'CN_max', 'pH_yesno', 'pH_min', 'pH_max', 'cellulose_yesno', 'cellulose_min', 'cellulose_max',
                'moisture_yesno', 'moisture', 'homogeneity_yesno', 'homogeneity', 'size_yesno', 'size']

        suffix = '_food'

        food = {}

        for par in parameters:
            food[par] = None

            try:
                value = request.form[par + suffix]

                if value:
                    food[par] = value

            except:
                pass


        tech = TechnologyDB(
                    materialId='1', userId=int(current_user.id), description=description, technology = technology, 
                    product_list = str(product_list), CN_min = food['CN_min'], CN_max = food['CN_max'], pH_min = food['pH_min'], pH_max = food['pH_max'], 
                    cellulose_min = food['cellulose_min'], cellulose_max = food['cellulose_max'], moisture = food['moisture'], 
                    homogeneity = food['homogeneity'], size = food['size'], date=datetime.now()
                    )

        '''
        CN_yesno = request.form['CN_yesno_food']
        CN_min = request.form['CN_min_food']
        CN_max = request.form['CN_max_food']

        pH_yesno = request.form['pH_yesno_food']
        pH_min = request.form['pH_min_food']
        pH_max = request.form['pH_max_food']

        cellulose_yesno = request.form['cellulose_yesno_food']
        cellulose_min = request.form['cellulose_min_food']
        cellulose_max = request.form['cellulose_max_food']
        
        moisture_yesno = request.form['moisture_yesno_food']
        moisture = request.form['moisture_food']

        homogeneity_yesno = request.form['homogeneity_yesno_food']
        homogeneity = request.form['homogeneity_food']

        size_yesno = request.form['size_yesno_food']
        size = request.form['size_food']

        tech = TechnologyDB(
                            materialID=int(materialId), userId=int(current_user.id), description=description, technology = technology, 
                            product_list = product_list, CN_min = CN_min, CN_max = CN_max, pH_min = pH_min, pH_max = pH_max, 
                            cellulose_min = cellulose_min, cellulose_max = cellulose_max, moisture = moisture, 
                            homogeneity = homogeneity, size = size, date=datetime.now()
                            )
        '''
        db.session.add(tech)
        db.session.commit()

    return tech
    