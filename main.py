from operator import and_
from flask import Flask, jsonify, abort
from flask import render_template, request, redirect, session, url_for, flash, make_response
from sqlalchemy import ForeignKey, desc, asc
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
from time import sleep
from oauth2client.service_account import ServiceAccountCredentials
from multiprocessing import Process
import pandas as pd
import csv
import uuid
import psutil
import os
import webbrowser
import subprocess
import gspread

path = r'C:\IPFS\file'
if not os.path.exists(path):
  os.makedirs(path)

UPLOAD_FOLDER = path

app = Flask(__name__)
app.secret_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJ1c2VyLTFTTTRSUTlfLS1IVEpGM0QiLCJpYXQiOjE2NjI5ODc0Nzd9.mCvSd2o2vw5Gs7grkBLkW75dlgVcJ-aiqMzfVUvG-q4'
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://kevin:123456@localhost/flask_db'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

class User(db.Model): 
    __tablename__='user'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(40))
    email=db.Column(db.String(40))
    password=db.Column(db.String(40))
    mac=db.Column(db.String(40))


    def __init__(self,name,email,password,mac):
        self.name=name
        self.email=email
        self.password=password
        self.mac=mac
    
  
class Histori(db.Model):
    __tablename__='histori'
    id=db.Column(db.Integer,primary_key=True)
    id_user=db.Column(db.Integer, ForeignKey(User.id))
    username=db.Column(db.String(40))
    date=db.Column(db.Date)
    jam=db.Column(db.String(40))
    status=db.Column(db.Integer)
    keterangan=db.Column(db.String(120))
 
 
  # def __init__(self,id,id_user,file_name,date,file_hash,pin_status):
    def __init__(self,id_user,username,date,jam,status,keterangan):
    # self.id=id
        self.id_user=id_user
        self.username=username
        self.date=date
        self.jam=jam
        self.status=status
        self.keterangan=keterangan


@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register-submit', methods = ['POST'])
def register_submit():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    mac = get_mac_address()

    user = User(name, email, password, mac)
    # db.create_all()
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login-submit', methods = ['POST'])
def login_submit():
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter(and_(User.email == email, User.password == password)).first()
    if user:
        session['user_id'] = user.id
        session['name'] = user.name
        return redirect('/')
    else:
        flash("Gagal login\nEmail atau Password salah")
        return redirect('/login')

@app.route('/admin')
def admin():
    # db.create_all()
    history_data = Histori.query.all()
    # c = history_data.count()
    if 'user_id' in session:
        return render_template('admin.html', histori = history_data)
    else:
        return redirect(url_for('login'))

@app.route('/employee')
def employee():
    emp_data = User.query.all()
    # c = emp_data.count()
    if 'user_id' in session:
        return render_template('employee.html', employee = emp_data)
    else:
        return redirect(url_for('login'))


@app.route('/')
def home():
    try:
        user_data = User.query.filter_by(id=session['user_id']).first().name
    except:
        return redirect(url_for('login'))
    if user_data == "admin":
        return redirect('/admin')
    if isConnected():
        if 'user_id' in session:
            mac_address = get_mac_address()
            now = datetime.now()
            if User.query.filter_by(id=session['user_id']).first().mac == mac_address:    
            # timestamp = now.strftime("%d/%m/%Y %H:%M:%S")
                timestamp = now.strftime("%H:%M:%S")
                return render_template('home.html', user = user_data, time=timestamp, mac=mac_address)
            else:
                return render_template('gagal.html', pesan = "Mac Address Tidak Sesuai!")
        else:
            return redirect(url_for('login'))
    else:
        return render_template('gagal.html', pesan = "Gunakan WIFI Kantor!")
    
@app.route('/absen-datang')
def absen_datang():
    now = datetime.now()
    user = Histori(session['user_id'], session['name'], now.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S"), 1, "masuk")
    db.session.add(user)
    db.session.commit()
    flash("Berhasil Absen Datang")
    return redirect('/')

@app.route('/izin-keluar', methods = ['POST', 'GET'])
def izin_keluar(): 
    if request.method == "POST":  
        now = datetime.now()
        ket = request.form['ket']
        user = Histori(session['user_id'], session['name'], now.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S"), 2, ket)
        db.session.add(user)
        db.session.commit()
        flash("Berhasil Izin")
        return redirect('/')

@app.route('/absen-pulang')
def absen_pulang():
    now = datetime.now()
    hour = int(now.strftime("%H"))
    if hour >= 16:
        user = Histori(session['user_id'], session['name'], now.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S"), 3, "pulang")
        db.session.add(user)
        db.session.commit()
        flash("Berhasil Absen Pulang")
        return redirect('/')
    else:
        flash("Absen pulang baru bisa dilakukan diatas jam 4!")
        return redirect('/')

@app.route('/keluar')
def update():
    return render_template('keluar.html')

@app.route("/logout")
def logout():
    try:
        p2.join()
    except:
        pass
    session.pop("user_id", None)
    return redirect(url_for("login")) 

@app.route("/gagal")
def gagal():
    return render_template('gagal.html') 

@app.route('/delete-history')
def delete_history():
    id_histori = request.args.get('id')
    Histori.query.filter(Histori.id == id_histori).delete()
    db.session.commit()
    return redirect('/admin')

@app.route('/delete-employee')
def delete_employee():
    id_user = request.args.get('id')
    User.query.filter(User.id == id_user).delete()
    db.session.commit()
    return redirect('/employee')

@app.route('/write-csv')
def writecsv():
    records = Histori.query.all()
    a = [[i.id, i.id_user, i.username, i.date.strftime('%d/%m/%Y'), i.jam, i.status, i.keterangan] for i in records]
    
    with open("out.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(['ID histori', 'ID User', 'Nama User', 'Tanggal', 'Jam', 'Status', 'Keterangan'])
        writer.writerows(a)
    
        
    df = pd.read_csv(r'out.csv')
    writer = pd.ExcelWriter(r'file.xlsx', engine='xlsxwriter') 
    df.to_excel(writer, sheet_name='Sheet1', index = None, header=True)
    # read_file.to_excel (r'data.xlsx', index = None, header=True)
    
    for column in df:
        column_length = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        writer.sheets['Sheet1'].set_column(col_idx, col_idx, column_length+8)
    writer.close()

    
    return redirect("/admin")
  
@app.route('/add_review', methods=["POST"])
def add_review():
    req = request.get_json()
    row = [req["email"], req["date"], req["score"]]
    gsheet.insert_row(row, 2)  # since the first row is our title header
    return jsonify(gsheet.get_all_records())

@app.route('/filter-name', methods = ['POST'])
def filter_name():
    name = request.form['fil-name']
    if request.method == "POST":
        his_data = Histori.query.filter_by(username=name).order_by(Histori.date.asc())
        return render_template('admin.html', histori = his_data)

@app.route('/filter-name-fm', methods = ['POST'])
def filter_name_fm():
    name = request.form['fil-name']
    if request.method == "POST":
        his_data = Histori.query.filter_by(username=name).order_by(Histori.date.asc())
        return render_template('admin fm.html', histori = his_data)
    
@app.route('/filter-name-fi', methods = ['POST'])
def filter_name_fi():
    name = request.form['fil-name']
    if request.method == "POST":
        his_data = Histori.query.filter_by(username=name).order_by(Histori.date.asc())
        return render_template('admin fi.html', histori = his_data)  
    
@app.route('/filter-name-fp', methods = ['POST'])
def filter_name_fp():
    name = request.form['fil-name']
    if request.method == "POST":
        his_data = Histori.query.filter_by(username=name).order_by(Histori.date.asc())
        return render_template('admin fp.html', histori = his_data)  

@app.route('/filter-masuk')
def filter_masuk():
    his_data = Histori.query.all()
    return render_template('admin fm.html', histori = his_data)

@app.route('/filter-keluar')
def filter_keluar():
    his_data = Histori.query.all()
    return render_template('admin fi.html', histori = his_data)

@app.route('/filter-pulang')
def filter_pulang():
    his_data = Histori.query.all()
    return render_template('admin fp.html', histori = his_data)

def get_mac_address():
    try:
        # Get a list of all network interfaces on the system
        interfaces = psutil.net_if_addrs()

        for interface_name, interface_addresses in interfaces.items():
            for address in interface_addresses:
                # Check if the address family is MAC address
                if address.family == psutil.AF_LINK:
                    return address.address
    except Exception as e:
        print("Error:", e)
    return None

def isConnected():
    wifi = subprocess.check_output(['netsh', 'WLAN', 'show', 'interfaces'])
    data = wifi.decode('utf-8')
    if "8c:dc:02:9b:cf:9a" in data:
        return True
    else:
        return False

def isConnected2():
    while True:
        wifi = subprocess.check_output(['netsh', 'WLAN', 'show', 'interfaces'])
        data = wifi.decode('utf-8')
        if "8c:dc:02:9b:cf:9a" in data:
            sleep(1)
            print('masuk')
        else:
            print('keluar')
            break
        
    try:
        print('oke')
        user = Histori(session['user_id'], session['name'], now.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S"), 3, "koneksi terputus")
        db.session.add(user)
        db.session.commit()
        return redirect('/')
    except:
        return redirect('/login')
    
if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
    
