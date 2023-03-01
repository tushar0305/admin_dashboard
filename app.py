from asyncio.windows_events import NULL
from flask_mail import Message, Mail
from flask import Flask, flash, request, session, redirect, render_template, jsonify, url_for
from flaskext.mysql import MySQL
from werkzeug.utils import secure_filename
import urllib.request
import pymysql
import random
import string
import os

app = Flask(__name__)
app.secret_key = 'Thinkfinity Labs'
mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_pASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'iot-sub-zero'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# Route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        # Create variables for easy access
        email = request.form['email']
        password = request.form['password']
        cursor.execute(
            'SELECT * FROM admin_info WHERE email = %s AND pass = %s', (email, password))
        # Fetch one record and return result

        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['admin_id'] = account['adminid']
            session['company_name'] = account['cname']
            session['password'] = account['pass']
            session['email'] = account['email']
            flash("Succesfully Loggedout")
            return redirect(url_for('dashboard'))
        else:
            flash("Your account does not exists or you entered wrong password.")

    return render_template('login.html')


@app.route('/')
def home():
    return redirect('/login')


@app.route('/user', methods=['GET', 'POST'])
def user():
    if 'loggedin' in session:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        #Fetching UserID
        if request.method == 'POST' and 'user_selection' in request.form:
            session['userid'] = request.form['user_selection']
            
        fetch_total_devices = cursor.execute("SELECT * FROM device_info WHERE uid = %s",(session['userid']))
        total_devices = fetch_total_devices + 1
        #List of all the devices
        def fetch_devices() -> dict:
            cursor.execute("Select * from device_info WHERE uid = %s", (session['userid']))
            query_results = cursor.fetchall()
            conn.commit()
            device_list = []
            for result in query_results:
                device = {
                    "dname": result['dname'],
                    "deviceid": result['deviceid']
                }
                device_list.append(device)
            return device_list


        #Taking device detail from the user
        if request.method == 'POST' and 'device' in request.form:
            device = request.form['device']
            address = request.form['address']
            city = request.form['city']
            state = request.form['state']
            zip = request.form['zip']
            uid = session.get('userid')
            total_devices = fetch_total_devices + 1
            
            cursor.execute("UPDATE device_info SET uid=%s, address=%s, city=%s, state=%s, pincode=%s WHERE deviceid = %s",
                        (uid, address, city, state, zip, device))
            conn.commit()

            cursor.execute("UPDATE user_info SET totaldev=%s WHERE uid = %s",
                        (total_devices, session['userid']))
            conn.commit()

        # Attach devices with particular user
        def fetch_attach_devices() -> dict:
            cursor.execute(
                'Select * from device_info where uid = %s', (session.get('userid')))
            query_results = cursor.fetchall()
            conn.commit()
            attach_device_list = []
            for result in query_results:
                attach_device = {
                    "dname": result['dname'],
                    "mstate": result['mstate'],
                }
                attach_device_list.append(attach_device)
            return attach_device_list
            
        return render_template('user.html', company_name=session['company_name'], device=fetch_devices(), attach_device=fetch_attach_devices())


@app.route('/profile')
def profile():
    if 'loggedin' in session:
        return render_template('profile.html', company_name=session['company_name'])


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'loggedin' in session:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        adminid = session['admin_id']
        total_user = cursor.execute("SELECT * FROM user_info WHERE uid != '0' and adminid = %s",(adminid))
        total_devices = cursor.execute("SELECT * FROM device_info WHERE deviceid != '0' and adminid = %s",(adminid))
        new_devices = cursor.execute("SELECT * FROM device_info WHERE uid = '0' and adminid = %s",(adminid))
        start = cursor.execute("SELECT * FROM device_info WHERE dstate = '1' and adminid = %s",(adminid))
        stop = cursor.execute("SELECT * FROM device_info WHERE dstate = '0' and adminid = %s",(adminid))


        def fetch_users() -> dict:
            cursor.execute(
                'Select * from user_info where adminid = %s', (session.get('admin_id')))
            query_results = cursor.fetchall()
            conn.commit()
            user_list = []
            for result in query_results:
                user = {
                    "uname": result['uname'],
                    "uid": result['uid'],
                    "totaldev": result['totaldev'],
                    "uemail": result['uemail'],
                    "upass": result['upass'],
                    "uphone": result['uphone'],
                }
                user_list.append(user)

            return user_list
        users = fetch_users()
        return render_template('index.html', start=start, stop=stop, new_devices=new_devices, company_name=session['company_name'], total_user=total_user, total_devices=total_devices, user=users)


@app.route('/devices', methods=['GET', 'POST'])
def devices():
    if 'loggedin' in session:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        adminid = session['admin_id']
        sold = "0"

        # Fetching Sold Devices List
        def fetch_sold_devices() -> dict:
            cursor.execute('Select * from device_info where uid != %s and adminid = %s', (sold, adminid))
            query_results = cursor.fetchall()
            conn.commit()
            device_list = []
            for result in query_results:
                device = {
                    "dname": result['dname'],
                    "deviceid": result['deviceid'],
                    "mstate": result['mstate'],
                }
                device_list.append(device)
            return device_list

        # Fetching UnSold Devices List
        def fetch_unsold_devices() -> dict:
            cursor.execute('Select * from device_info where uid = %s and adminid = %s', (sold, adminid))
            query_results = cursor.fetchall()
            conn.commit()
            device_list = []
            for result in query_results:
                device = {
                    "dname": result['dname'],
                    "deviceid": result['deviceid'],
                }
                device_list.append(device)
            return device_list

        if request.method == 'POST' and 'state' in request.form:
            state = request.form['state']
            deviceid = request.form['deviceid']
            cursor.execute("UPDATE device_info SET mstate=%s WHERE deviceid = %s",
                        (state, deviceid))
            conn.commit()


        return render_template('devices.html', company_name=session['company_name'], sold=fetch_sold_devices(), unsold=fetch_unsold_devices())


@app.route('/adduser', methods=['GET', 'POST'])
def adduser():
    if 'loggedin' in session:
        adminid = session['admin_id']
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        if request.method == 'POST' and 'name' in request.form and 'email' in request.form and request.form.get("name") != "":
            # Create variables for easy access
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            address = request.form['address']
            city = request.form['city']
            state = request.form['state']
            zip = request.form['zip']
            id = id_generator()
            otp = str(otp_generator(6))

            total_user = cursor.execute("SELECT * FROM user_info WHERE uid != '0' and adminid = %s",(adminid))

            cursor.execute('INSERT INTO user_info VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                           (id, name, adminid, 0, email, NULL, phone, otp, address, city, state, zip))
            
            cursor.execute('UPDATE admin_info SET tuser = %s WHERE adminid = %s', (total_user + 1, adminid))

            conn.commit()


            msg = Message(
                "Verification code", sender="Thinkfinitylabs@gmail.com", recipients=[email])
            msg.body = "Here is your verification code : " + otp
            mail.send(msg)
        return render_template('adduser.html', company_name=session['company_name'])


@app.route('/adddevice', methods=['GET', 'POSt'])
def adddevice():
    if 'loggedin' in session:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        if request.method == 'POST' and 'dname' in request.form and 'deviceid' in request.form:
            # Create variables for easy access
            dname = request.form['dname']
            deviceid = request.form['deviceid']
            adminid = session['admin_id']

            total_devices = cursor.execute("SELECT * FROM device_info WHERE deviceid != '0' and adminid = %s",(adminid))

            cursor.execute('INSERT INTO device_info VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                           (adminid, NULL, deviceid, dname, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL))
            
            cursor.execute('Update admin_info SET tdevices = %s WHERE adminid = %s', (total_devices + 1, adminid))
            conn.commit()
        return render_template('add-device.html', company_name=session['company_name'])


@app.route('/userlist', methods=['GET', 'POST'])
def userlist():
    if 'loggedin' in session:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        adminid = session.get('admin_id')
        cursor.execute(
            'Select * from admin_info where adminid = %s', (adminid))
        user = cursor.fetchone()
        conn.commit()
        total_user = user['tuser']

        def fetch_users() -> dict:
            cursor.execute(
                'Select * from user_info where adminid = %s', (adminid))
            query_results = cursor.fetchall()
            conn.commit()
            user_list = []
            for result in query_results:
                user = {
                    "uname": result['uname'],
                    "uid": result['uid'],
                    "totaldev": result['totaldev'],
                    "uemail": result['uemail'],
                    "upass": result['upass'],
                    "uphone": result['uphone'],
                }
                user_list.append(user)

            return user_list
        session['users'] = fetch_users()
        return render_template('user-list.html', company_name=session['company_name'], total_user=total_user, user=session['users'])


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if 'loggedin' in session:
        return render_template('contact.html', company_name=session['company_name'])


@app.route('/logout')
def logout():
    if 'loggedin' in session:
        # Remove session data, this will log the user out
        session.pop('loggedin', None)
        # Redirect to login page
        return redirect(url_for('login'))

# Route for Master login page
@app.route('/master_login', methods=['GET', 'POST'])
def master_login():
    logout()
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        # Create variables for easy access
        session['loggedin'] = True
        email = request.form['email']
        password = request.form['password']

        if email=="thinkfinitylabs@gmail.com" and password=='123':
            return redirect(url_for('advance'))
        else:
            flash("Your account does not exists or you entered wrong password.")

    return render_template('master-login.html')

# Route for Master admin page
@app.route('/advance', methods=['GET', 'POST'])
def advance():
    if 'loggedin' in session:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        if request.method == 'POST' and 'name' in request.form:
            # Create variables for easy access
            cname = request.form['name']
            email = request.form['email']
            password = request.form['pass']
            phone = request.form['phone']
            address = request.form['address']
            city = request.form['city']
            state = request.form['state']
            zip = request.form['zip']
            adminid = id_generator()

            cursor.execute('INSERT INTO user_info VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                           (adminid, cname, password, email, phone, NULL, NULL, NULL, address, city, state, zip))
            conn.commit()

        return render_template('advance-setting.html')

@app.route('/company_list')
def company():
    if 'loggedin' in session:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        def fetch_companies() -> dict:
            cursor.execute('Select * from admin_info')
            query_results = cursor.fetchall()
            conn.commit()
            company_list = []
            for result in query_results:
                company = {
                    "name": result['cname'],
                    "totaldev": result['tdevices'],
                    "tuser": result['tuser'],
                    "email": result['amail'],
                }
                company_list.append(company)

            return company_list
        company = fetch_companies()
        return render_template('company-list.html', company=company)

def id_generator(size=16, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# function to generate otp of random digit

def otp_generator(size):
    range_start = 10**(size-1)
    range_end = (10**size)-1
    return random.randint(range_start, range_end)
