import math
from dss import db
from dss.models import WasteDB, Sample, ManureDB, TechnologyDB
from flask_login import current_user
from datetime import datetime

from dss.standards import FoodStandard, ManureStandard, WoodStandard



def AddWasteToDB(materialId, request, filepath):

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
            waste = WasteDB(materialId=int(materialId), wasteId = 'test', userId=int(current_user.id), description=request.form['description'], type = str(food_breakdown),
                            size = size, impurities = impurities, lab = lab, moistureType = 'dry', moistureValue = moisture, cellulosicValue = cellulose, 
                            homogeneityType = homogeneityType, homogeneityValue =homogeneityValue, pH = pH,  CNratio = CN_ratio, date=str(datetime.now())[0:19], lab_report_path = filepath)


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
                waste = WasteDB(materialId=int(materialId), wasteId = 'test', userId=int(current_user.id), description=description, type = str(food_breakdown),
                                size = size, impurities = impurities, lab = lab, moistureType = moistureType, moistureValue = moisture, cellulosicValue = cellulose, 
                                homogeneityType = homogeneityType, pH = pH, CNratio = CN_ratio, date=str(datetime.now())[0:19], lab_report_path = filepath)
            else:    
                waste = WasteDB(materialId=int(materialId), wasteId = 'test', userId=int(current_user.id), description=description, type = str(food_breakdown),
                                size = size, impurities = impurities, lab = lab, moistureType = moistureType, cellulosicValue = cellulose, 
                                homogeneityType = homogeneityType, pH = pH, CNratio = CN_ratio, date=str(datetime.now())[0:19], lab_report_path = filepath)
            
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
            waste = WasteDB(materialId=int(materialId), wasteId = 'test', userId=int(current_user.id), description=request.form['description'], type = type,
                             impurities = impurities, lab = lab, moistureType = moistureType, moistureValue = moisture, cellulosicValue = cellulose, 
                             homogeneityType = homogeneityType, homogeneityValue =homogeneityValue, pH = pH,  CNratio = CN_ratio, date=str(datetime.now())[0:19], lab_report_path = filepath)


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
                waste = WasteDB(materialId=int(materialId), wasteId = 'test', userId=int(current_user.id), description=description, type = type,
                                impurities = impurities, lab = lab, moistureType = moistureType, moistureValue = moisture, cellulosicValue = cellulose, 
                                homogeneityType =homogeneityType,  pH = pH, CNratio = CN_ratio, date=str(datetime.now())[0:19], lab_report_path = filepath)
            else:    
                waste = WasteDB(materialId=int(materialId), wasteId = 'test', userId=int(current_user.id), description=description, type = type,
                                impurities = impurities, lab = lab, moistureType = moistureType,  cellulosicValue = cellulose, 
                                homogeneityType =homogeneityType, pH = pH, CNratio = CN_ratio, date=str(datetime.now())[0:19], lab_report_path = filepath)


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
            waste = WasteDB(materialId=int(materialId), wasteId = 'test', userId=int(current_user.id), description=request.form['description'], type = type, size = size,
                             impurities = impurities, lab = lab, moistureType = moistureType, moistureValue = moisture, cellulosicValue = cellulose, 
                             homogeneityType =homogeneityType, homogeneityValue =homogeneityValue,  CNratio = CN_ratio, date=str(datetime.now())[0:19], lab_report_path = filepath)


        # Approximation

        elif lab == '0':
            
            moistureType = request.form['approx_moisture']
   
            homogeneityType = request.form['approx_homogeneity']

            
            
            # insert into database
            waste = WasteDB(materialId=int(materialId), wasteId = 'test', userId=int(current_user.id), description=description, type = type, size = size,
                                impurities = impurities, lab = lab, moistureType = moistureType, homogeneityType =homogeneityType, date=str(datetime.now())[0:19], lab_report_path = filepath)


        db.session.add(waste)
        db.session.commit()

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
                                'cellulose_max', 'moisture_yesno',  'homogeneity_yesno', 'size_yesno', 'impurities_yesno', 'impurities']

        for par in list_parameters:

            data[par] = None

            try:

                value = request.form.getlist(par + suffix)

                if value:
                    string = '' 

                    for item in value:
                        string +=  item + ',' 

                    data[par] = string[0:len(string) - 1]
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
                    homogeneity = data['homogeneity_level'], size = data['size_level'], impurities = data['impurities'],
                    CN_criteria = data['CN_yesno'], pH_criteria = data['pH_yesno'], cellulose_criteria = data['cellulose_yesno'], 
                    moisture_criteria = data['moisture_yesno'], homogeneity_criteria = data['homogeneity_yesno'], 
                    size_criteria = data['size_yesno'], impurities_criteria = data['impurities_yesno'], date=str(datetime.now())[0:19]
                    )

        db.session.add(tech)
        db.session.commit()

    if '2' in materialId:

        suffix = '_manure'

        data = {}

        list_parameters = ['moisture_level', 'homogeneity_level', 'size_level' ]

        scalar_parameters = ['CN_yesno', 'CN_min', 'CN_max', 'pH_yesno', 'pH_min', 'pH_max', 'cellulose_yesno', 'cellulose_min', 
                                'cellulose_max', 'moisture_yesno',  'homogeneity_yesno', 'size_yesno', 'impurities_yesno', 'impurities']

        for par in list_parameters:

            data[par] = None

            try:

                value = request.form.getlist(par + suffix)

                if value:
                    string = '' 

                    for item in value:
                        string +=  item + ',' 

                    data[par] = string[0:len(string) - 1]

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
                    materialId='2', userId=int(current_user.id), description=description, technology = technology, 
                    product_list = str(product_list), CN_min = data['CN_min'], CN_max = data['CN_max'], pH_min = data['pH_min'], pH_max = data['pH_max'], 
                    cellulose_min = data['cellulose_min'], cellulose_max = data['cellulose_max'], moisture = data['moisture_level'], 
                    homogeneity = data['homogeneity_level'], size = data['size_level'], impurities = data['impurities'],
                    CN_criteria = data['CN_yesno'], pH_criteria = data['pH_yesno'], cellulose_criteria = data['cellulose_yesno'], 
                    moisture_criteria = data['moisture_yesno'], homogeneity_criteria = data['homogeneity_yesno'], 
                    size_criteria = data['size_yesno'], impurities_criteria = data['impurities_yesno'], date=str(datetime.now())[0:19]
                    )

        db.session.add(tech)
        db.session.commit()

    if '3' in materialId:

        suffix = '_wood'

        data = {}

        list_parameters = ['moisture_level', 'homogeneity_level', 'size_level' ]

        scalar_parameters = ['CN_yesno', 'CN_min', 'CN_max', 'pH_yesno', 'pH_min', 'pH_max', 'cellulose_yesno', 'cellulose_min', 
                                'cellulose_max', 'moisture_yesno',  'homogeneity_yesno', 'size_yesno', 'impurities_yesno', 'impurities']

        for par in list_parameters:

            data[par] = None

            try:

                value = request.form.getlist(par + suffix)

                if value:
                    string = '' 

                    for item in value:
                        string +=  item + ',' 

                    data[par] = string[0:len(string) - 1]
                    
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
                    materialId='3', userId=int(current_user.id), description=description, technology = technology, 
                    product_list = str(product_list), CN_min = data['CN_min'], CN_max = data['CN_max'], pH_min = data['pH_min'], pH_max = data['pH_max'], 
                    cellulose_min = data['cellulose_min'], cellulose_max = data['cellulose_max'], moisture = data['moisture_level'], 
                    homogeneity = data['homogeneity_level'], size = data['size_level'], impurities = data['impurities'],
                    CN_criteria = data['CN_yesno'], pH_criteria = data['pH_yesno'], cellulose_criteria = data['cellulose_yesno'], 
                    moisture_criteria = data['moisture_yesno'], homogeneity_criteria = data['homogeneity_yesno'], 
                    size_criteria = data['size_yesno'], impurities_criteria = data['impurities_yesno'], date=str(datetime.now())[0:19]
                    )

        db.session.add(tech)
        db.session.commit()



   

    return materialId
    