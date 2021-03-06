import json
import os
import requests
import pickle
import pandas as pd
import cloudant
import random
from cloudant import Cloudant
from docx import Document
from flask import Flask , request, make_response , render_template, session,g
from sklearn.preprocessing import Imputer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.decomposition import PCA
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey,QueryResult

user= "9ef80d52-30b9-4e45-833a-75059db0825c-bluemix"
password= "79d7c792bb13072da32aecc7dc3777e28780d6d11619795d54d717d2abbd62e5"
host= "9ef80d52-30b9-4e45-833a-75059db0825c-bluemix.cloudant.com"
url = 'https://' + host
client = Cloudant(user, password, url=url, connect=True)    
app = Flask(__name__)
app.config['SECRET_KEY']="QWERTYUIOPASDFGHJKLZXCVBNM"

@app.route('/webhook',methods=['POST'])
def webhook():
    url="https://nwave-ideabot-flask-webhook-p.herokuapp.com/storedata"
    global output
    output={}
    try:
        req=request.get_json(silent=True,force=True)
        sessionId=req.get("sessionId")
        result=req.get("result")
        contexts=result.get("contexts")
        par=contexts[2].get("parameters")
        product=par.get("product")
        srcprotocol=par.get("srcprotocol")
        srcformat=par.get("srcmsgformat")
        targetmsgformat=par.get("targetmsgformat")
        targetprotocol=par.get("targetprotocol")
        associateId=par.get("number-integer")
        operationcount=par.get("operationcount")
        intdataformat=par.get("int-dataformat")
        Interfacetype=par.get("Interface-type")
        rulecount=par.get("rulecount")
        msgfieldcount=par.get("msgfieldcount")
        exposedasapi=par.get("exposed-as-api")
        newexisting=par.get("new-existing")
        dispproduct=par.get("product.original")
        dispsrcF=par.get("srcmsgformat.original")
        dispsrcP=par.get("srcprotocol.original")
        disptargetF=par.get("targetmsgformat.original")
        disptargetP=par.get("targetprotocol.original")
        regop=intRegression(req)
        weightage=regop[0]
        
        op={'sessionId':sessionId,
            'weightage':weightage,
            'product':product,
            'srcprotocol':srcprotocol,
            'srcmsgformat':srcformat,
            'targetmsgformat':targetmsgformat,
            'targetprotocol':targetprotocol,
            'associateId':associateId,
            'operationcount':operationcount, 
            'int-dataformat':intdataformat,
            'Interface-type': Interfacetype,
            'rulecount':rulecount,
            'msgfieldcount':msgfieldcount,
            'exposed-as-api':exposedasapi,
            'new-existing':newexisting,
            'disp-product':dispproduct,
            'disp-srcF':dispsrcF,
            'disp-srcP':dispsrcP,
            'disp-targetF':disptargetF,
            'disp-targetP':disptargetP,
            'feedback':"Not Given",
            'admin-flag':0
           }
        print(op)
        session = client.session()
        print('Username: {0}'.format(session['userCtx']['name']))
        print('Databases: {0}'.format(client.all_dbs()))
        db = client['nwaveoutput']
        doc= db.create_document(op)
        doc.save()
        c_score=regop[1]
        print(doc)
        print(c_score)
        #send_data=requests.post(url,data={'key':weightage,'sessionId':sessionId})
       
        response="Estimated Value:<strong> %s PD<br>Confidence level : </strong> %s Please provide feedback in the effort details pane.<br><i>Do you need estimation for another interface ? <br><button class=\"btn btn-primary\" onclick=\"buttonclick('yes')\">Yes</button>  <button class=\"btn btn-primary\" onclick=\"buttonclick('no')\">No</button> </i>" %(weightage,c_score)
    except:
        response="Sorry Bot has faced an issue! Please try after sometime!"
    
    res= {"speech": response,"displayText": "LOAD-PAGE","source": "nWave-estimation-chatbot"}
    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r
   
def intRegression(req):
    #Machine Learning Model
    dataset = pd.read_excel("https://github.com/Pin2Shaw/Smart-Estimation/blob/master/dataset_integration_v2.xlsx?raw=true",skip_header=1)
    
    Y=dataset.iloc[:, 13:]
    X=dataset.iloc[:,1:13]
    header=list(X)
    imputer = Imputer()
    dataset = imputer.fit_transform(X)
    lr=LinearRegression()
    model_int=lr.fit(X,Y)
    print(model_int.score(X,Y))
    #Data Processing
    val=[]
    result=req.get("result")
    contexts=result.get("contexts")
    print(contexts[0])
    parameters=contexts[0].get("parameters")
    for i in header:
        str=parameters.get(i)
        print("%s %s " %(i,str))
        val.append(str)
    ds=pd.DataFrame(val).T
    print(ds)

    #Prediction
    op_lrt=lr.predict(ds)
    print(op_lrt)
    
    op=[5]
    op=[round(op_lrt[0][0],2),model_int.score(X,Y)]
    print(op)
    return op
    
port = os.getenv('VCAP_APP_PORT', '5000')
if __name__ == "__main__":
       	app.run(host='0.0.0.0', port=int(port), use_reloader=True, debug=True)
