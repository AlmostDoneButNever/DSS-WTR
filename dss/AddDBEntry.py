import math
from dss import db
from dss.models import WasteDB, Sample
from flask_login import current_user
from datetime import datetime



def AddWasteToDB(materialId, request):
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

        # insert into database
        waste = WasteDB(materialID=int(materialId), wasteID = 'test', userId=int(current_user.id), description=request.form['description'], 
                           size = size, impurities = impurities, lab = lab, moistureType = 'dry', moistureValue = moisture, cellulosicValue = 20.5, pH = pH,  CNratio = CN_ratio, date=datetime.now())


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
            waste = WasteDB(materialID=int(materialId), wasteID = 'test', userId=int(current_user.id), description=request.form['description'], 
                            size = size, impurities = impurities, lab = lab, moistureType = moistureType, cellulosicValue = cellulose, pH = pH, CNratio = CN_ratio, date=datetime.now())
        else:    
            waste = WasteDB(materialID=int(materialId), wasteID = 'test', userId=int(current_user.id), description=request.form['description'], 
                            size = size, impurities = impurities, lab = lab, moistureType = moistureType, moistureValue = moisture, cellulosicValue = cellulose, pH = pH, CNratio = CN_ratio, date=datetime.now())
          
        
    db.session.add(waste)
    db.session.commit()










