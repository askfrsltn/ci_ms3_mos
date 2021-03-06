"""import app packages"""
import os
from datetime import date
from flask import (
    Flask,
    flash,
    render_template,
    redirect,
    request,
    session,
    url_for
    )
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

# connect env.py if it was created
if os.path.exists("env.py"):
    import env


# create flask app and define route decorator
app = Flask(__name__)


# define app configuration:
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


# set up mongo variable for mongo connection:
mongo = PyMongo(app)


@app.route("/")
# create route decorator for login page
@app.route("/login", methods=["GET", "POST"])
def login():
    """login view"""

    #  checks if the data is posted, ans assign a user_name to a variable
    if request.method == "POST":
        existing_user = mongo.db.users.find_one({
            "user_name": request.form.get("user_name").lower()
            })

        # checks if user_name exists
        if existing_user:
            if check_password_hash(
                existing_user["user_password"], request.form.get
                    ("user_password")):
                session["user"] = request.form.get("user_name").lower()
                flash("Welcome, {}".format(request.form.get("user_name")))
                return redirect(url_for(
                    'user_dashboard',
                    username=session["user"])
                    )

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
    """register view"""

    # registration functionality
    if request.method == "POST":

        # checks database if the user_email already registered
        existing_email = mongo.db.users.find_one({
            "user_email": request.form.get("user_email").lower()
            })
        existing_user = mongo.db.users.find_one({
            "user_name": request.form.get("user_name").lower()
            })

        # checks database if the user_email already registered
        if existing_email:
            flash("email already exists, try again")
            return redirect(url_for("register"))

        # checks database if the user_name already registered
        if existing_user:
            flash("user name already exists, try again")
            return redirect(url_for("register"))

        # if no user we create new user
        register_dict = {
            "user_name": request.form.get("user_name").lower(),
            "user_email": request.form.get("user_email").lower(),
            "user_password": generate_password_hash(
                request.form.get("user_password")),
            }

        # insert new user into Mongo Db database
        mongo.db.users.insert_one(register_dict)

        # create session for newly registered user
        session["user"] = request.form.get("user_name").lower()
        flash("Registration successfull!")
        return redirect(
            url_for('user_dashboard', username=session["user"])
            )
    return render_template("register.html")


# create route decorator for home page
@app.route("/home", methods=["GET", "POST"])
def home():
    """home view"""

    # prevent direct access to admin pages from regular user profilles:
    if "user" in session and session["user"] == "admin":

        # define meetings variable for dropdown select element
        meetings = mongo.db.meetings.find()

        # form submission conditon - activating the filter
        if request.method == ["POST"]:
            # collect the input and assign to variable
            meetingname = request.form.get("meeting_name")

            # use variable to get link from the meeting document
            link = mongo.db.meetings.find_one({
                "meeting_name": meetingname
                })["meeting_dashboardlink"]

        # default variable for meeting name to avoid "TypeError:
        # 'NoneType' object is not subscriptable"
        meetingname = "MS1"

        # default variable for iframe link
        link = mongo.db.meetings.find_one({
            "meeting_name": meetingname})["meeting_dashboardlink"]

        return render_template(
            "home.html",
            meetings=meetings,
            meetingname=meetingname,
            link=link
            )

    # defensive programming - sending the user to log himself out
    else:
        flash("Please login as Admin to access the page")
        return redirect(url_for('logout'))


# create route decorator for user dashboard page
@app.route("/user_dashboard/<username>", methods=["POST", "GET"])
def user_dashboard(username):
    """ user dashboard view """

    # if user in session defensive programming:
    if "user" in session:

        # create username variable for user_dashboard template entrance
        username = mongo.db.users.find_one(
            {"user_name": session["user"]})["user_name"]
        # create completionstatus variable for the loop on
        # user_dashboard selected component

        completionstatus = mongo.db.completionstatus.find()

        # define variable for automatic filter
        user = session["user"]

        # define variable for filtering selection
        action_status = request.form.get('action_status')

        # variable for action status selection after it has
        # been selected by filter
        actionstatusselection = action_status

        # define variables for kpis and actions loop -
        # it should be filtered to user as kpi_owner,
        # and if it is admin it should not filter,
        # this nested conditions should also be used
        # for filter section of actions
        if user == "admin":

            # variable kpis for KPIs section when user is logged in as admin
            kpis = mongo.db.kpi.find()

            # variable kpis for KPIs section when user is logged in as admin
            actions = mongo.db.actions.find()

            # action status filtering condition - activated after
            # the action status is selected
            if request.method == "POST":
                actions = list(
                    mongo.db.actions.find({
                        "action_status": action_status
                        }))

        # user logged in as non-admin
        else:

            # create kpis for KPI summary section if the user is non-admin
            kpis = list(mongo.db.kpi.find({"$text": {"$search": user}}))

            # create actions variable for non-admin
            actions = list(
                mongo.db.actions.find({"action_accountable": user})
                )

            # create actions variable for non-admin when filter is activated
            if request.method == "POST":

                # this filter has 2 filters - user and action status
                #  that is selected from filter section
                actions = list(
                    mongo.db.actions.find({
                        "action_accountable": user,
                        "action_status": action_status
                        })
                    )

        # pass all the variables into the loop
        if session["user"]:
            return render_template(
                "user_dashboard.html",
                username=username,
                actions=actions,
                completionstatus=completionstatus,
                kpis=kpis,
                user=user,
                action_status=action_status,
                actionstatusselection=actionstatusselection
                )
        return redirect(url_for('login'))

    # defensive programming getting back to logout
    else:
        flash("Please, login to access the page")
        return redirect(url_for('logout'))


@app.route("/logout")
def logout():
    """logout function"""

    # remove session cookies
    session.clear()
    flash("You have logged out")
    return redirect("login")


# setup router and function
@app.route("/admin_setup")
def setup():
    """setup view"""

    # prevent direct access
    if "user" in session and session["user"] == "admin":

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

        # collect all the kpistatuss
        kpistatuss = mongo.db.kpistatuss.find()

        # render setup.html using variables
        return render_template(
            "setup.html",
            users=users,
            completionstatus=completionstatus,
            depts=depts,
            workstreams=workstreams,
            meetings=meetings,
            kpi=kpi,
            kpistatuss=kpistatuss
            )

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# add user route decorator and add_user function
@app.route("/add_user", methods=["POST", "GET"])
def add_user():
    """add new user view"""

    # defensive programming
    if "user" in session and session["user"] == "admin":

        # add user functionality
        if request.method == "POST":

            # checks database if the user_email already added
            existing_email = mongo.db.users.find_one({
                "user_email": request.form.get("user_email")
                })

            existing_user = mongo.db.users.find_one({
                "user_name": request.form.get("user_name")
                })

            # checks database if the user_email already registered
            if existing_email:
                flash("email already exists, try again")
                return redirect(url_for("add_user"))

            # checks database if the user_name already registered
            if existing_user:
                flash("user name already exists, try again")
                return redirect(url_for("add_user"))

            # if no user we create new user
            add_newuser = {
                "user_name": request.form.get("user_name").lower(),
                "user_email": request.form.get("user_email").lower(),
                "user_password": generate_password_hash(
                    request.form.get("user_password")
                    ),
            }

            # insert new user into Mongo Db database
            mongo.db.users.insert_one(add_newuser)
            flash("New User added")
            return redirect(url_for('setup'))

        # render add_user
        return render_template("add_user.html")

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# function to add kpiinput
@app.route("/add_kpiinput", methods=["GET", "POST"])
def add_kpiinput():
    """add kpi input view"""

    if "user" in session:
        # variable for kpistatuss dropdown
        kpistatuss = mongo.db.kpistatuss.find()

        # variable for logdate=today, help on
        # https://www.programiz.com/python-programming/
        # datetime/current-datetime
        today = date.today().strftime("%d-%m-%Y")

        # variable for weeknumber, python documentation source:
        # https://docs.python.org/3/library/datetime.html?
        # highlight=datetime#datetime.datetime
        weeknumber = date.today().strftime("%W")

        # kpi variable for select element on kpi_name
        kpi = mongo.db.kpi.find()

        # variable for kpi_owner
        owners = mongo.db.users.find()

        # if request method is post condition
        if request.method == "POST":

            # create a variable for kpi input
            kpiinput = {
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

            # based on kpiinput define a variable to update
            # kpi collection fields
            latestinput = {
                "kpi_lastlogdate": request.form.get("input_logdate"),
                "kpi_lastbsl": request.form.get("input_bsl"),
                "kpi_lasttgt": request.form.get("input_tgt"),
                "kpi_lastact": request.form.get("input_act"),
                "kpi_laststatus": request.form.get("input_status")
            }

            # update kpi collection for specific fields following MongoDb
            # documentation -https://docs.mongodb.com/manual/reference/
            # operator/update/set/. Problem: the code {$set:latestinput}
            # did not work Johann from student support helped me - i had to
            # correct the code and add "" - {"$set":latestinput)
            mongo.db.kpi.update({
                "kpi_name": request.form.get(
                    "input_kpiname"
                    )
                }, {"$set": latestinput})

            # show the message that the operation was done successfully
            flash("KPI Input was successfully added")

            # redirect to home page
            return redirect(url_for('kpi_input'))

        # render add_kpi input page
        return render_template(
            "add_kpiinput.html",
            kpi=kpi,
            kpistatuss=kpistatuss,
            owners=owners,
            weeknumber=weeknumber,
            today=today
            )

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# setp admin kpi inputs page
@app.route("/add_kpi", methods=["POST", "GET"])
def add_kpi():
    """add new user view"""

    if "user" in session and session["user"] == "admin":
        # add select dropdown list
        owners = mongo.db.users.find()

        # add kpi into mongodb
        if request.method == "POST":
            kpi = {
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

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# create setup function for adding department
@app.route("/add_department", methods=["POST", "GET"])
def add_department():
    """add_department view"""

    # defensive programming
    if "user" in session and session["user"] == "admin":
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

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# create setup function for adding worksream
@app.route("/add_workstream", methods=["POST", "GET"])
def add_workstream():
    """add_workstream view"""

    if "user" in session and session["user"] == "admin":
        if request.method == "POST":

            # create a variable for new workstream
            new_workstream = {
                "workstream_name": request.form.get("workstream_name"),
                "workstream_shortname": request.form.get(
                    "workstream_shortname"
                    )
                }

            # insert new add_department inside status collection
            mongo.db.workstreams.insert_one(new_workstream)

            # show the message that the operation was done successfully
            flash("New workstream was successfully added")
            return redirect(url_for('setup'))
        return render_template("add_workstream.html")

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# create setup function to add new meeting
@app.route("/add_meeting", methods=["POST", "GET"])
def add_meeting():
    """add_meeting view"""

    if "user" in session and session["user"] == "admin":
        if request.method == "POST":

            # check if link  is defined
            link_defined = "link defined" if request.form.get(
                "meeting_linkdefined"
                ) else "not defined"

            # create a variable for new meeting
            new_meeting = {
                "meeting_linkdefined": link_defined,
                "meeting_name": request.form.get("meeting_name"),
                "meeting_shortname": request.form.get("meeting_shortname"),
                "meeting_dashboardlink": request.form.get(
                    "meeting_dashboardlink"
                    )
            }

            # insert new add_department inside status collection
            mongo.db.meetings.insert_one(new_meeting)

            # show the message that the operation was done successfully
            flash("New meeting was successfully added")
            return redirect(url_for('setup'))
        return render_template("add_meeting.html")

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# create setup function to add new kpi status
@app.route("/add_kpistatus", methods=["POST", "GET"])
def add_kpistatus():
    """add_kpistatus view"""

    # prevent direct access to th etemplate
    if "user" in session and session["user"] == "admin":
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

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# create setup function to add new action completion status
@app.route("/add_completionstatus", methods=["POST", "GET"])
def add_completionstatus():
    """add_completionstatus view"""

    # defensive programming
    if "user" in session and session["user"] == "admin":
        if request.method == "POST":

            # create a variable for new meeting
            new_completionstatus = {
                "completionstatus_name":
                request.form.get("completionstatus_name")
            }

            # insert new add_department inside status collection
            mongo.db.completionstatus.insert_one(new_completionstatus)

            # show the message that the operation was done successfully
            flash("New KPI Status was successfully added")
            return redirect(url_for('setup'))
        return render_template("add_completionstatus.html")

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# function to add actions
@app.route("/add_action", methods=["POST", "GET"])
def add_action():
    """add_action view"""

    if "user" in session:

        # variable for logdate = today, help on
        # https://www.programiz.com/python-programming/datetime/
        # current-datetime
        today = date.today().strftime("%d-%m-%Y")

        # calculating the action number
        action_number = str(mongo.db.actions.find().count()+1)

        # activating the form
        if request.method == "POST":
            # added varialble for action_number on add_action form
            action_number = str(mongo.db.actions.find().count()+1)

            # create a variable for new action
            task = {
                # used action nuumber variabe to input into mongodb
                "action_refno": action_number,
                "action_name": request.form.get("action_name"),
                "action_due": request.form.get("action_due"),
                "action_accountable": request.form.get(
                    "action_accountable"
                    ),
                "action_dept": request.form.get("action_dept"),
                "action_logdate": request.form.get("action_logdate"),
                "action_meeting": request.form.get("action_meeting"),
                "action_workstream": request.form.get(
                    "action_workstream"
                    ),
                "action_status": request.form.get("action_status")
                }

            # insert new action inside actions collection
            mongo.db.actions.insert_one(task)

            # show the message that the operation was done successfully
            flash("New action was successfully added")
            return redirect(
                url_for(
                    'user_dashboard',
                    username=session['user']
                    )
                )

        # variables for selection dropdown lists on add_action template, sorted
        users = mongo.db.users.find().sort("user_name", 1)
        meetings = mongo.db.meetings.find().sort("meeting_name", 1)
        depts = mongo.db.depts.find().sort("dept_name", 1)
        workstreams = mongo.db.workstreams.find().sort(
            "workstream_name", 1
            )
        completionstatus = mongo.db.completionstatus.find()

        # return render template using variables for dropdowns
        return render_template(
            "add_action.html",
            users=users,
            meetings=meetings,
            depts=depts,
            workstreams=workstreams,
            action_number=action_number,
            completionstatus=completionstatus,
            today=today
            )

    # defensive programming message
    else:
        flash("Please, login to access the page")
        return redirect(url_for('logout'))


# create edit_user function
@app.route("/edit_user/<user_id>", methods=["POST", "GET"])
def edit_user(user_id):
    """add_user view"""

    # defensive programming - access to admin only
    if "user" in session and session["user"] == "admin":

        # create user variable to prefill user input values in the form
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

        # update changed user data into mongodb
        if request.method == "POST":
            edituser = {
                    "user_name": request.form.get("user_name").lower(),
                    "user_email": request.form.get("user_email").lower(),
                    "user_password": generate_password_hash(
                        request.form.get("user_password")
                        ),
                    }

            # insert new user into Mongo Db database
            mongo.db.users.update({"_id": ObjectId(user_id)}, edituser)
            flash("User update successfull!")
            return redirect(url_for('setup'))
        return render_template("edit_user.html", user=user)

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# create edit_department function
@app.route("/edit_department/<dept_id>", methods=["POST", "GET"])
def edit_department(dept_id):
    """edit_meeting view"""

    # defensive programming to prevent from direct access
    if "user" in session and session["user"] == "admin":

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
        return render_template(
            "edit_department.html",
            dept=dept
            )

    # defensive programming message
    else:
        flash("Please, login as Admin  to access the page")
        return redirect(url_for('logout'))


# create edit_workstream function
@app.route("/edit_workstream/<workstream_id>", methods=["POST", "GET"])
def edit_workstream(workstream_id):
    """edit_meeting view"""

    # prevent direct non-admin access to template
    if "user" in session and session["user"] == "admin":

        # create workstream variable to prefill workstream input
        # values in the form
        workstream = mongo.db.workstreams.find_one({
            "_id": ObjectId(workstream_id)
            })

        # update changed workstream data into mongodb
        if request.method == "POST":
            editworkstream = {
                    "workstream_name": request.form.get("workstream_name"),
                    "workstream_shortname":
                    request.form.get("workstream_shortname")
                    }

        # insert new department into Mongo Db database
            mongo.db.workstreams.update(
                {"_id": ObjectId(workstream_id)},
                editworkstream
                )
            flash("Workstream update successfull!")
            return redirect(url_for('setup'))
        return render_template(
            "edit_workstream.html",
            workstream=workstream
            )

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# create edit_meeting function
@app.route("/edit_meeting/<meeting_id>", methods=["POST", "GET"])
def edit_meeting(meeting_id):
    """edit_meeting view"""

    # prevent direct non-admin access to thetemplate
    if "user" in session and session["user"] == "admin":

        # create meeting variable to prefill meeting input values in the form
        meeting = mongo.db.meetings.find_one(
            {"_id": ObjectId(meeting_id)}
            )

        # update changed meeting data into mongodb
        if request.method == "POST":

            # check if link  is defined by switch
            link_defined = "link defined" if request.form.get(
                "meeting_linkdefined"
                ) else "not defined"

            editmeeting = {
                    "meeting_linkdefined": link_defined,
                    "meeting_name": request.form.get("meeting_name"),
                    "meeting_shortname": request.form.get("meeting_shortname"),
                    "meeting_dashboardlink": request.form.ge(
                        "meeting_dashboardlink"
                        )
                }

        # insert new meeting into Mongo Db database
            mongo.db.meetings.update({
                "_id": ObjectId(meeting_id)
                }, editmeeting)
            flash("Meeting update successfull!")
            return redirect(url_for('setup'))
        return render_template(
            "edit_meeting.html",
            meeting=meeting
            )

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# create edit_kpi function
@app.route("/edit_kpi/<kpi_id>", methods=["POST", "GET"])
def edit_kpi(kpi_id):
    """edit_kpi view"""

    # prevent from direct access by other users
    if "user" in session and session["user"] == "admin":

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

            # informing the user that it was done
            flash("KPI update successfull!")
            return redirect(url_for('setup'))

        # define users variable for  KPI owner seectin
        users = mongo.db.users.find().sort("user_name", 1)
        return render_template("edit_kpi.html", kpi=kpi, users=users)

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# create edit_kpistatus function
@app.route("/edit_kpistatus/<kpistatus_id>", methods=["POST", "GET"])
def edit_kpistatus(kpistatus_id):
    """edit_kpistatus view"""

    # prevent from direct access
    if "user" in session and session["user"] == "admin":

        # kpistatus variable to prefill input values in the form
        kpistatus = mongo.db.kpistatuss.find_one({
            "_id": ObjectId(kpistatus_id)
            })

        # update changed kpistatus data into mongodb
        if request.method == "POST":
            editkpistatus = {
                    "kpistatus_name": request.form.get("kpistatus_name"),
                    "kpistatus_color": request.form.get("kpistatus_color")
                    }

        # insert new kpistatus into Mongo Db database
            mongo.db.kpistatuss.update({
                "_id": ObjectId(kpistatus_id)
                },
                editkpistatus)
            flash("KPI Status update successfull!")
            return redirect(url_for('setup'))
        return render_template(
            "edit_kpistatus.html",
            kpistatus=kpistatus
            )

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# create edit_completionstatus function
@app.route(
    "/edit_completionstatus/<completionstatus_id>",
    methods=["POST", "GET"]
    )
def edit_completionstatus(completionstatus_id):
    """edit_completionstatus fro action view"""

    # prevent direct access
    if "user" in session and session["user"] == "admin":

        # create completionstatus variable to prefill input value in the form
        completionstatus = mongo.db.completionstatus.find_one(
            {"_id": ObjectId(completionstatus_id)}
            )

        # update changed completionstatus data into mongodb
        if request.method == "POST":
            editcompletionstatus = {
                    "completionstatus_name": request.form.get(
                        "completionstatus_name"
                        )
                }

        # insert new completionstatus into Mongo Db database
            mongo.db.completionstatus.update(
                {"_id": ObjectId(completionstatus_id)},
                editcompletionstatus
                )

            # operation successfull mesage
            flash("Action Completion Status update successfull!")
            return redirect(url_for('setup'))
        return render_template(
            "edit_completionstatus.html",
            completionstatus=completionstatus
            )

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# create edit_kpi input function
@app.route("/edit_kpiinput/<kpiinput_id>", methods=["POST", "GET"])
def edit_kpiinput(kpiinput_id):
    """edit_kpiinput view"""

    # prevent form direct access by other users
    if "user" in session and session["user"] == "admin":

        # create kpiinput variable to prefill kpiinput input values in the form
        inp = mongo.db.kpiinputs.find_one(
            {"_id": ObjectId(kpiinput_id)}
            )

        # variable for kpiowners select
        owners = mongo.db.users.find()

        # variable for KPIs list select
        kpis = mongo.db.kpi.find()

        # user variable
        user = session["user"]

        # kpi statuss variable for dropdown on edit_kpiinput template
        kpistatuss = mongo.db.kpistatuss.find()

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
                    "input_kpiowner": request.form.get("input_kpiowner"),
                    "input_status": request.form.get("input_status")
                }

            # insert new kpiinput into Mongo Db database
            mongo.db.kpiinputs.update(
                {"_id": ObjectId(kpiinput_id)},
                editkpiinput
                )

            # based on kpiinput define a variable to update
            # kpi collection fields
            latestinput = {
                "kpi_lastlogdate": request.form.get("input_logdate"),
                "kpi_lastbsl": request.form.get("input_bsl"),
                "kpi_lasttgt": request.form.get("input_tgt"),
                "kpi_lastact": request.form.get("input_act"),
                "kpi_laststatus": request.form.get("input_status")
                }

            # update kpi collection:
            mongo.db.kpi.update({
                "kpi_name": request.form.get("input_kpiname")
                }, {"$set": latestinput})

            flash("KPI input update successfull!")

            return redirect(url_for('kpi_input'))
        return render_template(
            "edit_kpiinput.html",
            input=inp,
            user=user,
            owners=owners,
            kpis=kpis,
            kpistatuss=kpistatuss
            )

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# create edit_actionstatus input function
@app.route("/edit_actionstatus/<action_id>", methods=["POST", "GET"])
def edit_actionstatus(action_id):
    """edit_actionstatus view"""

    # prevent non-authorised direct access to the
    # page with defensive programming
    if "user" in session:

        # find the right action for status update
        action = mongo.db.actions.find_one({"_id": ObjectId(action_id)})

        # completionsattus collection for status dropdown on select
        completionstatus = mongo.db.completionstatus.find()

        # submit form update
        if request.method == "POST":

            # create variable for action update
            editactionstatus = {
                    "action_status": request.form.get("action_status")
                }
            # update an action with actionstatus in collection
            # -address only specific field that was changed
            mongo.db.actions.update(
                {"_id": ObjectId(action_id)},
                {"$set": editactionstatus}
                )

            # inform about successfull completion
            flash("Action status was updated")

            return redirect(url_for(
                'user_dashboard',
                username=session["user"]
                )
                )
        return render_template(
            "edit_actionstatus.html",
            action=action,
            completionstatus=completionstatus
            )

    # defensive programming message
    else:
        flash("Please, login to access the page")
        return redirect(url_for('logout'))


# create edit_action function
@app.route("/edit_action/<action_id>", methods=["POST", "GET"])
def edit_action(action_id):
    """edit_action view"""

    # prevent from direct access by non-admin
    if "user" in session and session["user"] == "admin":

        # find the right action for update
        action = mongo.db.actions.find_one(
            {"_id": ObjectId(action_id)}
            )

        # use completionsattus collection for status dropdawn
        # on select element
        completionstatus = mongo.db.completionstatus.find()

        # use completionsattus collection for status
        # dropdawn on select element
        users = mongo.db.users.find()

        # submit form update
        if request.method == "POST":
            # create variable for action update
            editaction = {
                    "action_refno": request.form.get("action_refno"),
                    "action_name": request.form.get("action_name"),
                    "action_due": request.form.get("action_due"),
                    "action_accountable": request.form.get(
                        "action_accountable"
                        ),
                    "action_status": request.form.get("action_status")
                }

            # update an action in collection - address only
            # specific fields that was changed
            mongo.db.actions.update(
                {"_id": ObjectId(action_id)},
                {"$set": editaction}
                )

            # inform about successfull completion
            flash("Action was updated")

            return redirect(url_for(
                'user_dashboard', username=session["user"])
                )
        return render_template(
            "edit_action.html",
            action=action,
            completionstatus=completionstatus,
            users=users
            )

    # defensive programming message
    else:
        flash("Please, login as Admin to access the page")
        return redirect(url_for('logout'))


# user delete function for setup template
@app.route("/delete_user/<user_id>")
def delete_user(user_id):
    """delete_user functionality"""

    mongo.db.users.remove({"_id": ObjectId(user_id)})
    flash("User was deleted")
    return redirect(url_for('setup'))


# department delete function for setup template
@app.route("/delete_department/<dept_id>")
def delete_department(dept_id):
    """delete_department functionality"""

    mongo.db.depts.remove({"_id": ObjectId(dept_id)})
    flash("Department was deleted")
    return redirect(url_for('setup'))


# workstream delete function for setup template
@app.route("/delete_workstream/<workstream_id>")
def delete_workstream(workstream_id):
    """delete_workstream functionality"""

    mongo.db.workstreams.remove({"_id": ObjectId(workstream_id)})
    flash("Workstream was deleted")
    return redirect(url_for('setup'))


# meeting delete function for setup template
@app.route("/delete_meeting/<meeting_id>")
def delete_meeting(meeting_id):
    """delete_meeting functionality"""

    mongo.db.meetings.remove({"_id": ObjectId(meeting_id)})
    flash("Meeting was deleted")
    return redirect(url_for('setup'))


# KPI delete function for setup template
@app.route("/delete_kpi/<kpi_id>")
def delete_kpi(kpi_id):
    """delete_kpi functionality"""

    mongo.db.kpi.remove({"_id": ObjectId(kpi_id)})
    flash("The KPI was deleted")
    return redirect(url_for('setup'))


# KPI status delete function for setup template
@app.route("/delete_kpistatus/<kpistatus_id>")
def delete_kpistatus(kpistatus_id):
    """delete_kpistatus functionality"""

    mongo.db.kpistatuss.remove({"_id": ObjectId(kpistatus_id)})
    flash("The KPI Status was deleted")
    return redirect(url_for('setup'))


# Action completion status delete function for setup template
@app.route("/delete_completionstatus/<completionstatus_id>")
def delete_completionstatus(completionstatus_id):
    """delete_completionstatus for action functionality"""

    mongo.db.completionstatus.remove({"_id": ObjectId(completionstatus_id)})
    flash("Action comlpetion status was deleted")
    return redirect(url_for('setup'))


# Action delete function for user_dashboard=>edit template
@app.route("/delete_action/<action_id>")
def delete_action(action_id):
    """delete_action functionality"""

    mongo.db.actions.remove({"_id": ObjectId(action_id)})
    flash("Action was deleted")
    return redirect(url_for(
        'user_dashboard',
        username=session['user']
        ))


# kpi input delete function for kpi_input=>edit
# kpiinput template for admin only
@app.route("/delete_kpiinput/<kpiinput_id>")
def delete_kpiinput(kpiinput_id):
    """delete_kpiinput functionality"""

    mongo.db.kpiinputs.remove(
        {"_id": ObjectId(kpiinput_id)}
        )
    flash("KPI input was deleted")
    return redirect(url_for('kpi_input'))


# kpi inputs page - add input page
@app.route("/kpi_input", methods=["POST", "GET"])
def kpi_input():
    """kpi inputs page - add input page"""

    # prevent direct access from non-user
    if "user" in session:

        # create kpi input variable for the loop on kpi_input
        kpis = mongo.db.kpi.find()

        # add user variable for title and nested statement
        user = session["user"]

        # nested coniditons to build kpi inputs table for user login
        # and search text
        if user == "admin":

            # create kpiinputs variable for table body values
            kpiintputs = mongo.db.kpiinputs.find().sort(
                "input_weeknumber", 1
                )

            # condition statement for sirting the week
            if request.method == "POST":

                # search variable if the form is submitted
                search_kpiinput = str(
                    request.form.get("search_kpiinput")
                    )

                # using search variable to generate kpiintputs
                # for the table rendering
                kpiintputs = list(
                    mongo.db.kpiinputs.find({
                        "$text": {"$search": search_kpiinput}
                        }))

        else:
            # variable for non-admin
            kpiintputs = list(
                mongo.db.kpiinputs.find(
                    {"$text": {"$search": user}})
                )

            # condition for non-admin when serhc button activated
            if request.method == "POST":

                # variable for 4 fields index text search - input_kpiname,
                # input_kpiowner, input_kpistatus, input_weeknumber - mongodb:
                # input_kpiname_text_input_kpiowner_text_input_
                # weeknumber_text_input_status_text
                search_kpiinput = request.form.get("search_kpiinput")

                # variable for search for 2 criterea user AND 4 fields text
                kpiintputs = list(mongo.db.kpiinputs.find(
                    {
                        "input_kpiowner": user,
                        "$text": {"$search": search_kpiinput}
                        }
                        ))

        # render the page
        return render_template(
            "kpi_input.html",
            kpiintputs=kpiintputs,
            user=user,
            kpis=kpis
            )

    # defensive programming message
    else:
        flash("Please, login to access the page")
        return redirect(url_for('logout'))


@app.route("/copy_kpiinput/<kpiinput_id>", methods=["POST", "GET"])
def copy_kpiinput(kpiinput_id):
    """create copy kpiinput function"""

    # prevent form direct access from non-user
    if "user" in session:
        # create kpiinput variable to prefill kpiinput input values in the form
        inp = mongo.db.kpiinputs.find_one({
            "_id": ObjectId(kpiinput_id)
            })

        # variable for kpiowners select
        owners = mongo.db.users.find()

        # variable for KPIs list select
        kpis = mongo.db.kpi.find()

        # user variable
        user = session["user"]

        # kpi statuss variable for dropdown on edit_kpiinput template
        kpistatuss = mongo.db.kpistatuss.find()

        # create new kpiinput data into mongodb
        if request.method == "POST":
            copied_kpiinput = {
                    "input_kpiname": request.form.get("input_kpiname"),
                    "input_logdate": request.form.get("input_logdate"),
                    "input_weeknumber": request.form.get(
                        "input_weeknumber"
                        ),
                    "input_uom": request.form.get("input_uom"),
                    "input_bsl": request.form.get("input_bsl"),
                    "input_tgt": request.form.get("input_tgt"),
                    "input_act": request.form.get("input_act"),
                    "input_kpiowner": request.form.get("input_kpiowner"),
                    "input_status": request.form.get("input_status")
                }

            # insert new kpiinput into Mongo Db database
            mongo.db.kpiinputs.insert(copied_kpiinput)

            # based on kpiinput define a variable to update
            # kpi collection fields
            latestinput = {
                "kpi_lastlogdate": request.form.get("input_logdate"),
                "kpi_lastbsl": request.form.get("input_bsl"),
                "kpi_lasttgt": request.form.get("input_tgt"),
                "kpi_lastact": request.form.get("input_act"),
                "kpi_laststatus": request.form.get("input_status")
            }

            # update kpi collection:
            mongo.db.kpi.update(
                {"kpi_name": request.form.get("input_kpiname")},
                {"$set": latestinput}
                )

            flash("New KPI copied from previous successfully!")

            # render page
            return redirect(url_for('kpi_input'))
        return render_template(
            "copy_kpiinput.html",
            input=inp,
            user=user,
            owners=owners,
            kpis=kpis,
            kpistatuss=kpistatuss
            )

    # defensive programming message
    else:
        flash("Please, login to access the page")
        return redirect(url_for('logout'))


# tell where and how to return an app, DO NOT FORGET TO
# change debug=Falseputting in production.
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=os.environ.get("PORT"), debug=False)
