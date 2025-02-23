import email
from flask import Flask, render_template,jsonify, redirect, request, session, flash, url_for
from werkzeug.utils import secure_filename
from web3 import Web3, HTTPProvider
from dotenv import load_dotenv  # Load environment variables
import boto3, time, json, os
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import smtplib
from datetime import datetime, timedelta
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = "qwertyuiop"

# Email Credentials (Replace with your actual credentials)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "kr4785543@gmail.com"
EMAIL_PASSWORD = "qhuzwfrdagfyqemk"

otp_storage = {}

def send_otp(email):
    """
    Sends a one-time password (OTP) to the provided email.
    Returns True if email is sent successfully, else False.
    """
    try:
        # Generate a 6-digit OTP
        otp = random.randint(100000, 999999)
        otp_storage[email] = otp  # Store OTP (Use a database in real-world applications)

        # Email subject and body
        subject = "SecureVote - OTP for Password Reset"
        body = f"""
        Dear User,

        Your OTP for password reset is: {otp}

        Please use this OTP to proceed with resetting your password.

        Best Regards,
        SecureVote Team
        """

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send email using SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"OTP sent successfully to {email}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("Failed to authenticate with email server. Check your credentials.")
        return False
    except Exception as e:
        print(f"Error sending OTP: {str(e)}")
        return False


def send_confirmation_email(email, name):
    """ Sends an email confirming successful registration using SMTP """
    try:
        # Create message with proper encoding
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = "Secure Voting Platform - Registration Successful"
        
        body = f"""Dear {name},

Your account has been successfully created on the Secure Voting Platform.
Update your password ASAP.To confirn account creation you can use the password "irisvoting" temporarily.

Best Regards,
Secure Voting Team"""
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Create SMTP connection with proper error handling
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()  # Identify yourself to the server
            server.starttls()  # Secure the connection
            server.ehlo()  # Re-identify yourself over TLS
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)  # Use send_message instead of sendmail
            
        print(f"Confirmation email sent successfully to {email}")
        return True
    
    except smtplib.SMTPAuthenticationError:
        print("Failed to authenticate with Gmail. Check your email and app password.")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {str(e)}")
        return False
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False
# Configure Upload Folder
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def compare_images(image1_path, image2_path):
    """
    Compare two images using both structural similarity and mean squared error.
    Returns True if images are very similar, False otherwise.
    """
    try:
        # Read images
        img1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)
        
        if img1 is None or img2 is None:
            return False
            
        # Resize images to same dimensions
        height = 800  # Standard height for comparison
        width = int(height * img1.shape[1] / img1.shape[0])
        dim = (width, height)
        img1 = cv2.resize(img1, dim)
        img2 = cv2.resize(img2, dim)
        
        # Calculate structural similarity index
        similarity_index, _ = ssim(img1, img2, full=True)
        
        # Calculate Mean Squared Error
        mse = np.mean((img1 - img2) ** 2)
        
        # Print debug information
        print(f"Comparing {image1_path} with {image2_path}")
        print(f"Similarity Index: {similarity_index}")
        print(f"MSE: {mse}")
        
        # Return True if images are very similar (using more lenient thresholds)
        return similarity_index > 0.75 and mse < 5000
        
    except Exception as e:
        print(f"Error comparing images: {e}")
        return False

def send_vote_confirmation(email, name):
    """ Sends a thank-you email after the user casts a vote. """
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = "Thank You for Voting - Secure Voting Platform"

        body = f"""Dear {name},

Thank you for participating in the Secure Voting Platform.

Your vote has been successfully recorded. We appreciate your contribution to democracy.

Best Regards,  
Secure Voting Team
"""

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # 🔹 Create SMTP connection with error handling
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()  # Secure connection
            server.ehlo()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"Vote confirmation email sent successfully to {email}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("Failed to authenticate with Gmail. Check your email and app password.")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {str(e)}")
        return False
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False

def check_iris_existence(new_image_path):
    """Checks if an iris image already exists in the 'uploads' folder using image comparison."""
    try:
        # Get the list of existing images in uploads folder
        image_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                      if f.lower().endswith(tuple(app.config['ALLOWED_EXTENSIONS']))]
        
        # Skip comparing with itself
        image_files = [f for f in image_files if os.path.join(app.config['UPLOAD_FOLDER'], f) != new_image_path]
        
        for existing_image in image_files:
            existing_image_path = os.path.join(app.config['UPLOAD_FOLDER'], existing_image)
            
            if compare_images(new_image_path, existing_image_path):
                print(f"Duplicate iris found: New image matches with {existing_image}")
                return True
                
        return False
        
    except Exception as e:
        print(f"Error checking iris existence: {e}")
        return False

# Blockchain configuration
votingArtifactPath = "../build/contracts/voting.json"
blockchainServer = "http://127.0.0.1:7545"

def connectWithContract(wallet, artifact=votingArtifactPath):
    """Connects to the Ethereum Blockchain via Web3 and loads the smart contract."""
    web3 = Web3(HTTPProvider(blockchainServer))

    print('Connected to Blockchain')

    web3.eth.defaultAccount = web3.eth.accounts[wallet]

    with open(artifact) as f:
        artifact_json = json.load(f)
        contract_abi = artifact_json['abi']
        contract_address = artifact_json['networks']['5777']['address']

    contract = web3.eth.contract(abi=contract_abi, address=contract_address)
    print('Smart contract loaded')
    return contract, web3

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/admin")
def adminDashboard():
    try:
        contract,web3=connectWithContract(0)
        voters=contract.functions.getAllVoters().call()
        return render_template("adminDashboard.html",voters=voters)
    except Exception as e:
        print(e)
        return redirect(url_for("login"))

@app.route("/addUser")
def addUser():
    return render_template("addUser.html")

@app.route("/addPoll")
def addPoll():
    return render_template("addPoll.html")

@app.route("/addParty")
def ad_party():
    return render_template("addParty.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/viewPolls")
def viewPolls():
    try:
        contract,web3=connectWithContract(0)
        allPolls=contract.functions.getAllPolls().call()
        return render_template("userPolls.html",polls=allPolls)
    except Exception as e:
        flash(f"Error fetching polls: {str(e)}", "error")
        return redirect(url_for("dashboard"))  # Redirect in case of error

@app.route("/registerUser", methods=["POST"])
def userRegister():
    try:
        # Get Form Data
        name = request.form.get('name')
        aadhar = request.form.get('aadhar')
        email=request.form.get('email')
        print(name,aadhar,email)

        if not name or not aadhar or not email:
            flash("All fields are required", "error")
            return redirect(url_for("addUser"))

        if len(aadhar) != 12 or not aadhar.isdigit():
            flash("Aadhar should contain exactly 12 digits", "error")
            return redirect(url_for("addUser"))

        iris_file = request.files.get('iris')

        if not iris_file or iris_file.filename == '':
            flash("No file selected", "error")
            return redirect(url_for("addUser"))

        if iris_file and allowed_file(iris_file.filename):
            file_extension = iris_file.filename.rsplit('.', 1)[1].lower()
            timestamp = int(time.time())  
            filename = f"{timestamp}.{file_extension}"  
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            iris_file.save(file_path)

            if check_iris_existence(file_path):
                os.remove(file_path)  
                flash("Iris already registered", "error")
                return redirect(url_for("addUser"))

            # Connect to Blockchain and Register the User
            try:
                contract, web3 = connectWithContract(0)
                tx_hash = contract.functions.registerVoter(name, aadhar, filename,email,"irisvoting").transact()
                web3.eth.waitForTransactionReceipt(tx_hash)

                 # Send confirmation email
                send_confirmation_email(email, name)
                
                flash("User added successfully", "success")
                return redirect(url_for("addUser"))

            except Exception as e:
                error_message = str(e)
                last_sentence = error_message.split(":")[-1].strip()  # Extract last part after last colon
                flash(last_sentence, "error")  
                return redirect(url_for("addUser"))

        else:
            flash("Invalid file format. Only PNG, JPG, and JPEG allowed", "error")
            return redirect(url_for("addUser"))

    except Exception as e:
        error_message = str(e)
        last_sentence = error_message.split(":")[-1].strip()  
        flash(last_sentence, "error")  
        return redirect(url_for("addUser"))
    
@app.route("/login", methods=["POST"])
def userLogin():
    """Handles user login with Aadhar and password, using flash messages and templates."""
    aadhar = request.form.get("aadhar")
    password = request.form.get("password")

    if not aadhar or not password:
        flash("Aadhar and Password are required!", "error")
        return redirect(url_for("login"))
    
    if(aadhar=="959008065677" and password=="admin@123"):
        session['admin']="admin"
        return redirect(url_for("adminDashboard"))

    try:
        # Call Smart Contract Function
        contract,web3=connectWithContract(0)
        voter = contract.functions.getVoter(aadhar).call()
        print(voter)

        if not voter:
            flash("Voter not registered!", "error")
            return redirect(url_for("login"))

        id,fullName, aadharNumber, irisImagePath, email, stored_password = voter

        # Check Password
        if password == stored_password:
            session["user"] = {"name": fullName, "aadhar": aadharNumber, "email": email}  # Store session
            flash("Login Successful!", "success")
            return redirect(url_for("dashboard"))  # Redirect to dashboard

        else:
            flash("Invalid Password!", "error")
            return redirect(url_for("login"))

    except Exception as e:
        print(e)
        flash(f"Login failed", "error")
        return redirect(url_for("login"))
    
@app.route("/dashboard")
def dashboard():
    try:
        session['user']
        return render_template("dashboard.html")
    except Exception as e:
        flash(f"Please login", "error")
        return redirect(url_for("login"))

@app.route("/addParty", methods=["POST"])
def add_party():
    """Handles poll creation by saving form data and an image."""
    try:
        # Get Form Data
        party_name = request.form.get("partyName")
        leader_name = request.form.get("leaderName")
        party_image = request.files.get("partyImage")

        # Validate Inputs
        if not party_name or not leader_name or not party_image:
            flash("All fields are required!", "error")
            return redirect(url_for("ad_party"))

        if not allowed_file(party_image.filename):
            flash("Invalid file format. Only PNG, JPG, and JPEG allowed!", "error")
            return redirect(url_for("ad_party"))

        # Save Image with Timestamp
        file_extension = party_image.filename.rsplit('.', 1)[1].lower()
        timestamp = int(time.time())  
        filename = f"{timestamp}.{file_extension}"  
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        party_image.save(file_path)
        
        id=session['pollId']

        contract,web3=connectWithContract(0)
        tx_hash=contract.functions.addParty(int(id),party_name,leader_name,filename).transact()
        web3.eth.waitForTransactionReceipt(tx_hash)

        flash("Party added successfully!", "success")
        return redirect(url_for("ad_party"))

    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("addPoll"))
    
@app.route("/addPoll", methods=["POST"])
def add_poll():
    try:
        # Read form data
        poll_name = request.form.get("pollName")
        poll_date = request.form.get("pollDate")
        start_time = request.form.get("startTime")
        end_time = request.form.get("endTime")

        # Validation
        if not poll_name or not poll_date or not start_time or not end_time:
            flash("All fields are required!", "error")
            return redirect(url_for("add_poll_page"))

        # Connect to Blockchain
        try:
            contract, web3 = connectWithContract(0)

            # Call Smart Contract Function to Add Poll
            tx_hash = contract.functions.addPoll(poll_name, poll_date, start_time, end_time).transact()
            web3.eth.waitForTransactionReceipt(tx_hash)

            flash("Poll added successfully!", "success")
            return redirect(url_for("addPoll"))

        except Exception as e:
            flash(f"Error adding poll: {str(e)}", "error")
            return redirect(url_for("addPoll"))

    except Exception as e:
        flash(f"Unexpected error: {str(e)}", "error")
        return redirect(url_for("addPoll"))

@app.route("/getAllPolls")
def getAllPolls():
    try:
        contract,web3=connectWithContract(0)
        allPolls=contract.functions.getAllPolls().call()
        return render_template("allPolls.html",polls=allPolls)
    except Exception as e:
        flash(f"Error fetching polls: {str(e)}", "error")
        return redirect(url_for("dashboard"))  # Redirect in case of error 
    
@app.route("/viewParties/<id>")
def view_parties(id):
    try:
        session['admin']
        session['pollId']=id
        contract,web3=connectWithContract(0)
        parties=contract.functions.getPartiesByPartyId(int(id)).call()
        print(parties)
        return render_template("parties.html",parties=parties)
    except Exception as e:
        contract,web3=connectWithContract(0)
        parties=contract.functions.getPartiesByPartyId(int(id)).call()
        print(parties)
        return render_template("userParties.html",parties=parties)
    
@app.route("/timer")
def timer():
    return render_template("timer.html")

@app.route("/voteNow/<id>")
def voteNow(id):
    contract, web3 = connectWithContract(0)
    poll = contract.functions.getPollById(int(id)).call()
    print("Raw Poll Data:", poll)
    session["pollingId"]=id

    # Extract date and time from the poll response
    poll_date = poll[2]  # Format: 'YYYY-MM-DD'
    poll_start_time = poll[3]  # Format: 'HH:MM'
    poll_end_time = poll[4]  # Format: 'HH:MM'

    # Combine date and time into full datetime strings
    poll_start_str = f"{poll_date} {poll_start_time}:00"  # 'YYYY-MM-DD HH:MM:SS'
    poll_end_str = f"{poll_date} {poll_end_time}:00"  # 'YYYY-MM-DD HH:MM:SS'

    # Convert formatted strings into datetime objects
    poll_start_datetime = datetime.strptime(poll_start_str, "%Y-%m-%d %H:%M:%S")
    poll_end_datetime = datetime.strptime(poll_end_str, "%Y-%m-%d %H:%M:%S")

    # Get current UTC time
    current_time_utc = datetime.utcnow()

    # Convert UTC to IST (UTC + 5 hours 30 minutes)
    current_time_ist = current_time_utc + timedelta(hours=5, minutes=30)


    # Debugging output
    print(f"Poll Start Time: {poll_start_datetime}")
    print(f"Current Time: {current_time_ist}")
    print(f"Poll End Time: {poll_end_datetime}")

    # Logic for navigation
    if current_time_ist >= poll_end_datetime:
        print("Polling ended")
        return render_template("timeout.html")  # Poll has ended
    elif poll_start_datetime <= current_time_ist < poll_end_datetime:
        print("Poll is active")
        return render_template("irisVerification.html")  # Poll is active
    else:
        print("Polling not started")
        return render_template("timer.html", time=poll_start_str)  # Poll hasn't started yet

@app.route("/verifyIris", methods=["POST"])
def verify_iris():
    """Verifies if the uploaded iris image matches an existing registered user."""
    try:
        # ✅ Check if an image is provided
        if 'iris' not in request.files:
            return jsonify({"success": False, "message": "No file provided"}), 400

        iris_file = request.files['iris']

        if iris_file.filename == '':
            return jsonify({"success": False, "message": "No file selected"}), 400

        if not allowed_file(iris_file.filename):
            return jsonify({"success": False, "message": "Invalid file format. Only PNG, JPG, and JPEG allowed"}), 400

        # ✅ Save the uploaded image temporarily
        file_extension = iris_file.filename.rsplit('.', 1)[1].lower()
        timestamp = int(time.time())
        filename = f"temp_{timestamp}.{file_extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        iris_file.save(file_path)

        print(f"✅ Temp file saved at: {file_path}")

        # ✅ Resize image to match stored format
        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        height = 800
        width = int(height * img.shape[1] / img.shape[0])
        img = cv2.resize(img, (width, height))
        cv2.imwrite(file_path, img)

        # ✅ Compare with existing registered iris images
        image_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER'])
                       if f.lower().endswith(tuple(app.config['ALLOWED_EXTENSIONS']))]

        print(f"✅ Found {len(image_files)} images to compare against")

        for existing_image in image_files:
            existing_image_path = os.path.join(app.config['UPLOAD_FOLDER'], existing_image)
            print(f"🔸 Checking against: {existing_image}")

            if compare_images(file_path, existing_image_path):
                print(f"✅ Match found with: {existing_image}")

                # ✅ If a match is found, retrieve Aadhar linked to the image
                contract, web3 = connectWithContract(0)
                all_voters = contract.functions.getAllVoters().call()

                for voter in all_voters:
                    id,name, aadhar, stored_image, email, _ = voter
                    voterDetails = contract.functions.getVoter(aadhar).call()
                    print(voterDetails)

                    # 🔹 Fix: Compare only filenames
                    if os.path.basename(stored_image) == existing_image:
                        os.remove(file_path)  # Clean up temp file
                        return jsonify({
                            "success": True,
                            "message": "Iris match found",
                            "aadhar": aadhar,
                            "name": name,
                            "email": email
                        }), 200

        # ✅ If no match found
        os.remove(file_path)  # Clean up temp file
        return jsonify({"success": False, "message": "Iris not recognized"}), 404

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route("/vote")
def vote():
    try:
        session['user']
        contract,web3=connectWithContract(0)
        parties=contract.functions.getPartiesByPartyId(int(session['pollingId'])).call()
        print(parties)
        return render_template("votenow.html",parties=parties)
    except Exception as e:
        flash(f"Please login", "error")
        return redirect(url_for("login"))

@app.route("/castVote", methods=["POST"])
def cast_vote():
    """
    Casts a vote for a given poll and party.
    """
    try:
        poll_id = session['pollingId']
        id=request.form.get('party_id')
        print(id)

        # Connect to Smart Contract
        contract, web3 = connectWithContract(0)
        # Check if voter has already voted
        has_voted = contract.functions.hasVoted(int(poll_id), session['user']['aadhar']).call()
        if has_voted:
            return render_template('voteCasted.html')

        # Cast the vote
        tx_hash = contract.functions.vote(int(poll_id), int(id), session['user']['aadhar']).transact()
        web3.eth.wait_for_transaction_receipt(tx_hash)

        # Send Thank-You Email
        voter_email = session['user']['email']
        voter_name = session['user']['name']
        send_vote_confirmation(voter_email, voter_name)
        return render_template("success.html"),200

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route("/viewResults", methods=["GET"])
def view_results():
    try:
        poll_id = request.args.get("pollId")
        if poll_id is None:
            return jsonify({"success": False, "message": "pollId is required"}), 400

        poll_id = int(poll_id)
        contract, web3 = connectWithContract(0)

        # Fetch poll results
        party_ids, vote_counts = contract.functions.getPollResults(poll_id).call()

        if not party_ids:
            return jsonify({"success": False, "message": "Poll not found or no votes recorded"}), 404

        # Format response
        results = [{"partyId": party_ids[i], "voteCount": vote_counts[i]} for i in range(len(party_ids))]

        return jsonify({"success": True, "pollId": poll_id, "results": results}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route("/timeout")
def timeout():
    return render_template("timedOut.html")

@app.route("/results")
def results():
    contract,web3=connectWithContract(0)
    allPolls=contract.functions.getAllPolls().call()
    return render_template("results.html",polls=allPolls)

@app.route("/deleteVoter/<aadhar>")
def deleteVoter(aadhar):
    try:
        session['admin']
        contract, web3 = connectWithContract(0)
        tx_hash = contract.functions.deleteVoter(aadhar).transact()
        web3.eth.wait_for_transaction_receipt(tx_hash)
        flash("Voter deleted successfully!", "success")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        flash(f"Error deleting voter: {str(e)}", "error")
        return redirect(url_for("adminDashboard"))

@app.route("/change-password", methods=["GET", "POST"])
def changePassword():
    return render_template("changePassword.html")

@app.route("/sendOtp",methods=['post'])
def sendOtp():    
    email=request.form.get("email")
    session['email']=email
    send_otp(email)
    return render_template("verify.html")

@app.route('/verifyOtp', methods=['POST'])
def verify_otp():
    """
    Verifies the OTP entered by the user.
    Expects JSON data: { "email": "user@example.com", "otp": "123456" }
    """
    try:
        email=session['email']
        otp_entered = int(request.form.get("otp"))

        # Check if OTP exists for the given email
        print(otp_storage)
        if email not in otp_storage:
            return jsonify({"success": False, "message": "OTP not found or expired."}), 400

        # Retrieve stored OTP
        stored_otp = otp_storage[email]


        # Validate OTP
        if stored_otp == otp_entered:
            del otp_storage[email]  # Remove OTP after successful verification
            return render_template("update.html")
        else:
            return render_template("verify.html",message="Invalid OTP. Please try again.")
    except ValueError:
        return render_template("verify.html",message="Invalid OTP format.")
    except Exception as e:
        return render_template("verify.html",message=f"Error: {str(e)}")

@app.route("/updatePassword", methods=["POST"])
def updatePassword():
    try:
        email = session['email']
        password = request.form.get('password')
        cpassword = request.form.get('cpassword')
        if password != cpassword:
            return render_template("update.html",message="Passwords do not match")
        contract, web3 = connectWithContract(0)
        tx_hash = contract.functions.updateVoterByEmail(email, password).transact()
        web3.eth.wait_for_transaction_receipt(tx_hash)
        return render_template("login.html")
    except Exception as e:
        return render_template("update.html",message=f"Error: {str(e)}")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
