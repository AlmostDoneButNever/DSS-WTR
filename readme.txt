# Creating and initializing virtual environment
python -m venv .venv
pip install -r packages.txt

# Activating virtual environment
cmd
.\venv\Scripts\activate

# Deactivating virtual environment
.\venv\Scripts\deactivate

# Creating migration
flask db init

# Commit and update database
flask db  migrate -m "version name"
flask db upgrade



from dss import db
from dss.models import User, Waste, Technology

add_user = User(
    username = "angelmah1",
    email = "angelmah1@email.com",
    password = "password"
)

db.session.add(add_user)

add_entry = Waste(
    materialId = 1,
    wasteId = "first"
)
db.session.add(add_entry)
add_user.wastes.append(add_entry)

db.session.commit()