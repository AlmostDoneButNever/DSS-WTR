import traceback
from collections import defaultdict
from sqlalchemy.inspection import inspect
import os
from datetime import datetime
import pandas as pd
from flask import render_template, url_for, flash, redirect, request,jsonify
from dss import app, db
from dss.forms import (MaterialsForm, maxRowsForm, BuyingForm,RSPForm) 
from dss.models import (User, RSP, Materials, Questions, Giveoutwaste, Processwaste, Technology, Takeinresource, Technologybreakdown, 
     Sample, TechnologyDB, MaterialsDB, ManureDB, Product, WasteDB)
from flask_login import current_user, login_required
from dss.AddEntryToDB import AddWasteToDB, AddTechToDB

from dss.wasteIdGenerator import getWasteId
from dss.matching_algorithm import matching_algorithm_seller, matching_algorithm_rsp

from dss.standards import FoodStandard, ManureStandard, WoodStandard
from dss.forms import dispatchMatchingForm

@app.route("/matching", methods=['GET', 'POST'])
@login_required
def matching():
    form = dispatchMatchingForm()

    prevWasteEntries = [(waste.id, waste.description + ' - ' + waste.date[:10]) for waste in WasteDB.query.filter_by(userId=int(current_user.id)).all()]
    prevWasteEntries.insert(0,(None,None))
    form.wasteSelect.choices = prevWasteEntries

    prevTechEntries = [(tech.id,  tech.description + ' - ' + tech.date[:10]) for tech in TechnologyDB.query.filter_by(userId=int(current_user.id)).group_by(TechnologyDB.description, TechnologyDB.date).all()]
    prevTechEntries.insert(0,(None,None))
    form.techSelect.choices = prevTechEntries

    if request.method == 'POST':

        if request.form['select_role'] == 'waste_seller':
            return redirect(url_for("matching_filter_waste", giveoutwasteId=form.wasteSelect.data))
        else:
            return redirect(url_for("matching_filter_recycling", processwasteId=form.techSelect.data))

    #return render_template('matching/matching.html')
    return render_template('matching/main.html', title="Matching", form = form)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ waste sellers ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

@app.route("/matching/sellingwaste", methods=['GET', 'POST'])
@login_required
def selling_waste():
    form = MaterialsForm()
    form.type.choices = [(material.type, material.type) for material in Materials.query.group_by(Materials.type)]
    #form.material.choices = [(material.id, material.material) for material in Materials.query.filter_by(type=Materials.query.first().type).all()]

    form.material.choices = [(material.id, material.material) for material in MaterialsDB.query.all()]
    #form.material.choices = ['Food Waste', 'Animal Manure', 'Wood Waste', 'E-waste', 'Plastic waste']
    #get past waste ID
    prevEntries = [(waste.id, waste.description + ' - ' + waste.date) for waste in WasteDB.query.filter_by(userId=int(current_user.id)).all()]
    prevEntries.insert(0,(None,None))
    form.wasteID.choices = prevEntries
    # flash(prevEntries, 'success')

    if request.method == 'POST':
        #user selects past Waste ID
        if form.wasteID.data != None:
            print(form.wasteID.data)
            return redirect(url_for("matching_filter_waste", giveoutwasteId=form.wasteID.data))
            
        #creates new Waste ID
        else:
            return redirect(url_for("matching_questions_sellers",materialId=form.material.data))
    return render_template('matching/sellingwaste.html', title="Matching", form=form)


@app.route("/matching/sellerquestions/<materialId>", methods=['GET', 'POST'])
@login_required
def matching_questions_sellers(materialId):
    form = []
    material = Materials.query.filter_by(id=materialId).first()
    samples = Sample.query.all()
    result = defaultdict(list)
    for obj in samples:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    df = pd.DataFrame(result)
    samplefood=df['FoodItem'].tolist()

    samples = ManureDB.query.all()
    result = defaultdict(list)
    for obj in samples:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    df = pd.DataFrame(result)
    samplemanure=df['ManureType'].tolist()

    foodref = FoodStandard()
    manureref = ManureStandard()
    woodref = WoodStandard()
   
    if request.method == 'POST':
        print(request.files)
        print(request.files.getlist('image'))
        
        filename = None
        #save file
        if request.files["file"]:
            file = request.files["file"] 
            filename = str(datetime.now()).replace(":","_") + "_" + file.filename
            file.save( os.path.join(app.config['LAB'], filename))


        image_files = request.files.getlist('image')
        image_name_list = ""

        if image_files:
            for image in image_files:
                image_name = str(datetime.now()).replace(":","_") + "_" + image.filename
                image.save(os.path.join(app.config['IMAGE'], image_name))   
                image_name_list += str(image_name) + ";;;" 
            
        #convert output to a code    
        try:
            output = AddWasteToDB(materialId, request, filename, image_name_list)
            #success message:
            #flash(f'ID: {questionCode}', 'success')
            flash('Your response has been recorded!','success')  
            
        except Exception:
            traceback.print_exc()
            flash(f'Please ensure that the form is filled in correctly first before submitting','danger')
            return redirect(request.referrer)
            #return redirect(url_for("matching_questions_sellers", materialId=materialId))

        return redirect(url_for("profile", user_id = current_user.id))
        #return redirect(url_for("selling_waste"))


    return render_template('matching/questions_template_seller.html', title="Matching Questions", form=form, samplefood=samplefood, samplemanure = samplemanure, materialId=materialId, foodref = foodref, manureref = manureref, woodref = woodref)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Treatment provider ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


@app.route("/matching/recycling_service_provider", methods=['GET', 'POST'])
@login_required
def recycling_service_provider():
    form = RSPForm()
    form.maincat.choices = [(rsp.maincat, rsp.maincat) for rsp in RSP.query.group_by(RSP.maincat)]
    form.subcat.choices = [(rsp.id, rsp.subcat) for rsp in RSP.query.filter_by(maincat=RSP.query.first().maincat).all()]

    wastematerial = [(material.id, material.material) for material in MaterialsDB.query.all()]

    #get past technology ID
    prevEntries = [(waste.id, waste.description + ': ' + waste.technology + ' - ' + waste.date) for waste in TechnologyDB.query.filter_by(userId=int(current_user.id)).group_by(TechnologyDB.description, TechnologyDB.date).all()]
    prevEntries.insert(0,(None,None))
    form.technologyID.choices = prevEntries
    # flash(prevEntries, 'success')

    if request.method == 'POST':
        #user selects past Tech ID
        if form.technologyID.data != None:
            print(form.technologyID.data)
            return redirect(url_for("matching_filter_recycling", processwasteId=form.technologyID.data))
        #creates new Tech ID
        else:
            materialId = []
            for key, value in request.form.items():
                if 'tech_waste_id' in key:
                    materialId.extend(value)

            return redirect(url_for("matching_questions_rsp",materialId=materialId))
    return render_template('matching/recycling_service_provider.html', title="Matching", form=form, wastematerial = wastematerial)    

@app.route("/matching/rspquestions/<materialId>", methods=['GET', 'POST'])
@login_required
def matching_questions_rsp(materialId):
    print(materialId)
    foodref = FoodStandard()
    manureref = ManureStandard()
    woodref = WoodStandard()

    sampleproduct = [(product.ProductName, product.unit) for product in Product.query.all()]
    
    if request.method == 'POST':
        
        print(request.data)
        print(request.form)

        try:
            output = AddTechToDB(materialId, request)
            print('output', output)
            flash('Your response has been recorded!','success')
            #return redirect(url_for("recycling_service_provider"))
            return redirect(url_for("profile", user_id = current_user.id))

       

        except Exception:
            traceback.print_exc()
            flash(f'Please ensure that the form is filled in correctly first before submitting','danger')
            return redirect(url_for("matching_questions_rsp", materialId=materialId))



    return render_template('matching/questions_template_rsp.html', title="Matching Questions",  materialId=materialId, sampleproduct = sampleproduct, foodref = foodref, manureref = manureref, woodref = woodref)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ resource buyers ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

@app.route("/matching/buying_resources", methods=['GET', 'POST'])
@login_required
def buying_resources_selection():
    return render_template('matching/buying_resource.html', title="Matching")  

@app.route("/matching/buying_resources/processed", methods=['GET', 'POST'])
@login_required
def buying_resources():
    form = BuyingForm()
    form.dropdown.choices = ['Biogas','Chemical','Metal','Biochar','Digestate','Oil','Others']
    

    if request.method == 'POST':
        if form.dropdown.data == None:
            return redirect(url_for("buying_resources"))
        else:
            return redirect(url_for("matching_filter_resource",byproduct=form.dropdown.data))
    return render_template('matching/buying_resources.html', title="Matching", form=form)

@app.route("/matching/filter_resource/waste", methods=['GET', 'POST'])
def buying_waste():

    rset = Giveoutwaste.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    df = pd.DataFrame(result)

    
    counter=0
    result=[]
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
                    'AdditionalInformation']

        
    #print(techmaterialID)
    for i in range(len(df)):
        wastematerialID=int(df.loc[i,'materialId'])
        #print(techmaterialID)
        print(wastematerialID)      
        
        wasteID = (df.loc[i,'questionCode'])
        print(wasteID)
        # homogeneity=wasteID[1]
        # wCHNType=wasteID[2]
        # wCRatio=wasteID[3:5]
        # wHRatio=wasteID[5:7]
        # wNRatio=wasteID[7:9]
        # wproteinType=wasteID[9]
        # wproteinRatio=wasteID[10:12]
        # wcellulosic=wasteID[12]
        # wshellAndBones=wasteID[13:15]
        # wmoistureType=wasteID[15]
        # wmoistureContent=wasteID[16:18]
        # wsaltType=wasteID[18]
        # wsaltContent=wasteID[19:21]
        # wpHType=wasteID[21]
        # wphValue=wasteID[22:24]
        # wparticleSize=wasteID[24]
        counter+=1
        index=(counter)
        desc=(df.loc[i,'description'])
        supplier=(User.query.filter_by(id=int(df.loc[i,'userId'])).first().username)
        #print(supplier)
        rawdate=str(df.loc[i,'date'])
        rawdate=rawdate[:10]
        result.append([index,desc,supplier,rawdate])
    return render_template('matching/matching_results_recycling.html', result=result )

   

@app.route("/materials/<Type>")
def materials(Type):
    materials = Materials.query.order_by(Materials.id.asc()).filter_by(type=Type).all()

    materialArray = []
    for material in materials:
        materialObj = {}
        materialObj['id'] = material.id
        materialObj['material'] = material.material
        materialArray.append(materialObj)
    return jsonify({'materials' : materialArray})

@app.route("/rsp/<maincat>")
def rsp(maincat):
    rsp = RSP.query.order_by(RSP.id.asc()).filter_by(maincat=maincat).all()

    subcatArray = []
    for subcat in rsp:
        subcatObj = {}
        subcatObj['id'] = subcat.id
        subcatObj['subcat'] = subcat.subcat
        subcatArray.append(subcatObj)
    return jsonify({'subcats' : subcatArray})


@app.route("/matching/filter_waste/<giveoutwasteId>", methods=['GET','POST'])
def matching_filter_waste(giveoutwasteId):
    
    result = matching_algorithm_seller(giveoutwasteId)

    return render_template('matching/matching_results_waste.html', result=result )

@app.route("/matching/filter_recycling/<processwasteId>", methods=['GET','POST'])
def matching_filter_recycling(processwasteId):
    result = matching_algorithm_rsp(processwasteId)
    return render_template('matching/matching_results_recycling.html', result=result )

@app.route("/matching/filter_resource/<byproduct>", methods=['GET','POST'])
def matching_filter_resource(byproduct):
    rset = Processwaste.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    df = pd.DataFrame(result)
    counter=0
    result=[]
    byproducts = ['Biogas','Chemical','Metal','Biochar','Digestate','Oil','Others']
    j=41
    for k in range(len(byproducts)):
        if byproducts[k]==byproduct:
            print(byproduct)
            for i in range(len(df)):
                techID=(df.loc[i,'questionCode'])      
                byproductID=techID[j+k]
                if byproductID=="1":
                    counter+=1
                    index=(counter)
                    desc=(df.loc[i,'description'])
                    supplier=(User.query.filter_by(id=int(df.loc[i,'userId'])).first().username)
                    #print(supplier)
                    rawdate=str(df.loc[i,'date'])
                    rawdate=rawdate[:10]
                    result.append([index,desc,supplier,rawdate])


    return render_template('matching/matching_results_buyer.html', result=result,byproduct=byproduct)

@app.route("/matching/results_resource/<takeinresourceId>/<byProduct>/<landSpace>/<cost>/<env>", methods=['GET','POST'])
def matching_results_resource(takeinresourceId,byProduct,landSpace,cost,env):
    form = maxRowsForm()
    page = request.args.get('page', 1, type=int)
    order = request.args.get('order','id',type=str)
    orderName = 'None' if order == 'id' else order

    #get material info
    materialId = Takeinresource.query.filter_by(id=takeinresourceId).first().materialId
    materialType = Materials.query.filter_by(id=materialId).first().material
        
    if byProduct == 'All':
        results = Technology.query.\
            filter(Technology.resourceId==materialId, Technology.landSpace<=landSpace, Technology.estimatedCost<=cost, Technology.environmentalImpact<=env)\
            .order_by( getattr(Technology,order) .asc()).paginate(page=page, per_page=5) 
    else:
        results = Technology.query.\
            filter(Technology.resourceId==materialId, Technology.byProduct==byProduct, Technology.landSpace<=landSpace, Technology.estimatedCost<=cost, Technology.environmentalImpact<=env)\
            .order_by( getattr(Technology,order) .asc()).paginate(page=page, per_page=5) 

    if request.method == 'POST':
        return redirect(url_for('matching_results_resource', takeinresourceId=takeinresourceId,byProduct=byProduct,landSpace=landSpace,cost=cost,env=env,page=page,order=form.order.data))
    return render_template('matching/matching_results_resource.html', title="Matching Results", results=results, materialType=materialType, form=form, order=order, orderName=orderName, takeinresourceId=takeinresourceId,byProduct=byProduct,landSpace=landSpace,cost=cost,env=env)


@app.route("/matching/technology/<technologyId>", methods=['GET','POST'])
def matching_technology(technologyId):
    technology = Technology.query.filter(Technology.id==technologyId).first()
    technologyBreakdown = Technologybreakdown.query.filter(Technologybreakdown.technologyId==int(technologyId)).first()

    #carousel pictures & HTML
    navHTML = []
    if technologyBreakdown and technologyBreakdown.carouselHTML:
        for i in range(len(technologyBreakdown.carouselHTML.split('<div class="carousel-item"'))):
            if technologyBreakdown.carouselHTML != None:
                navHTML.append(f'<li data-target="#technologyPictures" data-slide-to="{i}"></li>')


    return render_template('matching/matching_technology.html', title="Matching Technology", technology=technology, technologyBreakdown=technologyBreakdown, navHTML=navHTML)

