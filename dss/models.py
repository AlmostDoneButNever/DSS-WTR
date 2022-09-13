from dss import db, login_manager, app
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

#~~~~~~~~~~~~~~~~~~~~~ USER ~~~~~~~~~~~~~~~~~~~~~~#

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True) 
    username = db.Column(db.String(20), unique=True, nullable=False) 
    email = db.Column(db.String(100), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    wastes = db.relationship("Waste", backref= "user", lazy="select")
    techs = db.relationship("Technology", backref= "user", lazy="select")


    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod 
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)


    def __repr__(self): 
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

#~~~~~~~~~~~~~~~~~~~~~ DATABASE~~~~~~~~~~~~~~~~~~~~~~#
class MaterialDB(db.Model):
    id = db.Column(db.Integer, primary_key = True) 
    category = db.Column(db.String(100), nullable=False)
    material = db.Column(db.String(100), nullable=False)

class FoodWasteDB(db.Model):
    FoodItem = db.Column(db.String(100), primary_key = True)
    C = db.Column(db.Integer)
    H = db.Column(db.Integer)
    N = db.Column(db.Integer)
    moisture = db.Column(db.Float(500))
    pH = db.Column(db.Float(500))
    cellulose = db.Column(db.Float(500))

class ManureDB(db.Model):
    ManureType = db.Column(db.String(100), primary_key = True)
    C = db.Column(db.Float(500))
    H = db.Column(db.Float(500))
    N = db.Column(db.Float(500))
    moisture = db.Column(db.Float(500))
    pH = db.Column(db.Float(500))
    cellulose = db.Column(db.Float(500))

class ProductDB(db.Model):
    ProductName = db.Column(db.String(100), primary_key = True)
    unit = db.Column(db.String(100))

#~~~~~~~~~~~~~~~~~~~~~ REGISTERED WASTE AND TECHNOLOGY ~~~~~~~~~~~~~~~~~~~~~~#

class Waste(db.Model):
    id = db.Column(db.Integer, primary_key = True) 
    userId = db.Column(db.Integer, db.ForeignKey("user.id"))
    materialId = db.Column(db.Integer, nullable=False)
    materialType = db.Column(db.String(100))
    wasteId = db.Column(db.String(1000))
    type = db.Column(db.String(1000))
    description = db.Column(db.String(1000))
    size = db.Column(db.String(1000))
    impurities = db.Column(db.Integer)
    lab = db.Column(db.Integer)
    moistureType = db.Column(db.String(1000))
    moistureValue = db.Column(db.Float(500))
    cellulosicValue = db.Column(db.Float(500))
    homogeneityType = db.Column(db.String(1000))
    homogeneityValue = db.Column(db.Float(500))
    pH = db.Column(db.Float(500))
    CNratio = db.Column(db.Float(500))

    date = db.Column(db.String(100))
    lab_report_path = db.Column(db.String(1000))
    image_path = db.Column(db.String(1000))

class Technology(db.Model):
    id = db.Column(db.Integer, primary_key = True) 
    userId = db.Column(db.Integer, db.ForeignKey("user.id"))
    materialId = db.Column(db.Integer)
    materialType = db.Column(db.String(100))
    description = db.Column(db.String(100))
    technology = db.Column(db.String(100))
    product_list = db.Column(db.String(100))
    CN_min = db.Column(db.Float(100))
    CN_max = db.Column(db.Float(100))
    pH_min = db.Column(db.Float(100))
    pH_max = db.Column(db.Float(100))
    cellulose_min = db.Column(db.Float(100))
    cellulose_max = db.Column(db.Float(100))
    moisture = db.Column(db.String(100))
    homogeneity = db.Column(db.String(100))
    size = db.Column(db.String(100))
    impurities = db.Column(db.String(100))
    CN_criteria = db.Column(db.String(100))
    pH_criteria = db.Column(db.String(100))
    cellulose_criteria = db.Column(db.String(100))
    moisture_criteria = db.Column(db.String(100))
    homogeneity_criteria = db.Column(db.String(100))
    size_criteria = db.Column(db.String(100))
    impurities_criteria = db.Column(db.String(100))
    date = db.Column(db.String(100))
    

#~~~~~~~~~~~~~~~~~~~~~ DISPATCH MATCHING~~~~~~~~~~~~~~~~~~~~~~#

class Dispatchmatchingsupply(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    userId = db.Column(db.Integer, nullable=False)
    wasteId = db.Column(db.Integer, nullable=False)
    materialId = db.Column(db.Integer)
    quantity = db.Column(db.Float(500), nullable=False)
    reservePrice = db.Column(db.Float(500), nullable=False)
    deliveryFee = db.Column(db.Float(500), nullable=False)
    matchedFlag = db.Column(db.Integer, nullable=False)
    postalCode = db.Column(db.String(500))
    date = db.Column(db.String(500))

class Dispatchmatchingdemand(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    userId = db.Column(db.Integer, nullable=False)
    techId = db.Column(db.Integer, nullable=False)
    materialId = db.Column(db.Integer)
    quantity = db.Column(db.Float(500), nullable=False)
    reservePrice = db.Column(db.Float(500), nullable=False)
    matchedFlag = db.Column(db.Integer, nullable=False)
    postalCode = db.Column(db.String(500))
    date = db.Column(db.String(500))

class Dispatchmatchingresults(db.Model):
    no = None
    id = db.Column(db.Integer, primary_key = True)
    supplyId = db.Column(db.Integer, nullable=False)
    demandId = db.Column(db.Integer, nullable=False)
    materialId = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float(500))
    quantity = db.Column(db.Float(500))
    date = db.Column(db.String(500))      



