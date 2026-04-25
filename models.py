from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# DB is created BUT not connected to Flask yet
db = SQLAlchemy()


# creating a blue print of a table
class User(db.Model, UserMixin):
    id = db.Column(db.Integer,primary_key = True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))   
    email = db.Column(db.String(100), nullable = False)
    age = db.Column(db.Integer, nullable = True)

    role = db.Column(db.String(20), nullable = False)
    is_active_account = db.Column(db.Boolean, default=True)






# function to add new user into db
def insert_user(username,password,email, age, role):
    new_user = User(username = username, password = password, email = email, age = age, role = role)
    db.session.add(new_user)
    db.session.commit()
# now data is permanently saved


# checking if user already exists in database
def check_user(username,password):
    user = User.query.filter_by(username = username).first()

    if user and user.password == password:
        return user
    return None


class Appointments(db.Model):
    id = db.Column(db.Integer, primary_key= True)

    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    date = db.Column(db.String(20))
    time = db.Column(db.String(20))

    status = db.Column(db.String(20), default = "pending")



class Report(db.Model):
    id =  db.Column(db.Integer, primary_key = True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    filename = db.Column(db.String(200))
    filepath = db.Column(db.String(300))

    uploaded_at = db.Column(db.DateTime, default=db.func.now())

    