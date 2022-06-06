import matplotlib.pyplot as plt
import numpy as np

import shutil
import sys
import os.path

from pyomo.environ import *

import pandas as pd
from pandas import IndexSlice as idx
from .model import BaseModel

from .data import DataView


def runModel():
    originalPath = os.getcwd()
    os.chdir('dss/PyomoSolver')
    #os.chdir('PyomoSolver')
    
    base_data = pd.read_excel('data_input.xlsx', None)

    supply = base_data['supply'].set_index(['id', "materialId"])

    demand = base_data['demand'].set_index(['id', "materialId"])

    distance = base_data['distance'].set_index(['seller_id', "buyer_id"])
    distance = distance.dropna()

    edges = pd.merge(
                supply.index.to_frame(index=False, name=['producer', 'material']),
                demand.index.to_frame(index=False, name=['consumer', 'material']),
                on='material', how='inner'
            ).set_index(['producer', 'consumer', 'material'])

    # Mask out edges which are not included in the distance table
    mask = [(i,j) in distance.index for (i,j,m) in edges.index]
    edges = edges[mask]

    # Save edge list as a model attribute
    edges = edges.sort_index()

    E = edges.index

    # parameters
    r_p = supply.reservePrice
    r_c = demand.reservePrice
    mu = distance.distance
    tau = supply.deliveryFee
    S_bar = supply.quantity
    D_bar = demand.quantity

    # building the model
    model = ConcreteModel()
    model.dual = Suffix(direction=Suffix.IMPORT)

    # declare decision variables
    model.supply = Var(E,domain=NonNegativeReals)
    model.demand = Var(E,domain=NonNegativeReals)

        #Objective function
    # Objective = producer_surplus + consumer_surplus - delivery_fees
    model.surplus = Objective(expr = 
        sum(-r_p[i,m] * model.supply[i,j,m] for i,j,m in E)                #producer surplus
        +  sum(r_c[j,m] * model.demand[i,j,m] for i,j,m in E)              #consumer surplus
        -  sum(mu[i,j] * tau[i,m] * model.demand[i,j,m] for i,j,m in E)    #delivery fees
        ,sense = maximize)

    # Constraints

    IM = {(i,m) for i,_,m in E if (i,m) in supply.index}
    model.supply_capacity = ConstraintList()
    for i,m in IM:
        E_im = edges.loc[idx[i,:,m], :].index
        x_im = sum( model.supply[i,j,m] for i,j,m in E_im) <= S_bar[i,m]
        model.supply_capacity.add(x_im)

    JM = {(j,m) for _,j,m in edges.index if (j,m) in demand.index}
    model.demand_capacity = ConstraintList()
    for j,m in JM:
        E_jm = edges.loc[idx[:,j,m], :].index
        x_jm = sum(model.demand[i,j,m] for i,j,m in E_jm) <= D_bar[j,m]
        model.demand_capacity.add(x_jm)

    model.market_equilibrium = ConstraintList()
    for i,j,m in edges.index:
        x_ijm = model.demand[i,j,m] - model.supply[i,j,m] == 0
        model.market_equilibrium.add(x_ijm)

    # solve

    solver = SolverFactory('cbc')
    results = solver.solve(model)

    demand_quantity = []
    for i,j,m in E:
        demand_quantity.append(model.demand[i,j,m]())

    # get market equilibrium
    market_equilibrium_val = []
    for index in model.market_equilibrium:
        market_equilibrium_val.append(-model.dual[model.market_equilibrium[index]])

    soln = pd.DataFrame(
        data = map(list, zip(*[market_equilibrium_val,demand_quantity])), #transpose data
        index = pd.MultiIndex.from_tuples(E, names=['producer_id', 'consumer_id', 'material_id']),
        columns = ['price','quantity'])
        
    soln = soln[soln!=0].dropna()

    
    return soln