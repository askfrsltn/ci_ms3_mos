# import libraries and functions from packages
import os
from flask import (Flask, flash, render_template, 
    redirect, request, session,url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
# import datetie method: from datetime import datetime


# connect env.py if it was created
if os.path.exists("env.py"):
    import env


# create flask app and define route decorator
app = Flask(__name__)


# define app configuration:
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

# set up moongo variable for mongo connection:
mongo = PyMongo(app)


@app.route("/")
# create route decorator for home page
@app.route("/home")
def home():
    users = mongo.db.users.find()
    return render_template("home.html", users=users)

# create route decorator for login page
@app.route("/login", methods=["GET", "POST"])
def login():
    #  checks if the data is posted, ans assign a user_name to a variable
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"user_name": request.form.get("user_name").lower()})
        # checks if user_name exists - !!! I want to use email - find the way
        # later
        if existing_user:
            if check_password_hash(
                existing_user["user_password"], request.form.get
                    ("user_password")):
                session["user"] = request.form.get("user_name").lower()
                flash("Welcome, {}".format(request.form.get("user_name")))
                return redirect(url_for('user_dashboard', 
                    username=session["user"]))
            # invalid password message
            else:
                flash("Incorrect login details, please try again")
                return redirect(url_for('login'))
        # email doesn't exist
        else:
            flash("Incorrect login details, please try again")
            return redirect(url_for('login'))
    return render_template("login.html")


# create route decorator for register page
@app.route("/register", methods=["GET", "POST"])
def register():
    # registration functionality
    if request.method == "POST":
        
        # checks database if the user_email already registered
        existing_email = mongo.db.users.find_one({"user_email": request.form.get("user_email").lower()})
        existing_user = mongo.db.users.find_one({"user_name": request.form.
            get("user_name").lower()})
        
        # checks database if the user_email already registered
        if existing_email:
            flash("email already exists, try again")
            return redirect(url_for("register"))
        
        # checks database if the user_name already registered
        if existing_user:
            flash("user name already exists, try again")
            return redirect(url_for("register"))
            
        # if no user we create new user
        register = {
            "user_name": request.form.get("user_name").lower(),
            "user_email": request.form.get("user_email").lower(),
            "user_password": generate_password_hash(request.form.get
                ("user_password")),
        }

        # insert new user into Mongo Db database
        mongo.db.users.insert_one(register)

        # create session for newly registered user
        session["user"] = request.form.get("user_name").lower()
        flash("Registration successfull!")
        return redirect(url_for('user_dashboard', username=session["user"]))
    return render_template("register.html")


# create route decorator for user dashboard page
@app.route("/user_dashboard/<username>", methods=["POST", "GET"])
def user_dashboard(username):
    # create username variable
    username = mongo.db.users.find_one(
        {"user_name": session["user"]})["user_name"]
    # create actions variable for the loop on user_dashboard
    actions = mongo.db.actions.find()
    
    # create completionstatus variable for the loop on user_dashboard selected component
    completionstatus = mongo.db.completionstatus.find()
    

    # security function to celan cookies and passing actions into the loop
    if session["user"]: 
        return render_template("user_dashboard.html", 
            username=username,
            actions=actions,
            completionstatus=completionstatus)
    return redirect(url_for('login'))

@app.route("/logout")
def logout():
    flash("you have logged out")
    # remove user from session cookies
    session.clear()
    return redirect("login")

# function to add actions
@app.route("/add_action", methods=["POST","GET"])
def add_action():
    if request.method=="POST":
        # create a variable for new action
        task={
            "action_refno": request.form.get("action_refno"),
            "action_name": request.form.get("action_name"),
            "action_due": request.form.get("action_due"),
            "action_accountable": request.form.get("action_accountable"),
            "action_dept": request.form.get("action_dept"),
            "action_logdate": request.form.get("action_logdate"),
            "action_meeting": request.form.get("action_meeting"),
            "action_workstream": request.form.get("action_workstream")
        }
        
        # insert new action inside actions collection
        mongo.db.actions.insert_one(task)

        # show the message that the operation was done successfully
        flash("New action was successfully added")
        return redirect(url_for('add_action'))

    # action counter - not perfect needds to be ahcnge later
    action_dept =str(mongo.db.actions.find().count()+1)
    
    # variables for selection dropdown lists on add_action template
    users=mongo.db.users.find().sort("user_name", 1)
    meetings=mongo.db.meetings.find().sort("meeting_name", 1)
    depts =mongo.db.depts.find().sort("dept_name", 1)
    workstreams=mongo.db.workstreams.find().sort("workstream_name", 1)
    return render_template("add_action.html", 
        users=users,
        meetings=meetings,
        depts=depts, 
        workstreams=workstreams, action_dept=action_dept)

# setup router and function
@app.route("/admin_setup")
def setup():
    
    # collect all the users
    users = mongo.db.users.find()
    
    # collect all the status items
    completionstatus = mongo.db.completionstatus.find()

    # collect all the departments
    depts = mongo.db.depts.find()

    # collect all the workstreams
    workstreams = mongo.db.workstreams.find()

    # collect all the meetings
    meetings = mongo.db.meetings.find()

    # collect all the kpis
    kpi = mongo.db.kpi.find()

    # collect all the kpis
    kpistatuss = mongo.db.kpistatuss.find()
    
    return render_template("setup.html", users=users, 
        completionstatus=completionstatus,
        depts=depts,
        workstreams=workstreams,
        meetings=meetings,
        kpi=kpi,
        kpistatuss=kpistatuss)

# add user route decorator and add_user function
@app.route("/add_user", methods=["POST", "GET"])
def add_user():
    # add user functionality
    if request.method == "POST":
        # checks database if the user_email already added
        existing_email = mongo.db.users.find_one({"user_email": request.form.get("user_email")})

        existing_user = mongo.db.users.find_one({"user_name": request.form.
            get("user_name")})
        
        # checks database if the user_email already registered
        if existing_email:
            flash("email already exists, try again")
            return redirect(url_for("add_user"))
        
        # checks database if the user_name already registered
        if existing_user:
            flash("user name already exists, try again")
            return redirect(url_for("add_user"))
            
        # if no user we create new user
        add_user = {
            "user_name": request.form.get("user_name").lower(),
            "user_email": request.form.get("user_email").lower(),
            "user_password": generate_password_hash(request.form.get
                ("user_password")),
        }

        # insert new user into Mongo Db database
        mongo.db.users.insert_one(add_user)
        flash("New User added")
        return redirect(url_for('setup'))

    return render_template("add_user.html")

# create edit_user function
@app.route("/edit_user/<user_id>", methods=["POST", "GET"])
def edit_user(user_id):
    # create user variable to prefill user input values in the form
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    # update changed user data into mongodb
    if request.method == "POST":
        edituser = {
                "user_name": request.form.get("user_name").lower(),
                "user_email": request.form.get("user_email").lower(),
                "user_password": generate_password_hash(request.form.
                    get("user_password")),
            }
        # insert new user into Mongo Db database
        mongo.db.users.update({"_id": ObjectId(user_id)}, edituser)
        flash("User update successfull!")
        return redirect(url_for('setup'))
    return render_template("edit_user.html", user=user)

# user delete function for setup template
@app.route("/delete_user/<user_id>")
def delete_user(user_id):
    mongo.db.users.remove({"_id": ObjectId(user_id)})
    flash("User was deleted")
    return redirect(url_for('setup'))

# action completion status delete function for setup template
@app.route("/delete_actionstatus/<completionstatus_id>")
def delete_completionstatus(completionstatus_id):
    mongo.db.completionstatus.remove({"_id": ObjectId(completionstatus_id)})
    flash("Action status was deleted")
    return redirect(url_for('setup'))


# department delete function for setup template
@app.route("/delete_department/<dept_id>")
def delete_department(dept_id):
    mongo.db.depts.remove({"_id": ObjectId(dept_id)})
    flash("Department was deleted")
    return redirect(url_for('setup'))


# workstream delete function for setup template
@app.route("/delete_workstream/<workstream_id>")
def delete_workstream(workstream_id):
    mongo.db.workstreams.remove({"_id": ObjectId(workstream_id)})
    flash("Workstream was deleted")
    return redirect(url_for('setup'))


# meeting delete function for setup template
@app.route("/delete_meeting/<meeting_id>")
def delete_meeting(meeting_id):
    mongo.db.meetings.remove({"_id": ObjectId(meeting_id)})
    flash("Meeting was deleted")
    return redirect(url_for('setup'))


# KPI delete function for setup template
@app.route("/delete_kpi/<kpi_id>")
def delete_kpi(kpi_id):
    mongo.db.kpi.remove({"_id": ObjectId(kpi_id)})
    flash("The KPI was deleted")
    return redirect(url_for('setup'))

# KPI status delete function for setup template
@app.route("/delete_kpistatus/<kpistatus_id>")
def delete_kpistatus(kpistatus_id):
    mongo.db.kpistatuss.remove({"_id": ObjectId(kpistatus_id)})
    flash("The KPI Status was deleted")
    return redirect(url_for('setup'))

# admin kpi inputs page
@app.route("/kpi_input")
def kpi_input():
    # create kpis variable for the select loop on kpi_input
    kpi = mongo.db.kpi.find()
    return render_template("kpi_input.html",kpi=kpi)

# admin kpi inputs page
@app.route("/add_kpi", methods=["POST","GET"])
def add_kpi():
    owners = mongo.db.users.find()
    # add kpi into mongodb
    if request.method=="POST":
        kpi={
            "kpi_name": request.form.get("kpi_name"),
            "kpi_shortname": request.form.get("kpi_shortname"),
            "kpi_uom": request.form.get("kpi_uom"),
            "kpi_owner": request.form.get("kpi_owner").lower(),
            "kpi_description": request.form.get("kpi_description")
        }

        mongo.db.kpi.insert(kpi)

        flash("KPI was successfully added!")
        return redirect(url_for('setup'))
    return render_template("add_kpi.html", owners=owners)


# tell where and how to return an app, DO NOT FORGET TO change  
# debug=False  putting in production.
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=os.environ.get("PORT"), debug=True)
