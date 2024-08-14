import pandas as pd
from flask_cors import CORS # CORS for handling Cross-Origin Resource Sharing
import pickle 
from flask import Flask, request, jsonify,render_template,session,url_for,redirect
from pymongo import MongoClient 
from gradio_client import Client
from urllib.parse import quote_plus
username = quote_plus("nithish")
password = quote_plus("Spike@23")

connection_string = f"mongodb+srv://{username}:{password}@patient-data.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
print(connection_string)
client = MongoClient(connection_string)
mydatabase = client["dummy_data"] 
# Create a Flask application instance
app = Flask(__name__)
app.secret_key = 'nithish'
#client = Client("yuva2110/vanilla-charbot")
# Enable CORS for all routes, allowing requests from any origin
CORS(app,resources={r"/*":{"origins":"*"}})

model = pickle.load(open('model.pkl', 'rb'))

# Define a route for handling HTTP GET requests to the root URL
@app.route('/', methods=['GET'])
def get_data():
    data = {
        "message":"API is Running"
    }
    return render_template("/homepage.html")

@app.route("/patient_detail")
def patient_detail():
    print(request.form,request.args.get("detail"))
    try:
        if 'detail' in request.args:
            collection = mydatabase["school"]
            patient_det=collection.find_one({'username':session['username']},{"patient_data":{"$elemMatch":{"pname":request.args.get("detail")}}})
            return render_template("patientdetail.html",patient_det=patient_det['patient_data'][0])
        else:
            return redirect(url_for('patient_data'))
    except:
        return redirect(url_for('patient_data'))
    return redirect(url_for('patient_data'))
@app.route("/report")
def report():
    return render_template("report.html")
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/patient_data")
def patient_data():
    return render_template("patientdata.html")
# Define a route for making predictions

@app.route('/my_notes')
def my_notes():
    return render_template("mynotes.html")

@app.route("/support")
def support():
    return render_template("support.html")

@app.route('/predict', methods=['POST','GET'])
def predict():
    collection = mydatabase["school"]
    try:
        data = request.form
        print(data,data.get("action"),"hi")
        if data.get("action")=="Predict":
            data = request.form.to_dict()  # Convert ImmutableMultiDict to a mutable dict
            data.pop('action', None)
            data.pop('pname',None)
            query_df = pd.DataFrame([data])
            prediction = model.predict(query_df)
            print(prediction)
            prediction_labels = {"0": "No Heart ","1": "Arrhythmia","2": "cardiomyopathy","3": "congenital Heart","4": "Conory Artery" ,"5":"Heart Failure","6":"Valvular Heart "}
    
            # Get the label corresponding to the prediction value
            prediction_text = prediction_labels.get(str(prediction[0]), "Unknown")
             
            result = client.predict(message="Patient have a "+prediction_text+",in 3 lines give some measures to cure this disease",
            system_message="You are a friendly Chatbot.",
            max_tokens=512,
            temperature=0.7,
		    top_p=0.95,
		    api_name="/chat")

            #return jsonify({'Prediction': str(prediction[0])})
            return render_template("/report.html", prediction=prediction_text,cure=result.split('\n'))
        else:
            data = request.form.to_dict()  # Convert ImmutableMultiDict to a mutable dict
            action = data.pop('action', None)
            print(session["username"])
            collection.update_one({"username":session["username"]},{"$push": {"patient_data": data}})
            return render_template("/report.html", prediction="Data have been saved successfully")
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)})
@app.route("/signup_check",methods=['POST','GET'])
def signup_check():
    collection = mydatabase["school"]
    try:
        data = request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if collection.find_one({"username": username}):
         return redirect(url_for('signup'))
        else:
         print(username,password,collection.find_one({"username": username}))
         collection.insert_one({"username": username, "email": email, "password": password})
         session["username"]=username
         print(session["username"])
         return redirect(url_for('report'))

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route("/login_check",methods=['GET','POST'])
def login_check():
    data = request.form
    username = data.get('username')
    password = data.get('password')
    collection = mydatabase["school"]
    user = collection.find_one({"username": username, "password": password})
    print(username,password,user)
    if user:
        session['username']=username
        return redirect(url_for('report'))
    else:
        
        return redirect(url_for('login'))
    
# @app.route("/patient_data",methods=['POST'])
# def patient_data():
#     data = request.json
#     username = data.get("username") 
#     collection = mydatabase["school"]
#     print(collection.update_one({"username":username},{"$push": {"patient_data": data}}))
#     return jsonify({"message": "Patient data inserted successfully"})
# from flask import Flask, request, render_template, session, jsonify
# from pymongo import MongoClient
# from urllib.parse import quote_plus

# MongoDB connection setup
username = quote_plus("nithish")
password = quote_plus("Spike@23")
connection_string = f"mongodb+srv://{username}:{password}@patient-data.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
client = MongoClient(connection_string)
mydatabase = client["dummy_data"]
collection = mydatabase["school"]

# # ap'p = Flask(__name__)
# # app.secret_key = 'nithish

# Route to save notes
@app.route("/save_notes", methods=['POST'])
def save_notes():
    data = request.form
    patient_name = data.get('patient_name')
    patient_details = data.get('patient_details')

    collection.update_one(
        {"username": session["username"]}, 
        {"$push": {"patient_notes": {"patient_name": patient_name, "patient_details": patient_details}}}
    )
    
    return jsonify({'msg': "Notes saved successfully"})

# Route to view notes
@app.route("/view_notes", methods=['GET'])
def view_notes():
    search_patient_name = request.args.get('search_patient_name')
    
    user_data = collection.find_one(
        {"username": session["username"]}, 
        {"patient_notes": {"$elemMatch": {"patient_name": search_patient_name}}}
    )
    
    if user_data and 'patient_notes' in user_data:
        patient_notes = user_data['patient_notes'][0]['patient_details']
        return render_template("mynotes.html", patient_name=search_patient_name, patient_notes=patient_notes)
    else:
        error = "No notes found for the entered patient name."
        return render_template("mynotes.html", error=error)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    