from datetime import datetime
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

from dss.matching_algorithm import matching_algorithm_seller

from dss.distance import getDistanceMatrix
  

@app.route("/dispatch_matching", methods=['GET','POST'])
def dispatch_matching():
    form = dispatchMatchingForm()


    prevWasteEntries = [(waste.id, waste.description + ' - ' + waste.date[:10]) for waste in WasteDB.query.filter_by(userId=int(current_user.id)).all()]
    prevWasteEntries.insert(0,(None,None))
    form.wasteSelect.choices = prevWasteEntries

    prevTechEntries = [(tech.id,  tech.description + ' - ' + tech.date[:10]) for tech in TechnologyDB.query.filter_by(userId=int(current_user.id)).group_by(TechnologyDB.description, TechnologyDB.date).all()]
    prevTechEntries.insert(0,(None,None))
    form.techSelect.choices = prevTechEntries

    if request.method == 'POST':
        if request.form['select_role'] == 'waste_seller':
            seller_wasteid = form.wasteSelect.data
            return redirect(url_for('dispatch_matching_questions_waste', seller_wasteid = seller_wasteid))
        else:
            buyer_techid = form.techSelect.data
            return redirect(url_for('dispatch_matching_questions_resource', buyer_techid = buyer_techid))
    return render_template('/dispatch_matching/main.html', title="Dispatch Matching", form=form)


@app.route("/dispatch_matching/questions_waste/<seller_wasteid>", methods=['GET','POST'])
def dispatch_matching_questions_waste(seller_wasteid):

    waste = WasteDB.query.filter_by(id=int(seller_wasteid)).first()

    form = dispatchMatchingQuestionsForm()

    print('seller waste id', seller_wasteid)

    recommendedReservePrice = 640

    if request.method == 'POST':
        if form.wasteName.data!='None' and form.postalCode.data.isnumeric() and len(form.postalCode.data)==6:
            supply = Dispatchmatchingsupply(userId=current_user.id,wasteId = seller_wasteid,materialId = waste.materialId, 
                                                quantity=form.quantity.data, postalCode=form.postalCode.data,
                                                reservePrice=form.reservePrice.data, deliveryFee=form.deliveryFee.data,
                                                matchedFlag=0, date=str(datetime.now())[0:19])

            db.session.add(supply)
            db.session.commit()
            flash('Your response has been recorded!','success')
            return redirect(url_for('dispatch_matching'))
        else:
            flash(f'Please check your inputs','danger')
    return render_template('/dispatch_matching/questions_waste.html', title="Dispatch Matching Questions", form=form, recommendedReservePrice=recommendedReservePrice)



@app.route("/dispatch_matching/questions_resource/<buyer_techid>", methods=['GET','POST'])
def dispatch_matching_questions_resource(buyer_techid):

    first_tech = TechnologyDB.query.filter_by(id=buyer_techid).first()
    all_tech = TechnologyDB.query.filter_by(description = first_tech.description, date = first_tech.date).all()

    materialId = []
    techologyId = []

    for entry in all_tech:
        materialId.append(entry.materialId)
        techologyId.append(entry.id)

    ids = list(zip(techologyId, materialId))
    form = dispatchMatchingQuestionsForm()

    recommendedReservePrice = 21

    if request.method == 'POST':

        print(request.form)
       
        if form.postalCode.data.isnumeric() and len(form.postalCode.data) == 6:

            for (techid, matid) in ids:

                if '1' == str(matid):
                    demand = Dispatchmatchingdemand(userId=current_user.id,techId=techid, materialId = matid, postalCode=form.postalCode.data, 
                                                    quantity=request.form['quantity_food'], reservePrice=request.form['reservePrice_food'],
                                                    matchedFlag=0, date=str(datetime.now())[0:19])

                    db.session.add(demand)
                    db.session.commit()
                    
                if '2' == str(matid):
                    demand = Dispatchmatchingdemand(userId=current_user.id,techId=techid, materialId = matid, postalCode=form.postalCode.data, 
                                                    quantity=request.form['quantity_manure'], reservePrice=request.form['reservePrice_manure'],
                                                    matchedFlag=0, date=str(datetime.now())[0:19])

                    db.session.add(demand)
                    db.session.commit()

                if '3' == str(matid):
                    demand = Dispatchmatchingdemand(userId=current_user.id,techId=techid, materialId = matid, postalCode=form.postalCode.data, 
                                                    quantity=request.form['quantity_wood'], reservePrice=request.form['reservePrice_wood'],
                                                    matchedFlag=0, date=str(datetime.now())[0:19])

                    db.session.add(demand)
                    db.session.commit()
            
            flash('Your response has been recorded!','success')

            return redirect(url_for('dispatch_matching'))
        else:
            flash(f'Please check your inputs','danger')

    return render_template('/dispatch_matching/questions_resource.html', title="Dispatch Matching Questions", form=form, recommendedReservePrice=recommendedReservePrice, materialId = materialId)

@app.route("/dispatch_matching/export")
def dispatch_matching_matchtest():
    seller_df = pd.read_sql_table('Dispatchmatchingsupply', db.session.bind).set_index('id')
    buyer_df = pd.read_sql_table('Dispatchmatchingdemand', db.session.bind).set_index('id')


    distance_df = getDistanceMatrix(seller_df, buyer_df)

    import xlsxwriter as xw

    def export_df(worksheet_name, df):

        # Setting up rows and columns
        target_row = 0
        target_col = 0

        # Write results into excel
        df.to_excel(writer, worksheet_name, startrow = target_row, startcol = target_col, merge_cells = False)

        # Create an new Excel file and add a worksheet.
        workbook = writer.book
        worksheet = writer.sheets[worksheet_name]

    workbook_name = 'data_input'
    workbook_path = 'dss/PyomoSolver/' + str(workbook_name) + '.xlsx'

    with pd.ExcelWriter(workbook_path) as writer: 

        export_df('supply', seller_df)
        export_df('demand', buyer_df)
        export_df('distance', distance_df)
    

    return redirect(url_for('dispatch_matching'))


        
@app.route("/dispatch_matching/solve")
def dispatch_matching_solve():

    solution=PyomoModel.runModel()
    solution = solution.reset_index()
   
    print(solution)

    for i in solution.itertuples():
        result = Dispatchmatchingresults(supplyId=int(i.producer_id),demandId=int(i.consumer_id),materialId=i.material_id,price=i.price,quantity=i.quantity,date=str(datetime.now())[0:11])
        db.session.add(result)
        db.session.commit()


    return redirect(url_for('dispatch_matching'))


@app.route("/dispatch_matching/results", methods=['GET','POST'])
def dispatch_matching_results():
    form = dispatchMatchingResultsForm()
    form.date.choices = [(Dispatchmatchingresult.date, Dispatchmatchingresult.date) for Dispatchmatchingresult in Dispatchmatchingresults.query.group_by(Dispatchmatchingresults.date)]
    
    waste_df = pd.read_sql_table('WasteDB', db.session.bind).set_index('id')
    tech_df = pd.read_sql_table('TechnologyDB', db.session.bind).set_index('id')
    material_df = pd.read_sql_table('MaterialsDB', db.session.bind).set_index('id')
    seller_df = pd.read_sql_table('Dispatchmatchingsupply', db.session.bind).set_index('id')
    buyer_df = pd.read_sql_table('Dispatchmatchingdemand', db.session.bind).set_index('id')
    user_df = pd.read_sql_table('user', db.session.bind).set_index('id')

    
    supplyIds = pd.read_sql_query(sql = Dispatchmatchingsupply.query.filter(Dispatchmatchingsupply.userId == current_user.id).statement, con=db.session.bind).set_index('id')

  

    sellers = pd.read_sql_query(sql = Dispatchmatchingresults.query.filter(Dispatchmatchingresults.supplyId.in_(supplyIds.index), Dispatchmatchingresults.date == form.date.data).statement, con=db.session.bind)
    sellers['supplyName']  = ''
    sellers['demandName']  = ''
    sellers['materialName']  = ''
    sellers['buyerName']  = ''


    demandIds = pd.read_sql_query(sql = Dispatchmatchingdemand.query.filter(Dispatchmatchingdemand.userId == current_user.id).statement, con=db.session.bind).set_index('id')

    buyers = pd.read_sql_query(sql = Dispatchmatchingresults.query.filter(Dispatchmatchingresults.demandId.in_(demandIds.index), Dispatchmatchingresults.date == form.date.data).statement, con=db.session.bind)
    buyers['supplyName']  = ''
    buyers['demandName']  = ''
    buyers['materialName']  = ''
    buyers['sellerName']  = ''

    sellers_list = []
    buyers_list = []

    print(supplyIds)
    print(sellers)

    print(demandIds)
    print(buyers)


    if request.method == 'POST':

        #get matched buyers

        if form.buySell.data != '2':
            
            for i in sellers.index:
                supplyId = sellers.loc[i,'supplyId']
                demandId = sellers.loc[i,'demandId']
                materialId = sellers.loc[i,'materialId']

                waste_id = seller_df.loc[supplyId, 'wasteId']
                tech_id = buyer_df.loc[demandId, 'techId']
                tech_userid = buyer_df.loc[demandId, 'userId']

                sellers.loc[i,'supplyName'] = waste_df.loc[waste_id, 'description']
                sellers.loc[i,'demandName'] = tech_df.loc[tech_id, 'description']
                sellers.loc[i,'materialName'] = material_df.loc[materialId, 'material']
                sellers.loc[i,'buyerName'] = user_df.loc[tech_userid, 'username']

            sellers = sellers.reset_index()
            sellers_list = sellers.values.tolist()
            print(sellers_list)

        if form.buySell.data != '1':
        #get matched sellers
            for i in buyers.index:
                supplyId = buyers.loc[i,'supplyId']
                demandId = buyers.loc[i,'demandId']
                materialId = buyers.loc[i,'materialId']

                waste_id = seller_df.loc[supplyId, 'wasteId']
                seller_userid = seller_df.loc[supplyId, 'userId']

                tech_id = buyer_df.loc[demandId, 'techId']

                buyers.loc[i,'supplyName'] = waste_df.loc[waste_id, 'description']
                buyers.loc[i,'demandName'] = tech_df.loc[tech_id, 'description']
                buyers.loc[i,'materialName'] = material_df.loc[materialId, 'material']
                buyers.loc[i,'sellerName'] = user_df.loc[seller_userid, 'username']

            buyers = buyers.reset_index()
            buyers_list = buyers.values.tolist()
            print(buyers_list)
           
        return render_template('dispatch_matching_results.html', title="Dispatch Matching Results", form=form, match = True, sellers = sellers_list, buyers = buyers_list)

    return render_template('dispatch_matching_results.html', title="Dispatch Matching Results", form=form)