import traceback
from collections import defaultdict
from sqlalchemy.inspection import inspect
import os
from datetime import datetime
import pandas as pd
from flask import render_template
from flask import url_for 
from flask import flash 
from flask import redirect
from flask import request
from flask import jsonify
from dss import app, db
from dss.forms import (MaterialsForm, maxRowsForm, BuyingForm,RSPForm) 
from dss.models import (User, RSP, Materials, Questions, Giveoutwaste, Processwaste, Technology, Takeinresource, Technologybreakdown, 
     Sample, TechnologyDB)
from flask_login import current_user, login_required


from dss.wasteIdGenerator import Waste


@app.route("/matching", methods=['GET', 'POST'])
@login_required
def matching():
    return render_template('matching.html')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ waste sellers ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

@app.route("/matching/sellingwaste", methods=['GET', 'POST'])
@login_required
def selling_waste():
    form = MaterialsForm()
    form.type.choices = [(material.type, material.type) for material in Materials.query.group_by(Materials.type)]
    form.material.choices = [(material.id, material.material) for material in Materials.query.filter_by(type=Materials.query.first().type).all()]
    #get past waste ID
    prevEntries = [(waste.id, waste.questionCode + ': ' + waste.description + ' - ' + waste.date.strftime("%d/%m/%Y")) for waste in Giveoutwaste.query.filter_by(userId=int(current_user.id)).all()]
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
    return render_template('sellingwaste.html', title="Matching", form=form)


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

    #get questions
    questionId = material.questionId.split(',')
    questions = []
    for id in questionId:
        questions.append(Questions.query.filter_by(id=id).first())
    
    if request.method == 'POST':
        
        print(request.data)
        print(request.form)
        #print(request.form.getlist('Q51_Chemical'))

        #save file
        if request.files["file"]:
            file = request.files["file"] 
            file.save(os.path.join(app.config['UPLOAD'],file.filename))
           
            #process file
            reportCode = 1
        else: 
            reportCode = 0
        
        #convert output to a code    
        try:
            wasteObj = Waste(materialId, request)
            questionCode = wasteObj.getId()
            if questionCode[0:5] == "Error":
                flash(questionCode,'danger')
                return redirect(url_for("matching_questions", materialId=materialId))       

            # insert into database
            waste = Giveoutwaste(materialId=int(materialId), questionCode=questionCode, reportCode=str(reportCode), userId=int(current_user.id), description=request.form['description'] or None, date=datetime.now())
            db.session.add(waste)
            db.session.commit()
            
            #success message:
            flash(f'ID: {questionCode}', 'success')
            flash('Your response has been recorded!','success')  
            
        except Exception:
            traceback.print_exc()
            flash(f'Please ensure that the form is filled in correctly first before submitting','danger')
            return redirect(request.referrer)
            #return redirect(url_for("matching_questions_sellers", materialId=materialId))

        
        return redirect(url_for("selling_waste"))


    return render_template('/matching/matching_questions_seller.html', title="Matching Questions", form=form, questions=questions, material=material, samplefood=samplefood, samplefoodlen=len(samplefood), materialId=materialId)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Treatment provider ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


@app.route("/matching/recycling_service_provider", methods=['GET', 'POST'])
@login_required
def recycling_service_provider():
    form = RSPForm()
    form.maincat.choices = [(rsp.maincat, rsp.maincat) for rsp in RSP.query.group_by(RSP.maincat)]
    form.subcat.choices = [(rsp.id, rsp.subcat) for rsp in RSP.query.filter_by(maincat=RSP.query.first().maincat).all()]
    #get past technology ID
    prevEntries = [(waste.id, waste.description + ': ' + waste.TechnologyName + ' - ' + waste.date) for waste in TechnologyDB.query.filter_by(userId=int(current_user.id)).all()]
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
            return redirect(url_for("matching_questions_rsp",materialId=form.subcat.data))
    return render_template('recycling_service_provider.html', title="Matching", form=form)    

@app.route("/matching/rspquestions/<materialId>", methods=['GET', 'POST'])
@login_required
def matching_questions_rsp(materialId):
    form = []
    material = Materials.query.filter_by(id=materialId).first()

    #get questions
    questionId = material.questionId.split(',')
    questions = []
    for id in questionId:
        questions.append(Questions.query.filter_by(id=id).first())
    
    if request.method == 'POST':
        
        print(request.data)
        print(request.form)
        
        #convert output to a code    
        try:
            materialId = int(materialId)
            if materialId==14:
                description = str(request.form['description'])
                userId = int(current_user.id)
                materialId = int(materialId)
                CRatiomin = int(request.form['Q45_min_C'])
                CRatiomax = int(request.form['Q45_max_C'])
                NRatiomin = int(request.form['Q45_min_N'])
                NRatiomax = int(request.form['Q45_max_N'])
                if len(request.form.getlist('Q46_moisture'))==2:
                    Moisturemin = int(request.form['Q46_min_moisture'])
                    Moisturemax = int(request.form['Q46_max_moisture'])
                else:
                    Moisturemin = 0
                    Moisturemax = 100
                if len(request.form.getlist('Q46_pH'))==2:
                    pHmin = int(request.form['Q46_min_ph'])
                    pHmax = int(request.form['Q46_max_ph'])
                else:
                    pHmin = 1
                    pHmax = 14
                if len(request.form.getlist('Q46_cellulosic'))==2:
                    cellulosicmin = int(request.form['Q46_min_Cellulosic'])
                    cellulosicmax = int(request.form['Q46_max_Cellulosic'])
                else:
                    cellulosicmin = 0
                    cellulosicmax = 100
                if len(request.form.getlist('Q46_size'))==2:
                    particleSizemin = int(request.form['Q46_min_Size'])
                    particleSizemax = int(request.form['Q46_max_Size'])
                else:
                    particleSizemin = 0
                    particleSizemax = 100
                
                
                if len(request.form.getlist('Q47_1'))==2:
                    unacceptableshells = 1
                    unacceptableshellspercent = int(request.form['Q47_1_value'])
                else:
                    unacceptableshells = 0
                    unacceptableshellspercent = 0
                if len(request.form.getlist('Q47_2'))==2:
                    unacceptablebones = 1
                    unacceptablebonespercent = int(request.form['Q47_2_value'])
                else:
                    unacceptablebones = 0
                    unacceptablebonespercent = 0
                if len(request.form.getlist('Q47_3'))==2:
                    unacceptablebamboo = 1
                    unacceptablebamboopercent = int(request.form['Q47_3_value'])
                else:
                    unacceptablebamboo = 0
                    unacceptablebamboopercent = 0
                if len(request.form.getlist('Q47_4'))==2:
                    unacceptablebanana = 1
                    unacceptablebananapercent = int(request.form['Q47_4_value'])
                else:
                    unacceptablebanana = 0
                    unacceptablebananapercent = 0
                        
                if len(request.form.getlist('Q47_5'))==2:
                    unacceptableothers = 1
                    unacceptableotherspercent = int(request.form['Q47_5_value'])
                else:
                    unacceptableothers = 0
                    unacceptableotherspercent = 0
                
                if len(request.form.getlist('Q51_Biogas'))==2:
                    byproductBiogas = 1
                    byproductBiogasEfficiency = int(request.form['Q51_Biogas_efficiency'])
                    byproductBiogasCHFour = 0
                    byproductBiogasCOTwo = 0
                    

                else:
                    byproductBiogas = 0
                    byproductBiogasEfficiency = 0
                    byproductBiogasCHFour = 0
                    byproductBiogasCOTwo = 0

                if len(request.form.getlist('Q51_Chemical'))==2:
                    ByproductChemical = 1
                    ByproductChemicalEfficiency = int(request.form['Q51_Chemical_efficiency'])
                else:
                    ByproductChemical = 0
                    ByproductChemicalEfficiency = 0

                if len(request.form.getlist('Q51_Metal'))==2:
                    ByproductMetal = 1
                    ByproductMetalEfficiency = int(request.form['Q51_Metal_efficiency'])
                else:
                    ByproductMetal = 0
                    ByproductMetalEfficiency = 0

                if len(request.form.getlist('Q51_Biochar'))==2:
                    ByproductBiochar = 1
                    ByproductBiocharEfficency = int(request.form['Q51_Biochar_efficiency'])
                else:
                    ByproductBiochar = 0
                    ByproductBiocharEfficency = 0

                if len(request.form.getlist('Q51_Digestate'))==2:
                    ByproductDigestate = 1
                    ByproductDigestateEfficiency = int(request.form['Q51_Digestate_efficiency'])
                else:
                    ByproductDigestate = 0
                    ByproductDigestateEfficiency = 0

                if len(request.form.getlist('Q51_Oil'))==2:
                    ByproductOil = 1
                    ByproductOilEfficiency = int(request.form['Q51_Oil_efficiency'])
                else:
                    ByproductOil = 0
                    ByproductOilEfficiency = 0

                if len(request.form.getlist('Q51_Others'))==2:
                    ByproductOthers = 1
                    ByproductOthersEfficiency = int(request.form['Q51_Others_efficiency'])
                else:
                    ByproductOthers = 0
                    ByproductOthersEfficiency = 0

            description = str(request.form['description'])
            userId = int(current_user.id)
            materialId = int(materialId)
            TechnologyName = str(request.form['Q50_tech'])
            AdditionalInformation = str(request.form['Q53'])
            cost = int(request.form['cost'])
            capacity = int(request.form['capacity'])
            url = str(request.form['URL'])
            forsale=int(request.form['Q_tech'])
            if forsale == 1:
                scaling=int(request.form['Q_scale'])
            else:
                scaling = 0
            questionCode = "Submitted!"
            
            
        except Exception:
            traceback.print_exc()
            flash(f'Please ensure that the form is filled in correctly first before submitting','danger')
            return redirect(url_for("matching_questions_rsp", materialId=materialId))

        flash(f'ID: {questionCode}', 'success')

        # insert into database
        if materialId==14:
            techID = TechnologyDB(userId=userId,
            materialId=materialId,
            CRatiomin=CRatiomin,
            CRatiomax=CRatiomax,
            NRatiomin=NRatiomin,
            NRatiomax=NRatiomax,
            Moisturemin=Moisturemin,
            Moisturemax=Moisturemax,
            pHmin=pHmin,
            pHmax=pHmax,
            cellulosicmin=cellulosicmin,
            cellulosicmax=cellulosicmax,
            particleSizemin=particleSizemin,
            particleSizemax=particleSizemax,
            unacceptableshells=unacceptableshells,
            unacceptableshellspercent=unacceptableshellspercent,
            unacceptablebones=unacceptablebones,
            unacceptablebonespercent=unacceptablebonespercent,
            unacceptablebamboo=unacceptablebamboo,
            unacceptablebamboopercent=unacceptablebamboopercent,
            unacceptablebanana=unacceptablebanana,
            unacceptablebananapercent=unacceptablebananapercent,
            unacceptableothers=unacceptableothers,
            unacceptableotherspercent=unacceptableotherspercent,
            TechnologyName=TechnologyName,
            byproductBiogas=byproductBiogas,
            byproductBiogasEfficiency=byproductBiogasEfficiency,
            ByproductChemical=ByproductChemical,
            ByproductChemicalEfficiency=ByproductChemicalEfficiency,
            ByproductMetal=ByproductMetal,
            ByproductMetalEfficiency=ByproductMetalEfficiency,
            ByproductBiochar=ByproductBiochar,
            ByproductBiocharEfficency=ByproductBiocharEfficency,
            ByproductDigestate=ByproductDigestate,
            ByproductDigestateEfficiency=ByproductDigestateEfficiency,
            ByproductOil=ByproductOil,
            ByproductOilEfficiency=ByproductOilEfficiency,
            ByproductOthers=ByproductOthers,
            ByproductOthersEfficiency=ByproductOthersEfficiency,
            AdditionalInformation=AdditionalInformation,
            date=str(datetime.now())[0:19],
            description=description,
            cost=cost,
            capacity=capacity,
            url=url,
            forsale=forsale,
            scaling=scaling)
        else:
            techID=TechnologyDB(userId=userId,
            materialId=materialId,
            AdditionalInformation=AdditionalInformation,
            TechnologyName=TechnologyName,
            date=str(datetime.now())[0:19],
            description=description,
            cost=cost)
        db.session.add(techID)
        db.session.commit()
        flash('Your response has been recorded!','success')
        return redirect(url_for("recycling_service_provider"))

    return render_template('/matching/matching_questions_rsp.html', title="Matching Questions", form=form, questions=questions, material=material, materialId=materialId)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ resource buyers ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

@app.route("/matching/buying_resources", methods=['GET', 'POST'])
@login_required
def buying_resources_selection():
    return render_template('buying_resource.html', title="Matching")  

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
    return render_template('buying_resources.html', title="Matching", form=form)

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
    return render_template('matching_results_recycling.html', result=result )

   

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
    # form = FilterForm()
    # materialId = Giveoutwaste.query.filter_by(id=giveoutwasteId).first().materialId

    # #get possible by-products
    # form.byproductType.choices = [(technology.byProduct, technology.byProduct) for technology in Technology.query.filter_by(materialId=materialId).group_by(Technology.byProduct)]
    # form.byproductType.choices.insert(0,('All','Display all'))

    # if request.method == 'POST':
    #     return redirect(url_for("matching_results_waste", giveoutwasteId=giveoutwasteId, byProduct=form.byproductType.data, landSpace=form.landSpace.data, cost=form.investmentCost.data, env=form.environmentalImpact.data))
    # return render_template('matching_filter_waste.html', title="Matching Filter", form=form)
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
    #print(df)
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

    #print(wastematerialID)
    print(df)
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
            #print('Waste CRatio:'+wCRatio)
            #print('Waste NRatio:'+wNRatio)
            #print('Waste pH:'+wphValue)
            #print('RSP pH Range '+techID['pHmin']+' '+techID['pHmax'])
            #print('RSP CRatio'+techID['CRatiomin']+' '+techID['CRatiomax'])
            #print('RSP NRatio'+techID['NRatiomin']+' '+techID['NRatiomax'])
            
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

    return render_template('matching_results_waste.html', result=result )

@app.route("/matching/filter_recycling/<processwasteId>", methods=['GET','POST'])
def matching_filter_recycling(processwasteId):
    techstuff=TechnologyDB.query.filter_by(id=processwasteId).first()
    
    techmaterialID = TechnologyDB.query.filter_by(id=processwasteId).first().materialId
    rset = Giveoutwaste.query.all()
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
    results = defaultdict(list)
    instance = inspect(techstuff)
    for key, x in instance.attrs.items():
        results[key].append(x.value)    
    #techdf = pd.DataFrame(result)
    #print(results)
    #print(df)
    counter=0
    result=[]
    #TechnologyDB.query.filter_by(id=processwasteId).first()
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
    techID = {}
    for at in attrib:
        #print(results[at][0])
        techID[at]=results[at][0]
        
    #print(techmaterialID)
    for i in range(len(df)):
        wastematerialID=int(df.loc[i,'materialId'])
        #print(techmaterialID)
        #print(wastematerialID)      
        if int(techmaterialID)==14 and int(wastematerialID)==1:
            #print("Triggered")
            wasteID = (df.loc[i,'questionCode'])
            print(wasteID)
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
            print(wCRatio)
            print(techID['CRatiomin'])
            print(techID['CRatiomax'])
            
            print(wNRatio)
            print(techID['NRatiomin'])
            print(techID['NRatiomax'])
            
            print(wphValue)
            print(techID['pHmin'])
            print(techID['pHmax'])
                   
            if (wCRatio=='__' or (int(wCRatio)>=int(techID['CRatiomin']) and int(wCRatio)<=int(techID['CRatiomax']))) and ((wNRatio)=='__' or (int(wNRatio)>=int(techID['NRatiomin']) and int(wNRatio)<=int(techID['NRatiomax']))) and ((wphValue)=='__' or (int(wphValue)>=int(techID['pHmin']) and int(wphValue)<=int(techID['pHmax']))):
                counter+=1
                index=(counter)
                desc=(df.loc[i,'description'])
                supplier=(User.query.filter_by(id=int(df.loc[i,'userId'])).first().username)
                #print(supplier)
                rawdate=str(df.loc[i,'date'])
                rawdate=rawdate[:10]
                result.append([index,desc,supplier,rawdate])
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
                result.append([index,desc,supplier,rawdate])
    return render_template('matching_results_recycling.html', result=result )

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


    return render_template('matching_results_buyer.html', result=result,byproduct=byproduct)

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
    return render_template('matching_results_resource.html', title="Matching Results", results=results, materialType=materialType, form=form, order=order, orderName=orderName, takeinresourceId=takeinresourceId,byProduct=byProduct,landSpace=landSpace,cost=cost,env=env)


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


    return render_template('matching_technology.html', title="Matching Technology", technology=technology, technologyBreakdown=technologyBreakdown, navHTML=navHTML)

