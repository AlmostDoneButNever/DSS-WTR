from dss.base_feature import *
from dss.matching_v2 import *
from dss.dispatch_matching import *

@app.route("/questions/seller") 
@login_required
def questions_seller():
    samples = Sample.query.all()
    result = defaultdict(list)
    for obj in samples:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)    
    df = pd.DataFrame(result)
    samplefood=df['FoodItem'].tolist()

    materialId = [0,1,2]
    material_questions_dict = {'0':['food_composition'], '1':['Q1','Q2'], '2':['Q2','Q3']}

    questions_id = []
    for item in materialId:
        questions_id.extend(material_questions_dict[str(item)])

    questions_id = list(dict.fromkeys(questions_id))

    return render_template('questions_template_seller.html', questions_id = questions_id, samplefood = samplefood, samplefoodlen=len(samplefood))

@app.route("/questions/rsp") 
@login_required
def questions_rsp():


    materialId = [0,1,2]
    material_questions_dict = {'0':['food_composition'], '1':['Q1','Q2'], '2':['Q2','Q3']}

    questions_id = []
    for item in materialId:
        questions_id.extend(material_questions_dict[str(item)])

    questions_id = list(dict.fromkeys(questions_id))

    return render_template('questions_template_rsp.html', questions_id = questions_id)