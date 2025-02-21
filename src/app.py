from flask import Flask,render_template,redirect,request,jsonify
from werkzeug.utils import secure_filename
from web3 import Web3,HTTPProvider
from dotenv import load_dotenv  # Load environment variables
import boto3
import json
import os

# Load environment variables from .env file
load_dotenv()

app=Flask(__name__)

# AWS Credentials from .env
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")  # Default region if not specified

def check_iris_existence(new_image_path):
    """Iterates through all images in 'uploads' folder and checks for a match using AWS Rekognition."""
    image_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.lower().endswith(tuple(ALLOWED_EXTENSIONS))]

    for existing_image in image_files:
        existing_image_path = os.path.join(app.config['UPLOAD_FOLDER'], existing_image)

        with open(new_image_path, "rb") as new_img, open(existing_image_path, "rb") as existing_img:
            response = rekognition.compare_faces(
                SourceImage={'Bytes': new_img.read()},
                TargetImage={'Bytes': existing_img.read()},
                SimilarityThreshold=90
            )

        if response['FaceMatches']:
            return True  # Match found

    return False  # No match found

# Configure Upload Folder
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

votingArtifactPath="../build/contracts/voting.json"
blockchainServer="http://127.0.0.1:7545"

def connectWithContract(wallet,artifact=votingArtifactPath):
    web3=Web3(HTTPProvider(blockchainServer)) # it is connecting with server
    print('Connected with Blockchain Server')

    if (wallet==0):
        web3.eth.defaultAccount=web3.eth.accounts[0]
    else:
        web3.eth.defaultAccount=wallet
    print('Wallet Selected')

    with open(artifact) as f:
        artifact_json=json.load(f)
        contract_abi=artifact_json['abi']
        contract_address=artifact_json['networks']['5777']['address']
    
    contract=web3.eth.contract(abi=contract_abi,address=contract_address)
    print('Contract Selected')
    return contract,web3

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

        if len(aadhar) != 12 or not aadhar.isdigit():
            return render_template("addPoll.html", error="Aadhar should contain 12 digits"), 400

        iris_file = request.files['iris']

        if iris_file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if iris_file and allowed_file(iris_file.filename):
            # Generate timestamp-based filename
            file_extension = iris_file.filename.rsplit('.', 1)[1].lower()
            timestamp = int(time.time())  # Get current timestamp
            filename = f"{timestamp}.{file_extension}"  # Example: 1708456789.jpg
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save the image temporarily before checking
            iris_file.save(file_path)

            # Check if the iris image already exists
            if check_iris_existence(file_path):
                os.remove(file_path)  # Delete temp file if match is found
                return render_template("addUser.html", error="Iris already registered"), 400

            # Connect to Blockchain and Register the User
            contract, web3 = connectWithContract()
            tx_hash = contract.functions.registerVoter(name, aadhar, file_path).transact()
            web3.eth.waitForTransactionReceipt(tx_hash)

            return render_template("addUser.html", success="User added successfully"), 201
        else:
            return render_template("addUser.html", error="Invalid file format"), 400

    except Exception as e:
        return render_template("addUser.html", error="Internal server error"), 500
 
    

if __name__== "__main__":
    app.run(debug=True)