# import libraries and functions from packages
import os
from flask import (Flask, flash, render_template, 
    redirect, request, session,url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
# import datetie method: from datetime import datetime
from datetime import datetime

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
    # create list of dictionaries from kpiinputs collection in mongodb
    kpiinputs = list(mongo.db.kpiinputs.find())
    
    # create list of input_kpiname values from kpiinputs list - thanks to stackoverflow help from Ismail Badawi: https://stackoverflow.com/questions/7271482/getting-a-list-of-values-from-a-list-of-dicts 
    kpinames = [name['input_kpiname'] for name in kpiinputs]
    
    # use set method to create unique list of name
    unames = set(kpinames)
    
    return render_template("home.html", kpiinputs=kpiinputs, kpinames=kpinames, unames=unames)


# create route decorator for login page
@app.route("/login", methods=["GET", "POST"])
def login():
    #  checks if the data is posted, ans assign a user_name to a variable
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"user_name": request.form.get("user_name").lower()})
        # checks if user_name exists - !!! I want to use email - find the way
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
    # create username variable for user_dashboard template entrance
    username = mongo.db.users.find_one(
        {"user_name": session["user"]})["user_name"]
    
    # create completionstatus variable for the loop on user_dashboard selected component
    completionstatus = mongo.db.completionstatus.find()
    
    # define variable for automatic filter
    user=session["user"]
    
    # define variable for filtering selection
    action_status=request.form.get('action_status')

    # variable for action status selection after it has been selected by filter
    actionstatusselection =  action_status
    
    # define variables for kpis and actions loop -it should be filtered to user as kpi_owner, and if it is admin it should not filter, this nested conditions should also be used for filter section of actions
    if user == "admin":
        
        # variable kpis for KPIs section when user is logged in as admin
        kpis = mongo.db.kpi.find()
        
        # variable kpis for KPIs section when user is logged in as admin
        actions = mongo.db.actions.find() 
        
        # action status filtering condition - activated after the action status is selected
        if request.method == "POST":
            actions = list(mongo.db.actions.find({"action_status":action_status}))
    
    # this part of the function is activated when the user logged in as non-admin
    else:
        
        # create kpis for KPI summary section if the user is non-admin
        kpis = list(mongo.db.kpi.find({"$text":{"$search":user}}))
        # create actions variable for non-admin
        actions = list(mongo.db.actions.find({"action_accountable": user}))
        # create actions variable for non-admin when filter is activated
        if request.method == "POST":
            # this filter has 2 filters - user and action status that is selected from filter section
            actions = list(mongo.db.actions.find({"action_accountable": user, "action_status":action_status}))   

    # pass all the variables into the loop
    if session["user"]: 
        return render_template("user_dashboard.html", 
            username=username,
            actions=actions,
            completionstatus=completionstatus,
            kpis=kpis,
            user=user,
            action_status=action_status,
            actionstatusselection=actionstatusselection)
    return redirect(url_for('login'), username=user)


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
            "action_workstream": request.form.get("action_workstream"),
            "action_status": request.form.get("action_status")
        }
        
        # insert new action inside actions collection
        mongo.db.actions.insert_one(task)
        
        # show the message that the operation was done successfully
        flash("New action was successfully added")
        return redirect(url_for('user_dashboard', username=session['user']))

    # action counter - not perfect needds to be ahcnge later
    action_dept =mongo.db.actions.find().count()+1
    
    # variables for selection dropdown lists on add_action template
    users = mongo.db.users.find().sort("user_name", 1)
    meetings = mongo.db.meetings.find().sort("meeting_name", 1)
    depts = mongo.db.depts.find().sort("dept_name", 1)
    workstreams = mongo.db.workstreams.find().sort("workstream_name", 1)
    completionstatus = mongo.db.completionstatus.find()

    # return render template using variables for dropdowns
    return render_template("add_action.html", 
        users=users,
        meetings=meetings,
        depts=depts, 
        workstreams=workstreams, 
        action_dept=action_dept,
        completionstatus = completionstatus)

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


# create edit_department function
@app.route("/edit_department/<dept_id>", methods=["POST", "GET"])
def edit_department(dept_id):
    # create dept variable to prefill user input values in the form
    dept = mongo.db.depts.find_one({"_id": ObjectId(dept_id)})

    # update changed department data into mongodb
    if request.method == "POST":
        editdept = {
                "dept_name": request.form.get("dept_name"),
                "dept_shortname": request.form.get("dept_shortname")
            }
    
    # insert new department into Mongo Db database
        mongo.db.depts.update({"_id": ObjectId(dept_id)}, editdept)
        flash("Deparment update successfull!")
        return redirect(url_for('setup'))
    return render_template("edit_department.html", dept=dept)


# create edit_workstream function
@app.route("/edit_workstream/<workstream_id>", methods=["POST", "GET"])
def edit_workstream(workstream_id):
    # create workstream variable to prefill workstream input values in the form
    workstream = mongo.db.workstreams.find_one({"_id": ObjectId(workstream_id)})

    # update changed workstream data into mongodb
    if request.method == "POST":
        editworkstream = {
                "workstream_name": request.form.get("workstream_name"),
                "workstream_shortname": request.form.get("workstream_shortname")
            }
    
    # insert new department into Mongo Db database
        mongo.db.workstreams.update({"_id": ObjectId(workstream_id)}, editworkstream)
        flash("Workstream update successfull!")
        return redirect(url_for('setup'))
    return render_template("edit_workstream.html", workstream=workstream)


# create edit_meeting function
@app.route("/edit_meeting/<meeting_id>", methods=["POST", "GET"])
def edit_meeting(meeting_id):
    # create meeting variable to prefill meeting input values in the form
    meeting = mongo.db.meetings.find_one({"_id": ObjectId(meeting_id)})

    # update changed meeting data into mongodb
    if request.method == "POST":
        editmeeting = {
                "meeting_name": request.form.get("meeting_name"),
                "meeting_shortname": request.form.get("meeting_shortname")
            }
    
    # insert new meeting into Mongo Db database
        mongo.db.meetings.update({"_id": ObjectId(meeting_id)}, editmeeting)
        flash("Meeting update successfull!")
        return redirect(url_for('setup'))
    return render_template("edit_meeting.html", meeting=meeting)


# create edit_kpi function
@app.route("/edit_kpi/<kpi_id>", methods=["POST", "GET"])
def edit_kpi(kpi_id):
    # create kpi variable to prefill kpi input values in the form
    kpi = mongo.db.kpi.find_one({"_id": ObjectId(kpi_id)})

    # update changed kpi data into mongodb
    if request.method == "POST":
        editkpi = {
                "kpi_name": request.form.get("kpi_name"),
                "kpi_shortname": request.form.get("kpi_shortname"),
                "kpi_uom": request.form.get("kpi_uom"),
                "kpi_description": request.form.get("kpi_description"),
                "kpi_owner": request.form.get("kpi_owner")
            }
        # insert new kpi into Mongo Db database
        mongo.db.kpi.update({"_id": ObjectId(kpi_id)}, editkpi)
        flash("KPI update successfull!")
        return redirect(url_for('setup'))
    # define users variable for  KPI owner seectin
    users=mongo.db.users.find().sort("user_name", 1)
    return render_template("edit_kpi.html", kpi=kpi, users=users)


# create edit_kpistatus function
@app.route("/edit_kpistatus/<kpistatus_id>", methods=["POST", "GET"])
def edit_kpistatus(kpistatus_id):
    # create kpistatus variable to prefill kpistatus input values in the form
    kpistatus = mongo.db.kpistatuss.find_one({"_id": ObjectId(kpistatus_id)})

    # update changed kpistatus data into mongodb
    if request.method == "POST":
        editkpistatus = {
                "kpistatus_name": request.form.get("kpistatus_name"),
                "kpistatus_color": request.form.get("kpistatus_color")
            }
    
    # insert new kpistatus into Mongo Db database
        mongo.db.kpistatuss.update({"_id": ObjectId(kpistatus_id)}, editkpistatus)
        flash("KPI Status update successfull!")
        return redirect(url_for('setup'))
    return render_template("edit_kpistatus.html", kpistatus=kpistatus)

# user delete function for setup template
@app.route("/delete_user/<user_id>")
def delete_user(user_id):
    mongo.db.users.remove({"_id": ObjectId(user_id)})
    flash("User was deleted")
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

# setp admin kpi inputs page
@app.route("/add_kpi", methods=["POST","GET"])
def add_kpi():
    # add select dropdown list
    owners = mongo.db.users.find()

    # add kpi into mongodb
    if request.method=="POST":
        kpi={
            "kpi_name": request.form.get("kpi_name"),
            "kpi_shortname": request.form.get("kpi_shortname"),
            "kpi_uom": request.form.get("kpi_uom"),
            "kpi_owner": request.form.get("kpi_owner").lower(),
            "kpi_description": request.form.get("kpi_description"),
            "kpi_lastlstatus": "grey"
        }
        # insert new document into mongodb collection kpi
        mongo.db.kpi.insert(kpi)
        # print completion on th escreen
        flash("KPI was successfully added!")
        # redirect to setup
        return redirect(url_for('setup'))
    return render_template("add_kpi.html", owners=owners)


# create setup function for adding department
@app.route("/add_department",methods=["POST","GET"])
def add_department():
    if request.method == "POST":
        
        # create a variable for new department
        new_department = {
            "dept_name": request.form.get("dept_name"),
            "dept_shortname": request.form.get("dept_shortname")
        }

        # insert new add_department inside status collection
        mongo.db.depts.insert_one(new_department)

        # show the message that the operation was done successfully
        flash("New department was successfully added")
        return redirect(url_for('setup'))
    return render_template("add_department.html")


# create setup function for adding worksream
@app.route("/add_workstream", methods=["POST", "GET"])
def add_workstream():
    if request.method == "POST":
        
        # create a variable for new workstream
        new_workstream = {
            "workstream_name": request.form.get("workstream_name"),
            "workstream_shortname": request.form.get("workstream_shortname")
        }

        # insert new add_department inside status collection
        mongo.db.workstreams.insert_one(new_workstream)

        # show the message that the operation was done successfully
        flash("New workstream was successfully added")
        return redirect(url_for('setup'))
    return render_template("add_workstream.html")


# create setup function to add new meeting
@app.route("/add_meeting", methods=["POST", "GET"])
def add_meeting():
    if request.method == "POST":
        
        # create a variable for new meeting
        new_meeting = {
            "meeting_name": request.form.get("meeting_name"),
            "meeting_shortname": request.form.get("meeting_shortname")
        }

        # insert new add_department inside status collection
        mongo.db.meetings.insert_one(new_meeting)

        # show the message that the operation was done successfully
        flash("New meeting was successfully added")
        return redirect(url_for('setup'))
    return render_template("add_meeting.html")
    

# create setup function to add new kpi status
@app.route("/add_kpistatus", methods=["POST", "GET"])
def add_kpistatus():
    if request.method == "POST":
        
        # create a variable for new meeting
        new_kpistatus = {
            "kpistatus_name": request.form.get("kpistatus_name"),
            "kpistatus_color": request.form.get("kpistatus_color")
        }

        # insert new add_department inside status collection
        mongo.db.kpistatuss.insert_one(new_kpistatus)

        # show the message that the operation was done successfully
        flash("New KPI Status was successfully added")
        return redirect(url_for('setup'))
    return render_template("add_kpistatus.html")


# kpi inputs page - add input page
@app.route("/kpi_input")
def kpi_input():
    # create kpi input variable for the select loop on kpi_input
    kpi = mongo.db.kpi.find()

    # create kpiinputs variable for table body values
    kpiintputs = mongo.db.kpiinputs.find()

    return render_template("kpi_input.html", kpi=kpi, kpiintputs=kpiintputs)


# filter function for kpi inputs page
@app.route("/filter", methods = ["GET" , "POST"])
def filter():
    #  enable kpi for loop after filtering  
    kpi = mongo.db.kpi.find()
    
    # make second form work after the filtering
    input_kpiname = request.form.get("input_kpiname")
    
    # create variable for automatic KPI definition on the kpi input line 
    kpiselection = input_kpiname
    
    # create inputs variable for KPI inputs list based on search request
    kpiintputs = list(mongo.db.kpiinputs.find({"$text": {"$search":input_kpiname}}))
    
    # create inputs variable for KPI inputs list based on search request
    return render_template("kpi_input.html", kpiintputs=kpiintputs, 
        kpi=kpi, kpiselection=kpiselection)

# function to add kpiinput
@app.route("/add_kpiinput", methods=["GET","POST"])
def add_kpiinput():
    # if request method is post condition
    if request.method == "POST":
        
        # create a variable for kpi input
        kpiinput={
            "input_kpiowner": request.form.get("input_kpiowner"),
            "input_kpiname": request.form.get("input_kpiname"),
            "input_logdate": request.form.get("input_logdate"),
            "input_weeknumber": request.form.get("input_weeknumber"),
            "input_uom": request.form.get("input_uom"),
            "input_bsl": request.form.get("input_bsl"),
            "input_tgt": request.form.get("input_tgt"),
            "input_act": request.form.get("input_act"),
            "input_status": request.form.get("input_status")
        }
        # insert new kpi input inside kpiinputs collection
        mongo.db.kpiinputs.insert_one(kpiinput)
        
        # based on kpiinput define a variable to update  kpi collection fields
        latestinput ={
            "kpi_lastlogdate": request.form.get("input_logdate"),
            "kpi_lastbsl": request.form.get("input_bsl"),
            "kpi_lasttgt": request.form.get("input_tgt"),
            "kpi_lastact": request.form.get("input_act"),
            "kpi_laststatus": request.form.get("input_status")
        }
        
        # update kpi collection for specific fields following MongoDb documentation -https://docs.mongodb.com/manual/reference/operator/update/set/. Problem: the code {$set:latestinput} did not work Johann from student support helped me - i had to correct the code and add "" - {"$set":latestinput}. 
        mongo.db.kpi.update({"kpi_name": request.form.get("input_kpiname")},{"$set":latestinput})
        
        # show the message that the operation was done successfully
        flash("KPI Input was successfully added")
        
        # redirect to home page
        return redirect(url_for('kpi_input')) 
    return render_template("kpi_input.html", kpiintputs=kpiintputs)


# create edit_kpi input function
@app.route("/edit_kpiinput/<kpiinput_id>", methods=["POST", "GET"])
def edit_kpiinput(kpiinput_id):
    
    # create kpiinput variable to prefill kpiinput input values in the form
    input = mongo.db.kpiinputs.find_one({"_id": ObjectId(kpiinput_id)})

    # variable for kpiowners select
    owners = mongo.db.users.find()

    # variable for KPIs list select
    kpis = mongo.db.kpi.find()

    # user variable
    user = session["user"]

    # update changed kpiinput data into mongodb
    if request.method == "POST":
        editkpiinput = {
                "input_kpiname": request.form.get("input_kpiname"),
                "input_logdate": request.form.get("input_logdate"),
                "input_weeknumber": request.form.get("input_weeknumber"),
                "input_uom": request.form.get("input_uom"),
                "input_bsl": request.form.get("input_bsl"),
                "input_tgt": request.form.get("input_tgt"),
                "input_act": request.form.get("input_act"),
                "input_kpiowner": user,
                "input_status": request.form.get("input_status")
            }
            
        # insert new kpiinput into Mongo Db database
        mongo.db.kpiinputs.update({"_id": ObjectId(kpiinput_id)}, editkpiinput)
        
        # based on kpiinput define a variable to update  kpi collection fields
        latestinput ={
            "kpi_lastlogdate": request.form.get("input_logdate"),
            "kpi_lastbsl": request.form.get("input_bsl"),
            "kpi_lasttgt": request.form.get("input_tgt"),
            "kpi_lastact": request.form.get("input_act"),
            "kpi_laststatus": request.form.get("input_status")
        }
        
        # update kpi collection:
        mongo.db.kpi.update({"kpi_name": request.form.get("input_kpiname")},{"$set":latestinput})
        
        flash("KPI input update successfull!")
        
        return redirect(url_for('kpi_input'))
    return render_template("edit_kpiinput.html",  input=input, 
        user=user, owners=owners, kpis=kpis)

# create edit_actionstatus input function
@app.route("/edit_actionstatus/<action_id>", methods=["POST", "GET"])
def edit_actionstatus(action_id):
    
    # find the right action for status update
    action = mongo.db.actions.find_one({"_id": ObjectId(action_id)})
    
    # use completionsattus collection for status dropdawn on select element
    completionstatus = mongo.db.completionstatus.find()
    
    # submit form update
    if request.method=="POST":
        # create variable for action update
        editactionstatus = {
                "action_status": request.form.get("action_status")
            }
        
        # update an action with actionstatus in collection - address only specific field that was changed
        mongo.db.actions.update({"_id": ObjectId(action_id)},{"$set":editactionstatus})
        
        # inform about successfull completion
        flash("Action status was updated")
        
        return redirect(url_for('user_dashboard', username=session["user"]))
    return render_template("edit_actionstatus.html",  action=action, completionstatus=completionstatus)

# create edit_action function
@app.route("/edit_action/<action_id>", methods=["POST", "GET"])
def edit_action(action_id):
    
    # find the right action for update
    action = mongo.db.actions.find_one({"_id": ObjectId(action_id)})
    
    # use completionsattus collection for status dropdawn on select element
    completionstatus = mongo.db.completionstatus.find()
    
    # use completionsattus collection for status dropdawn on select element
    users = mongo.db.users.find()
    
    # submit form update
    if request.method=="POST":
        # create variable for action update
        editaction = {
                "action_refno": request.form.get("action_refno"),
                "action_name": request.form.get("action_name"),
                "action_due": request.form.get("action_due"),
                "action_accountable": request.form.get("action_accountable"),
                "action_status": request.form.get("action_status")
            }
        
        # update an action with actionstatus in collection - address only specific field that was changed
        mongo.db.actions.update({"_id": ObjectId(action_id)},{"$set":editaction})
        
        # inform about successfull completion
        flash("Action was updated")
        
        return redirect(url_for('user_dashboard', username=session["user"]))
    return render_template("edit_action.html",  action=action, completionstatus=completionstatus, users=users)


# tell where and how to return an app, DO NOT FORGET TO change debug=False  putting in production.
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=os.environ.get("PORT"), debug=True)
