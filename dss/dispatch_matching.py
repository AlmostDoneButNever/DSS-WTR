import requests as r
from onemapsg import OneMap
import json
from collections import defaultdict
from sqlalchemy.inspection import inspect
import os
import pandas as pd
from flask import render_template
from flask import url_for 
from flask import flash 
from flask import redirect
from flask import request, abort
from flask import jsonify
from dss import app, db, bcrypt, mail
from dss.forms import (dispatchMatchingForm, dispatchMatchingQuestionsForm, dispatchMatchingResultsForm,
    LCCForm, CPForm) 
from dss.models import (User, Materials, Giveoutwaste,Dispatchmatchingresults, Dispatchmatchingsupply, Dispatchmatchingdemand, TechnologyDB, Dispatchmatchinginvestment, WasteDB)
from flask_login import current_user
from dss.dispatchMatchingSavingsBreakdown import CostSavings

from .PyomoSolver import PyomoModel
from .PyomoSolver import PyomoModelInvest

from .LCCTest import TechSpecifications


def distance(start,end):
    email = "e0175262@u.nus.edu"
    passw = "Password1"

    locSupply = start
    locDemand = end


    # print(sorted([locSupply,locDemand]))
    #loc1, loc2 = [locSupply,locDemand].sort()

    try:
        onemap = OneMap(email,passw)
        loc1 = onemap.search(locSupply).results[0]
        loc2 = onemap.search(locDemand).results[0]

        loc1_latlong = ','.join(loc1.lat_long)
        loc2_latlong = ','.join(loc2.lat_long)
    
        route = onemap.route(loc1_latlong, loc2_latlong, 'drive')
        return route.route_summary['total_distance']
    except:
        return 0

def feasibility_check(techid,wasteid):
    rset = Giveoutwaste.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    waste_df = pd.DataFrame(result)

    rset = TechnologyDB.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    RSP_df = pd.DataFrame(result)

    rset = Materials.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    materials_df = pd.DataFrame(result)

    # try:
    waste_material_id=waste_df.loc[waste_df['id'] == int(wasteid), 'materialId'].iloc[0]
    waste_questioncode=waste_df.loc[waste_df['id']==int(wasteid),'questionCode'].iloc[0]
    tech_material_id=RSP_df.loc[RSP_df['id'] == int(techid), 'materialId'].iloc[0]
    RSP_df.set_index('id',inplace=True)
    tech_material=(materials_df.loc[materials_df['id'] == int(tech_material_id), 'material'].iloc[0])
    waste_material=(materials_df.loc[materials_df['id'] == int(waste_material_id), 'material'].iloc[0])
    print(tech_material[0:len(waste_material)])
    print(waste_material)
    if tech_material[0:len(waste_material)]!=waste_material:
        return 0
    else:
        if tech_material=='Food Waste':
            homogeneity=waste_questioncode[1]
            wCHNType=waste_questioncode[2]
            wCRatio=waste_questioncode[3:5]
            wHRatio=waste_questioncode[5:7]
            wNRatio=waste_questioncode[7:9]
            wproteinType=waste_questioncode[9]
            wproteinRatio=waste_questioncode[10:12]
            wcellulosic=waste_questioncode[12]
            wshellAndBones=waste_questioncode[13:15]
            wmoistureType=waste_questioncode[15]
            wmoistureContent=waste_questioncode[16:18]
            wsaltType=waste_questioncode[18]
            wsaltContent=waste_questioncode[19:21]
            wpHType=waste_questioncode[21]
            wphValue=waste_questioncode[22:24]
            wparticleSize=waste_questioncode[24]

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
            #print(df.loc[i,'description'])
            #print(techID)
            for at in attrib:
                techID[at]=RSP_df.loc[techid,at]
            # print('Buyer:'+str(techid))
            # print('Seller:'+str(wasteid))
            # print('Waste CRatio:'+wCRatio)
            # print('Waste NRatio:'+wNRatio)
            # print('Waste pH:'+wphValue)
            # print('RSP pH Range '+techID['pHmin']+' '+techID['pHmax'])
            # print('RSP CRatio'+techID['CRatiomin']+' '+techID['CRatiomax'])
            # print('RSP NRatio'+techID['NRatiomin']+' '+techID['NRatiomax'])
            
            if (wCRatio=='__' or (int(wCRatio)>=int(techID['CRatiomin']) and int(wCRatio)<=int(techID['CRatiomax']))) and ((wNRatio)=='__' or (int(wNRatio)>=int(techID['NRatiomin']) and int(wNRatio)<=int(techID['NRatiomax']))) and ((wphValue)=='__' or (int(wphValue)>=int(techID['pHmin']) and int(wphValue)<=int(techID['pHmax']))):
                return 1
            else:
                return 0
        else:
            print('pass')
            return 1
    # except:
    #     return 0




    





#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@app.route("/dispatch_matching", methods=['GET','POST'])
def dispatch_matching():
    form = dispatchMatchingForm()


    prevWasteEntries = [(waste.id, waste.description + ' - ' + waste.date[:10]) for waste in WasteDB.query.filter_by(userId=int(current_user.id)).all()]
    prevWasteEntries.insert(0,(None,None))
    form.wasteSelect.choices = prevWasteEntries

    prevTechEntries = [(tech.id,  tech.description + ' - ' + tech.date[:10]) for tech in TechnologyDB.query.filter_by(userId=int(current_user.id)).all()]
    prevTechEntries.insert(0,(None,None))
    form.techSelect.choices = prevTechEntries

    if request.method == 'POST':
        if form.type.data == '0':
            return redirect(url_for('dispatch_matching_questions_waste'))
        else:
            return redirect(url_for('dispatch_matching_questions_resource'))
    return render_template('dispatch_matching.html', title="Dispatch Matching", form=form)


@app.route("/dispatch_matching/questions_waste", methods=['GET','POST'])
def dispatch_matching_questions_waste():
    form = dispatchMatchingQuestionsForm()
    #get past waste ID
    prevEntries = [(waste.id, waste.description + ' - ' + waste.date) for waste in WasteDB.query.filter_by(userId=int(current_user.id)).all()]
    prevEntries.insert(0,(None,None))
    form.wasteName.choices = prevEntries

    recommendedReservePrice = 640

    if request.method == 'POST':
        supply = Dispatchmatchingsupply(userId=current_user.id,giveOutWasteId=form.wasteName.data,quantity=form.quantity.data,postalCode=form.postalCode.data,reservePrice=form.reservePrice.data,deliveryFee=form.deliveryFee.data,matchedFlag=0)
        if form.wasteName.data!='None' and form.postalCode.data.isnumeric() and len(form.postalCode.data)==6:
            db.session.add(supply)
            db.session.commit()
            flash('Your response has been recorded!','success')
            return redirect(url_for('dispatch_matching'))
        else:
            flash(f'Please check your inputs','danger')
    return render_template('dispatch_matching_questions_waste.html', title="Dispatch Matching Questions", form=form, recommendedReservePrice=recommendedReservePrice)

@app.route("/dispatch_matching/match", methods=['GET','POST'])
def dispatch_matching_match():
    rset = Dispatchmatchinginvestment.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_investment = pd.DataFrame(result)
    rset = Dispatchmatchingdemand.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_demand = pd.DataFrame(result)
    rset = Dispatchmatchingsupply.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_supply = pd.DataFrame(result)
    rset = Materials.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_materials = pd.DataFrame(result)
    rset = User.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_user = pd.DataFrame(result)
    rset = Giveoutwaste.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_waste = pd.DataFrame(result)
    rset = TechnologyDB.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_technology = pd.DataFrame(result)
    
    material_list=[]
    entity_list=[]
    company_list=[]
    postal_list=[]
    long_list=[]
    lat_list=[]
    BS_list=[]
    industry_supply_df=pd.DataFrame(columns=['entity','material','quantity','reserve_price','delivery_fee'])
    industry_demand_df=pd.DataFrame(columns=['entity','material','quantity','reserve_price'])
    for i in raw_demand.itertuples():
        company_list.append(raw_user.loc[raw_user['id'] == int(i.userId), 'username'].iloc[0])
        entity_list.append(i.takeInResourceId)
        postal_list.append(i.postalCode)
        BS_list.append('B')
        response = r.get('http://developers.onemap.sg/commonapi/search?searchVal='+i.postalCode+'&returnGeom=Y&getAddrDetails=Y&pageNum={1}')
        response_dict = json.loads(response.text)
        if response_dict['found']!=0:
            results = response_dict['results'][0]
            long_list.append(results['LONGITUDE'])
            lat_list.append(results['LATITUDE'])
        else:
            long_list.append(None)
            lat_list.append(None)
        material_id=raw_technology.loc[raw_technology['id'] == int(i.takeInResourceId), 'materialId'].iloc[0]
        material_entry=raw_materials.loc[raw_materials['id']== int(material_id),'material'].iloc[0]
        industry_demand_df = industry_demand_df.append({'entity' : i.takeInResourceId, 'material': material_entry, 'quantity': i.quantity, 'reserve_price': i.reservePrice}, ignore_index = True)
        if material_entry not in material_list:
            material_list.append(material_entry)
    for i in raw_supply.itertuples():
        company_list.append(raw_user.loc[raw_user['id'] == int(i.userId), 'username'].iloc[0])
        entity_list.append(i.giveOutWasteId)
        postal_list.append(i.postalCode)
        BS_list.append('S')
        response = r.get('http://developers.onemap.sg/commonapi/search?searchVal='+i.postalCode+'&returnGeom=Y&getAddrDetails=Y&pageNum={1}')
        response_dict = json.loads(response.text)
        if response_dict['found']!=0:
            results = response_dict['results'][0]
            long_list.append(results['LONGITUDE'])
            lat_list.append(results['LATITUDE'])
        else:
            long_list.append(None)
            lat_list.append(None)
        material_id=raw_waste.loc[raw_waste['id'] == int(i.giveOutWasteId), 'materialId'].iloc[0]
        material_entry=raw_materials.loc[raw_materials['id']==int(material_id),'material'].iloc[0]
        industry_supply_df = industry_supply_df.append({'entity' : i.giveOutWasteId, 'material': material_entry, 'quantity': i.quantity, 'reserve_price': i.reservePrice, 'delivery_fee': i.deliveryFee}, ignore_index = True)
        if material_entry not in material_list:
            material_list.append(material_entry)
    material_df=pd.DataFrame({'material': material_list})
    entity_df=pd.DataFrame({'entity': entity_list})
    industry_df=pd.DataFrame({'entity': entity_list, 'company': company_list, 'postal_code': postal_list, 'lat': lat_list, 'lon': long_list, 'BS': BS_list})
    distance_df= pd.DataFrame(index=range(len(entity_list)),columns=['entity']+list(range(len(entity_list))))
    distance_df=distance_df.assign(entity=entity_list)
    distance_df=distance_df.set_index('entity')
    feasible_df = distance_df.copy()
    for i in industry_df.itertuples():
        counter=0
        for j in industry_df.itertuples():
            if i.BS != j.BS:
                # if (i.BS=='B' and (industry_demand_df.loc[industry_demand_df['entity'] == int(i.entity), 'material'].iloc[0]==industry_supply_df.loc[industry_supply_df['entity'] == int(j.entity), 'material'].iloc[0])):
                #     if feasibility_check(i.entity,j.entity)==1:
                #         feasible_df.loc[i.entity,j.entity]=0
                #         distance_df.loc[i.entity,j.entity]=distance(i.postal_code,j.postal_code)/1000.0
                        
                if (i.BS=='S'):
                    if feasibility_check(j.entity,i.entity)==1:
                        feasible_df.loc[i.entity,counter]=0
                        distance_df.loc[i.entity,counter]=distance(i.postal_code,j.postal_code)/1000.0
            counter+=1
    print(feasible_df)
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    report_path = 'dss/PyomoSolver/'
    if not os.path.exists(report_path):
        os.makedirs(report_path)
    writer = pd.ExcelWriter(os.path.join(report_path + 'case_data.xlsx'), engine='xlsxwriter')

    # Write each dataframe to a different worksheet.
    material_df.to_excel(writer, sheet_name='material',index=False)
    entity_df.to_excel(writer, sheet_name='entity',index=False)
    industry_df.to_excel(writer, sheet_name='industry',index=False)
    industry_supply_df.to_excel(writer, sheet_name='industry_supply',index=False)
    industry_demand_df.to_excel(writer, sheet_name='industry_demand',index=False)
    feasible_df.to_excel(writer, sheet_name='feasible',index=True)
    distance_df.to_excel(writer, sheet_name='distance',index=True)
    

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

    solution=PyomoModel.runModel()
    writer = pd.ExcelWriter(os.path.join(report_path + 'solution.xlsx'), engine='xlsxwriter')
    solution.to_excel(writer, sheet_name='soln',index=True)
    writer.save()

    solution.reset_index(inplace=True)
    for i in solution.itertuples():
        result = Dispatchmatchingresults(supplyId=int(i.producer_id)-len(raw_demand)+1,demandId=int(i.consumer_id)+1,materialId=i.material_id,price=i.price,quantity=i.quantity,date=str(datetime.now())[0:11])
        db.session.add(result)
        db.session.commit()
    

    return redirect(url_for('dispatch_matching_results'))
    

@app.route("/dispatch_matching/questions_resource", methods=['GET','POST'])
def dispatch_matching_questions_resource():
    form = dispatchMatchingQuestionsForm()
    prevEntries = [(waste.id, waste.TechnologyName + ': ' + waste.description + ' - ' + waste.date[:10]) for waste in TechnologyDB.query.filter_by(userId=int(current_user.id)).all()]
    prevEntries.insert(0,(None,None))
    form.wasteName.choices = prevEntries

    recommendedReservePrice = 21

    if request.method == 'POST':
        demand = Dispatchmatchingdemand(userId=current_user.id,takeInResourceId=form.wasteName.data,quantity=form.quantity.data,postalCode=form.postalCode.data,reservePrice=form.reservePrice.data,matchedFlag=0)
        if form.wasteName.data!='None' and form.postalCode.data.isnumeric() and len(form.postalCode.data) == 6:
            db.session.add(demand)
            db.session.commit()
            flash('Your response has been recorded!','success')
            return redirect(url_for('dispatch_matching'))
        else:
            flash(f'Please check your inputs','danger')
    return render_template('dispatch_matching_questions_resource.html', title="Dispatch Matching Questions", form=form, recommendedReservePrice=recommendedReservePrice)


@app.route("/dispatch_matching/results", methods=['GET','POST'])
def dispatch_matching_results():
    form = dispatchMatchingResultsForm()

    #user change to current user id in the future
    # userId = 113
    userId = current_user.id


    form.date.choices = [(Dispatchmatchingresult.date, Dispatchmatchingresult.date) for Dispatchmatchingresult in Dispatchmatchingresults.query.group_by(Dispatchmatchingresults.date)]

    # soln = PyomoModel.runModel()
    # soln = soln.to_html(classes=["table","table-hover"])

    if request.method == 'POST':
        sell = []
        supplierSurplus = None
        buy = []
        demandSurplus = None
        #get matched buyers
        print(userId)
        print(form.buySell.data)
        if form.buySell.data != '2':
            supplyIds = Dispatchmatchingsupply.query.filter_by(userId=userId).all()
            
            print(supplyIds)
            for supplyId in supplyIds:
                sell.extend(Dispatchmatchingresults.query.filter_by(supplyId=supplyId.id, date=form.date.data).all())
            print(sell)
            #set running number and surplus
            supplierSurplus = 0
            for i in range(len(sell)):
                sell[i].no = str(i+1)+'.'
                supplierSurplus += float(sell[i].supplierSurplus())
            supplierSurplus = "{:.2f}".format(supplierSurplus)
            print(supplierSurplus)
        if form.buySell.data != '1':
        #get matched sellers
            demandIds = Dispatchmatchingdemand.query.filter_by(userId=userId).all()
            for demandId in demandIds:    
                buy.extend(Dispatchmatchingresults.query.filter_by(demandId=demandId.id, date=form.date.data).all())
            
            #set running number and surplus
            demandSurplus = 0
            for i in range(len(buy)):
                buy[i].no = str(i+1)+'.'
                demandSurplus += float(buy[i].demandSurplus())
            demandSurplus = "{:.2f}".format(demandSurplus)
            print(demandSurplus) 
                        
        return render_template('dispatch_matching_results.html', title="Dispatch Matching Results", form=form, match=True, sell=sell, buy=buy, date=form.date.data, supplierSurplus=supplierSurplus, demandSurplus=demandSurplus)

    return render_template('dispatch_matching_results.html', title="Dispatch Matching Results", form=form)

@app.route("/dispatch_matching/results/savings/<date>/<buySell>", methods=['GET','POST'])
def dispatch_matching_results_savings(date, buySell):

    userId = 113

    buyBreakdown,sellBreakdown,supplierSurplus,demandSurplus = 0,0,0,0
    

    
    if buySell == '0':
        sellBreakdown = []
        supplyIds = Dispatchmatchingsupply.query.filter_by(userId=userId).all()
        #get relevant matches    
        for supplyId in supplyIds:
            sellBreakdown.extend(Dispatchmatchingresults.query.filter_by(supplyId=supplyId.id, date=date).all() ) 
        for i in range(len(sellBreakdown)):
            sellBreakdown[i] = CostSavings(sell=sellBreakdown[i])

        #calculate surplus
        supplierSurplus = 0
        for i in range(len(sellBreakdown)):
            supplierSurplus += float(sellBreakdown[i].surplus)
        supplierSurplus = "{:.2f}".format(supplierSurplus) 

    if buySell == '1':
        buyBreakdown = []
        demandIds = Dispatchmatchingdemand.query.filter_by(userId=userId).all()
        #get relevant matches
        for demandId in demandIds:    
            buyBreakdown.extend(Dispatchmatchingresults.query.filter_by(demandId=demandId.id, date=date).all())
        for i in range(len(buyBreakdown)):
            buyBreakdown[i] = CostSavings(buy=buyBreakdown[i])
        
        #calculate surplus
        demandSurplus = 0
        for i in range(len(buyBreakdown)):
            demandSurplus += float(buyBreakdown[i].surplus)
        demandSurplus = "{:.2f}".format(demandSurplus) 



    return render_template('dispatch_matching_results_savings.html', title="Dispatch Matching Cost Breakdown", sellBreakdown=sellBreakdown, supplierSurplus=supplierSurplus, buyBreakdown=buyBreakdown, demandSurplus=demandSurplus)

@app.route("/capacity_planning", methods=['GET','POST'])
def capacity_planning():
    if current_user.is_authenticated:
        pass
    else: 
        flash(f'Please log in first','danger')
        return redirect(url_for("login"))
    rset = Dispatchmatchinginvestment.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    df = pd.DataFrame(result)
    counter=0
    result=[]
    for i in df.itertuples():
        result.append([i.id,i.name,i.cost,i.material,i.reservePrice,i.capacity])

    
    return render_template('capacity_planning.html', title="Capacity Planning", result=result)

@app.route("/capacity_planning/budget", methods=['GET','POST'])
def allocate_budget():
    form = []
    if request.method == 'POST':
        budget=request.form['budget']
        print(budget)
        flash('Your response has been recorded!','success')
        return redirect(url_for('allocate',budget=budget))
    else:
        flash(f'Please check your inputs','danger')
    return render_template('capacity_planning_budget.html', title="Capacity Planning - Budget", form=form)

@app.route("/capacity_planning/allocate/<budget>", methods=['GET','POST'])
def allocate(budget):
    rset = Dispatchmatchinginvestment.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_investment = pd.DataFrame(result)
    rset = Dispatchmatchingdemand.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_demand = pd.DataFrame(result)
    rset = Dispatchmatchingsupply.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_supply = pd.DataFrame(result)
    rset = Materials.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_materials = pd.DataFrame(result)
    rset = User.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_user = pd.DataFrame(result)
    rset = Giveoutwaste.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_waste = pd.DataFrame(result)
    rset = TechnologyDB.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    raw_technology = pd.DataFrame(result)
    
    material_list=[]
    entity_list=[]
    company_list=[]
    postal_list=[]
    long_list=[]
    lat_list=[]
    BS_list=[]
    invest_entity_list=[]
    invest_material_list=[]
    invest_quantity_list=[]
    invest_rp_list=[]
    invest_cost_list=[]

    industry_supply_df=pd.DataFrame(columns=['entity','material','quantity','reserve_price','delivery_fee'])
    industry_demand_df=pd.DataFrame(columns=['entity','material','quantity','reserve_price'])
    investment_demand_df=pd.DataFrame(columns=['entity','material','quantity','reserve_price'])
    investment_cost_df=pd.DataFrame(columns=['entity','invest_cost'])
    for i in raw_demand.itertuples():
        company_list.append(raw_user.loc[raw_user['id'] == int(i.userId), 'username'].iloc[0])
        entity_list.append(i.takeInResourceId)
        postal_list.append(i.postalCode)
        BS_list.append('B')
        response = r.get('http://developers.onemap.sg/commonapi/search?searchVal='+i.postalCode+'&returnGeom=Y&getAddrDetails=Y&pageNum={1}')
        response_dict = json.loads(response.text)
        if response_dict['found']!=0:
            results = response_dict['results'][0]
            long_list.append(results['LONGITUDE'])
            lat_list.append(results['LATITUDE'])
        else:
            long_list.append(None)
            lat_list.append(None)
        material_id=raw_technology.loc[raw_technology['id'] == int(i.takeInResourceId), 'materialId'].iloc[0]
        material_entry=raw_materials.loc[raw_materials['id']== int(material_id),'material'].iloc[0]
        industry_demand_df = industry_demand_df.append({'entity' : i.takeInResourceId, 'material': material_entry, 'quantity': i.quantity, 'reserve_price': i.reservePrice}, ignore_index = True)
        if material_entry not in material_list:
            material_list.append(material_entry)
    for i in raw_supply.itertuples():
        company_list.append(raw_user.loc[raw_user['id'] == int(i.userId), 'username'].iloc[0])
        entity_list.append(i.giveOutWasteId)
        postal_list.append(i.postalCode)
        BS_list.append('S')
        response = r.get('http://developers.onemap.sg/commonapi/search?searchVal='+i.postalCode+'&returnGeom=Y&getAddrDetails=Y&pageNum={1}')
        response_dict = json.loads(response.text)
        if response_dict['found']!=0:
            results = response_dict['results'][0]
            long_list.append(results['LONGITUDE'])
            lat_list.append(results['LATITUDE'])
        else:
            long_list.append(None)
            lat_list.append(None)
        material_id=raw_waste.loc[raw_waste['id'] == int(i.giveOutWasteId), 'materialId'].iloc[0]
        material_entry=raw_materials.loc[raw_materials['id']==int(material_id),'material'].iloc[0]
        industry_supply_df = industry_supply_df.append({'entity' : i.giveOutWasteId, 'material': material_entry, 'quantity': i.quantity, 'reserve_price': i.reservePrice, 'delivery_fee': i.deliveryFee}, ignore_index = True)
        if material_entry not in material_list:
            material_list.append(material_entry)
    for i in raw_investment.itertuples():
        invest_entity_list.append('E'+str(i.id))
        invest_material_list.append(i.material)
        invest_quantity_list.append(i.capacity)
        invest_rp_list.append(i.reservePrice)
        invest_cost_list.append(i.cost)
    investment_demand_df=pd.DataFrame({'entity':invest_entity_list,'material':invest_material_list,'quantity':invest_quantity_list,'reserve_price':invest_rp_list})
    investment_cost_df=pd.DataFrame({'entity':invest_entity_list,'invest_cost':invest_cost_list})
    material_df=pd.DataFrame({'material': material_list})
    entity_df=pd.DataFrame({'entity': entity_list+invest_entity_list})
    industry_df=pd.DataFrame({'entity': entity_list, 'company': company_list, 'postal_code': postal_list, 'lat': lat_list, 'lon': long_list, 'BS': BS_list})
    distance_df= pd.DataFrame(index=range(len(entity_list)+len(invest_entity_list)),columns=['entity']+list(range(len(entity_list)+len(invest_entity_list))))
    distance_df=distance_df.assign(entity=entity_list+invest_entity_list)
    distance_df=distance_df.set_index('entity')
    feasible_df = distance_df.copy()
    for i in industry_df.itertuples():
        counter=0
        for j in industry_df.itertuples():
            if i.BS != j.BS:
                # if (i.BS=='B' and (industry_demand_df.loc[industry_demand_df['entity'] == int(i.entity), 'material'].iloc[0]==industry_supply_df.loc[industry_supply_df['entity'] == int(j.entity), 'material'].iloc[0])):
                #     if feasibility_check(i.entity,j.entity)==1:
                #         feasible_df.loc[i.entity,j.entity]=0
                #         distance_df.loc[i.entity,j.entity]=distance(i.postal_code,j.postal_code)/1000.0
                        
                if (i.BS=='S'):
                    if feasibility_check(j.entity,i.entity)==1:
                        feasible_df.loc[i.entity,counter]=0
                        distance_df.loc[i.entity,counter]=distance(i.postal_code,j.postal_code)/1000.0
            counter+=1
        kcounter=0
        for k in investment_demand_df.itertuples():
            if (i.BS=='S' and (industry_supply_df.loc[industry_supply_df['entity'] == int(i.entity), 'material'].iloc[0][0:7]==k.material[0:7])):
                feasible_df.loc[i.entity,kcounter+len(industry_df)]=0
                distance_df.loc[i.entity,kcounter+len(industry_df)]=0
            kcounter+=1
    print(feasible_df)
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    report_path = 'dss/PyomoSolver/'
    if not os.path.exists(report_path):
        os.makedirs(report_path)
    writer = pd.ExcelWriter(os.path.join(report_path + 'case_data.xlsx'), engine='xlsxwriter')

    # Write each dataframe to a different worksheet.
    material_df.to_excel(writer, sheet_name='material',index=False)
    entity_df.to_excel(writer, sheet_name='entity',index=False)
    industry_df.to_excel(writer, sheet_name='industry',index=False)
    industry_supply_df.to_excel(writer, sheet_name='industry_supply',index=False)
    industry_demand_df.to_excel(writer, sheet_name='industry_demand',index=False)
    investment_demand_df.to_excel(writer, sheet_name='investment_demand',index=False)
    investment_cost_df.to_excel(writer, sheet_name='invest_cost',index=False)
    feasible_df.to_excel(writer, sheet_name='feasible',index=True)
    distance_df.to_excel(writer, sheet_name='distance',index=True)
    

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

    solution, investmentsolution=PyomoModelInvest.runModel(budget)
    writer = pd.ExcelWriter(os.path.join(report_path + 'solution.xlsx'), engine='xlsxwriter')
    solution.to_excel(writer, sheet_name='soln',index=True)
    investmentsolution.to_excel(writer, sheet_name='investmentsoln',index=True)
    writer.save()
    result=[]
    count=0
    investmentsolution=investmentsolution.reset_index()
    for i in raw_investment.itertuples():
        result.append([i.id,i.name,"{:.2f}".format(i.cost),i.material,"{:.2f}".format(int(i.reservePrice)/1.0),i.capacity,int(investmentsolution.at[count,'quantity']),"{:.2f}".format(int(investmentsolution.at[count,'quantity']*int(i.cost)))])
        count+=1
    return render_template('capacity_planning_result.html', title="Capacity Planning - Alloction Results",result=result,budget=budget)

    

        
    


@app.route("/capacity_planning/adding_tech", methods=['GET','POST'])
def adding_tech():
    
    rset = Materials.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    df = pd.DataFrame(result)

    rset = User.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    userdf = pd.DataFrame(result)
    
    rset = TechnologyDB.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    techdf = pd.DataFrame(result)
    
    rset = Dispatchmatchingdemand.query.all()
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    demanddf = pd.DataFrame(result)
    

    materiallist=[]
    for i in df.itertuples():
        if i.material not in materiallist:
            materiallist.append(i.material)
    materiallistlen=len(materiallist)
    form = CPForm()
    print(userdf.columns.tolist())
    #get past technology ID
    print(techdf.loc[techdf['userId'] == int('140'), 'TechnologyName'])
    prevEntries = [(tech.takeInResourceId, techdf.loc[techdf['userId'] == int(tech.userId), 'TechnologyName'].iloc[0] + ' - ' + userdf.loc[userdf['id'] == int(tech.userId), 'username'].iloc[0]) for tech in Dispatchmatchingdemand.query.all()]
    prevEntries.insert(0,(None,None))
    form.technologyID.choices = prevEntries
    # flash(prevEntries, 'success')

    if request.method == 'POST':
        print(form.technologyID.data)
        print(request.form)
        print('name ')
        print(techdf.loc[techdf['id'] == int(form.technologyID.data), 'TechnologyName'])
        print('cost ')
        print(techdf.loc[techdf['id'] == int(form.technologyID.data), 'cost'].iloc[0])
        print('material ')
        print((techdf.loc[techdf['id'] == int(form.technologyID.data), 'materialId'].iloc[0]))
        print(df.loc[df['id'] == int(techdf.loc[techdf['id'] == int(form.technologyID.data), 'materialId'].iloc[0]),'material'].iloc[0])
        print('reserve price ')
        print(demanddf.loc[demanddf['takeInResourceId'] == int(form.technologyID.data), 'reservePrice'].iloc[0])
        print('capacity ')
        print(demanddf.loc[demanddf['takeInResourceId'] == int(form.technologyID.data), 'quantity'].iloc[0])
        invest = Dispatchmatchinginvestment(name=techdf.loc[techdf['id'] == int(form.technologyID.data), 'TechnologyName'].iloc[0],cost=int(techdf.loc[techdf['id'] == int(form.technologyID.data), 'cost'].iloc[0]),material=df.loc[df['id'] == int(techdf.loc[techdf['id'] == int(form.technologyID.data), 'materialId'].iloc[0]),'material'].iloc[0],reservePrice=demanddf.loc[demanddf['takeInResourceId'] == int(form.technologyID.data), 'reservePrice'].iloc[0],capacity=demanddf.loc[demanddf['takeInResourceId'] == int(form.technologyID.data), 'quantity'].iloc[0])
        db.session.add(invest)
        db.session.commit()
        flash('Your response has been recorded!','success')
        return redirect(url_for('capacity_planning'))
    else:
        flash(f'Please check your inputs','danger')
    return render_template('adding_tech.html', title="Capacity Planning - Adding New Technology",materiallist=materiallist,materiallistlen=materiallistlen,form=form)



@app.route("/dispatch_matching/results/contact", methods=['GET','POST'])
def dispatch_matching_results_contact():
    return render_template('dispatch_matching_results_contact.html', title="Dispatch Matching Contact")



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@app.route("/LCC", methods=['GET','POST'])
def LCC():
    form = LCCForm()
    if request.method == 'POST':
        return redirect(url_for('LCC_results', technologyId=form.technology.data, weightPerYear=form.weightPerYear.data, disposalCostPerTon=form.disposalCostPerTon.data, discountRate=form.discountRate.data ))
    return render_template('LCC.html', title="LCC Analysis", form=form)

@app.route("/LCC/results/<technologyId>/<weightPerYear>/<disposalCostPerTon>/<discountRate>", methods=['GET','POST'])
def LCC_results(technologyId,weightPerYear,disposalCostPerTon,discountRate):

    #tech specifications (stored in database)
    noOfYears = 10      #machine lifespan?
    capitalCost = 50000

    rawMaterialCost = 3017.13
    utilitiesCost = 49.91
    maintenanceCost = 5000
    maintenanceFrequency = [3,7]     #list of years that machine requires maintenance
    salvageValue = 25000

    #tech output 
    #figure out how to store this in database
    byproductName = ['Gold', 'Silver', 'Palladium']
    percentageExtraction = [0.97, 0.98, 0.93]
    percentageComposition = [0.00025, 0.0001, 0.001]

    #see if can extract from Quandl
    price = [58141868.4, 620966.57, 65073624.0]

    #process material data
    byproductSpecifications = []
    for i in range(len(byproductName)):
        row = []
        row.append(byproductName[i])
        row.append(round(percentageExtraction[i]*percentageComposition[i]*price[i],2))
        row.append(percentageExtraction[i])
        row.append(percentageComposition[i])
        row.append(price[i])

        byproductSpecifications.append(row)
    # flash(byproductSpecifications,'success')

    
    #create technology object
    tech = TechSpecifications(noOfYears, capitalCost, rawMaterialCost, utilitiesCost, maintenanceCost, 
        maintenanceFrequency, salvageValue, byproductName, percentageExtraction, percentageComposition)

    return render_template('LCC_results.html', title="LCC Results", tech=tech, byproductSpecifications=byproductSpecifications, weightPerYear=float(weightPerYear), disposalCostPerTon=float(disposalCostPerTon), discountRate=float(discountRate), price=price)