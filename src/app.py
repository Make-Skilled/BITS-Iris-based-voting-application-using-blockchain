from flask import Flask, render_template, redirect, request, session, flash, url_for
from werkzeug.utils import secure_filename
from web3 import Web3, HTTPProvider
from dotenv import load_dotenv  # Load environment variables
import boto3, time, json, os
import numpy as np
from skimage.metrics import structural_similarity as ssim
import smtplib
import cv2

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = "qwertyuiop"

# Email Credentials (Replace with your actual credentials)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "kr4785543@gmail.com"
EMAIL_PASSWORD = "qhuzwfrdagfyqemk"

# AWS Credentials from .env
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")  # Default region if not specified

# Initialize AWS Rekognition client
rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

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
        
        # Return True if images are very similar
        return similarity_index > 0.95 and mse < 1000
        
    except Exception as e:
        print(f"Error comparing images: {e}")
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
                tx_hash = contract.functions.registerVoter(name, aadhar, file_path,email,"irisvoting").transact()
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
        return redirect(url_for("show_login"))

    try:
        # Call Smart Contract Function
        contract,web3=connectWithContract(0)
        voter = contract.functions.getVoter(aadhar).call()
        print(voter)

        if not voter:
            flash("Voter not registered!", "error")
            return redirect(url_for("login"))

        fullName, aadharNumber, irisImagePath, email, stored_password = voter

        # Check Password
        if password == stored_password:
            session["user"] = {"name": fullName, "aadhar": aadharNumber, "email": email}  # Store session
            flash("Login Successful!", "success")
            return redirect(url_for("dashboard"))  # Redirect to dashboard

        else:
            flash("Invalid Password!", "error")
            return redirect(url_for("login"))

    except Exception as e:
        flash(f"Login failed: {str(e)}", "error")
        return redirect(url_for("login"))
    
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/addPoll", methods=["POST"])
def add_poll():
    """Handles poll creation by saving form data and an image."""
    try:
        # Get Form Data
        party_name = request.form.get("partyName")
        leader_name = request.form.get("leaderName")
        party_image = request.files.get("partyImage")

        # Validate Inputs
        if not party_name or not leader_name or not party_image:
            flash("All fields are required!", "error")
            return redirect(url_for("show_add_poll_form"))

        if not allowed_file(party_image.filename):
            flash("Invalid file format. Only PNG, JPG, and JPEG allowed!", "error")
            return redirect(url_for("addPoll"))

        # Save Image with Timestamp
        file_extension = party_image.filename.rsplit('.', 1)[1].lower()
        timestamp = int(time.time())  
        filename = f"{timestamp}.{file_extension}"  
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        party_image.save(file_path)

        contract,web3=connectWithContract(0)
        tx_hash=contract.functions.addPoll(party_name,leader_name,file_path).transact()
        web3.eth.waitForTransactionReceipt(tx_hash)

        flash("Poll added successfully!", "success")
        return redirect(url_for("addPoll"))

    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("addPoll"))
    

if __name__ == "__main__":
    app.run(debug=True)
