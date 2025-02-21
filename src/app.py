from flask import Flask,render_template,redirect

app=Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/admin")
def adminDashboard():
    return render_template("adminDashboard.html")

@app.route("/addUser")
def addUser():
    return render_template("addUser.html")

@app.route("/addPoll")
def addPoll():
    return render_template("addPoll.html")

@app.route("/login")
def login():
    return render_template("login.html")

if __name__== "__main__":
    app.run(debug=True)