from flask import Flask, redirect, url_for, flash, session
from models import Report, db, check_user, User, Appointments

from flask_login import current_user, LoginManager
from flask_login import login_user

from flask import render_template, request
from flask_sqlalchemy import SQLAlchemy
import re
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename


import os

app = Flask(__name__)

app.secret_key = "mysecretkey123"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'shiwamsudhanshu1234@gmail.com'
app.config['MAIL_PASSWORD'] = 'abcdefghijk'
mail = Mail(app)


app.config['UPLOAD_FOLDER'] = 'static/reports'



login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




@app.route('/', methods=['GET','POST'])
def home():
    message = ""
    if request.method == 'POST':
        username = request.form['username']
        password  = request.form['password']

        if not username.strip() or not password.strip():
            flash("All fields are required")
            return redirect(url_for('home'))        

        user = check_user(username, password)

        if user:
            login_user(user)

            if user.role == 'admin':
                flash("Login Successful")
                return redirect(url_for('admin_dashboard'))
    
            elif user.role == 'patient': 
                flash("Login Successful")
                return redirect(url_for('patient_dashboard'))
        
            elif user.role == "doctor":
                flash("Login Successful")
                return redirect(url_for('doctor_dashboard'))
        
            else:
                flash("Invalid user", "error")
                return redirect(url_for('home'))

        else:
            flash("Invalid credentials", "error")
            return redirect(url_for('home'))

    return render_template('login.html', message=message)




@app.route('/register_patient', methods = ['GET','POST'])
def register_patient_route():
    message = ""
    if request.method == 'POST':
        username = request.form['username']
        password  = request.form['password']
        email = request.form['email']
        age = request.form['age']

        if not username or not password or not email or not age:
            flash("All fields are required")
            return redirect(url_for('register_patient_route'))
        
        if "@" not in email:
            flash("email must contain @")
            return redirect(url_for('register_patient_route'))

        if not re.match("^[a-zA-Z0-9_]+$", username):
            flash("Username must contain only letters, numbers or underscore")
            return redirect(url_for('register_patient_route'))

        if len(password) < 6:
            flash("Password too short")
            return redirect(url_for('register_patient_route'))
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            flash("password must contain one special character")
            return redirect(url_for('register_patient_route'))

        existing =  User.query.filter_by(email = email).first()

        if existing:
            flash("Email already exists")
            return redirect(url_for('home'))

        else:
            new_user = User(username = username,password = password, email = email,age = age, role = "patient")
            db.session.add(new_user)
            db.session.commit()

            # send email
            msg = Message (subject = "Registration Successful",
                          sender = app.config['MAIL_USERNAME'],
                          recipients = [email]
            )
            
            msg.body  = f'''Hello {username},
            
We are pleased to inform you that your account has been successfully created on the HMS Portal.

You can now log in using your registered credentials to access the system. Through your account, you will be able to manage appointments, view important updates, and use the services provided on the platform.

If you face any issues while logging in or using the portal, please feel free to contact the support team.

Welcome to the HMS Portal!'''
            mail.send(msg)

            flash("Patient_registered successfully")
            return redirect(url_for('home'))

    return render_template('patient_register.html')




@app.route('/patient_dashboard')
def patient_dashboard():
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')

    if not current_user.is_authenticated:
        return redirect(url_for('home'))

    appointments = db.session.query(Appointments, User)\
    .join(User, Appointments.doctor_id == User.id)\
    .filter(Appointments.patient_id == current_user.id)\
    .all()
    
    appointment_count = len(appointments)

    reports = Report.query.filter_by(patient_id = current_user.id).all()
    report_count = len(reports)
    

    upcoming_count = Appointments.query.filter(
        Appointments.patient_id == current_user.id,
        Appointments.status == "confirmed",  
        Appointments.date >= today
    ).count()

    all_appts = Appointments.query.filter_by(patient_id=current_user.id).all()
    for a in all_appts:
        print(repr(a.status), repr(a.date), repr(today))


    return render_template(
        'patient_dashboard.html',
        user=current_user,
        appointments=appointments,
        appointment_count=appointment_count,
        report_count=report_count,
        upcoming_count = upcoming_count
    )





@app.route('/doctor_dashboard')
def doctor_dashboard():

    if not current_user.is_authenticated:
        return redirect(url_for('home'))
    appointments = db.session.query(Appointments, User)\
    .join(User, Appointments.patient_id == User.id)\
    .filter(Appointments.doctor_id == current_user.id)\
    .all()
    return render_template('doctor_dashboard.html',user = current_user, appointments = appointments)

# //doctor upload route

@app.route('/upload_report', methods=['POST', 'GET'])
def upload_report():
    if not current_user.is_authenticated:
        return redirect(url_for('home'))

    patient_id = request.form.get('patient_id')
    file = request.files.get('file')

    if file:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        report = Report(
            doctor_id=current_user.id,
            patient_id=patient_id,
            filename=filename,
            filepath=path
        )

        db.session.add(report)
        db.session.commit()

        flash("Report uploaded successfully")

    return redirect(url_for('doctor_dashboard'))




# view report

@app.route('/my_reports')
def my_reports():
    reports = Report.query.filter_by(patient_id=current_user.id).all()
    if current_user.role == "patient":
        return render_template('reports.html', reports=reports)
    else:
        return render_template("admin_reports.html",reports = reports)

    


from sqlalchemy.orm import aliased

@app.route('/admin/appointments')
def admin_appointments():
    if current_user.role != "admin":
        return redirect(url_for('login'))

    Patient = aliased(User)
    Doctor = aliased(User)

    appointments = db.session.query(Appointments, Patient, Doctor)\
        .join(Patient, Appointments.patient_id == Patient.id)\
        .join(Doctor, Appointments.doctor_id == Doctor.id)\
        .all()

    return render_template("appointments.html", appointments=appointments)





from flask import request, render_template, redirect, url_for
from flask_login import current_user
from sqlalchemy import or_

@app.route('/admin_dashboard')
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for('login'))

    search_query = request.args.get('search')

    users = None
    if search_query:
        users = User.query.filter(
            User.username.ilike(f"%{search_query}%")
        ).all()

    total_users = User.query.count()
    total_doctors = User.query.filter_by(role="doctor").count()
    total_appointments = Appointments.query.count()
    pending_appointments = Appointments.query.filter_by(status="pending").count()

    return render_template(
        'admin_dashboard.html',
        user=current_user,
        total_users=total_users,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        pending_appointments=pending_appointments,
        users=users
    )




@app.route('/notification')
def notification():
    return render_template('notification.html')





@app.route('/back')
def back():
    return redirect(url_for('home'))





@app.route('/logo')
def logo():
    return render_template('logo.html')




@app.route('/about_us')
def about():
    return render_template('about.html')




@app.route('/services')
def services():
    return render_template('services.html')





@app.route('/help')
def help():
    return render_template('help.html')





@app.route('/logout')
def logout():
    flash("Logged out successfully")
    return redirect(url_for('home'))




@app.route('/homepage')
def homepage():
    return redirect(url_for('home'))




@app.route('/book',methods = ['GET','POST'])
def book_appointment():
    if request.method == 'POST':
        doctor_id = int(request.form['doctor'])
        date = request.form['date']
        time = request.form['time']


# Checking if slot already exists
        existing = Appointments.query.filter_by(doctor_id = doctor_id, date = date, time = time).first()
        if existing:
            flash("Slot already booked, choose another slot")
            return redirect(url_for('book_appointment'))
    

        new_appt = Appointments(patient_id = current_user.id, doctor_id = doctor_id, date = date, time = time, status = "pending")
        db.session.add(new_appt)
        db.session.commit()

        flash("Appointment Booked Successfully")
        return redirect(url_for('patient_dashboard'))
    
    doctors = User.query.filter_by(role="doctor").all()

    doctor_data = [
        {
            "id": d.id,
            "username": d.username
        }
        for d in doctors
    ]
    
    return render_template('book.html', doctors=doctor_data)





@app.route('/update_status/<int:appt_id>', methods=['POST'])
def update_status(appt_id):
    appt = Appointments.query.filter_by(
    id=appt_id,
    doctor_id=current_user.id
    ).first()

    if not appt:
        flash("unauthorised access")
        return redirect(url_for('doctor_dashboard'))

    appt.status = request.form['status'].strip().lower()
    db.session.commit()

    flash("Status updated")
    return redirect(url_for('doctor_dashboard'))


# when patients login, show their appointments on dashboard






@app.route('/register_doctor', methods = ['GET','POST'])
def register_doctor_route():
    message = ""
    if request.method == 'POST':
        username = request.form['username']
        password  = request.form['password']
        email = request.form['email']

        if not username or not password or not email:
            flash("All fields are required")
            return redirect(url_for('register_doctor_route'))
        
        if "@" not in email:
            flash("email must contain @")
            return redirect(url_for('register_patient_route'))

        if not re.match("^[a-zA-Z0-9_]+$", username):
            flash("Username must contain only letters, numbers or underscore")
            return redirect(url_for('register_patient_route'))

        if not re.match("^[a-zA-Z0-9_]+$", username):
            flash("Username must contain only letters, numbers or underscore")
            return redirect(url_for('register_doctor_route'))

        if len(password) < 6:
            flash("Password too short")
            return redirect(url_for('register_doctor_route'))
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            flash("password must contain one special character")
            return redirect(url_for('register_patient_route'))

        existing =  User.query.filter_by(email = email).first()

        if existing:
            flash("Email already exists")
            return redirect(url_for('home'))

        else:
            new_user = User(username = username,password = password,email = email,age =None, role = "doctor")
            db.session.add(new_user)
            db.session.commit()

            # send email
            msg = Message (subject = "Registration Successful",
                          sender = app.config['MAIL_USERNAME'],
                          recipients = [email]
            )
            
            msg.body  = f'''Hello Dr. {username},

We are pleased to inform you that your registration on the Hospital Management System has been successfully completed as a Doctor.
Your account has been created, and you can now log in using your registered email address.

If you did not initiate this registration, please contact the hospital administration immediately.

Thank you for joining our system.
Regards,
Hospital Management System Team'''
            mail.send(msg)

            flash("Doctor_registered successfully")
            return redirect(url_for('home'))

    return render_template('doctor_register.html')








# telling SQLAlchemy:
# Use SQLite and store data in a file named database.db

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)
# It connects your database (SQLAlchemy) to your Flask app


# Create all tables in the database based on my models
with app.app_context():
    db.create_all()
    print("table created")\
    
# Start app context → connect ORM → write this row → save permanently

with app.app_context():
    existing_admin = User.query.filter_by(username = "Hospital").first()

    if not existing_admin:
        admin = User(username = "Hospital", password = "123", email = "abc@123", age = 25, role = "admin")
        db.session.add(admin)
        db.session.commit()

    








if __name__ == '__main__':
    app.run(debug=True)



