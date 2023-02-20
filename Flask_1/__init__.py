from flask import Flask, jsonify, request, session, redirect, url_for
import mysql.connector

app = Flask(__name__)

app.secret_key = 'Thinkfinity Labs'

# Connect to the MySQL database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='iot-sub-zero'
)


@app.route("/api/verify_otp", methods=['GET', 'POST'])
def get_data():
    global session
    cursor = conn.cursor()
    session['email'] = request.json["email"]
    session['otp'] = request.json["otp"]

    cursor.execute('SELECT * FROM user_info WHERE uemail = %s AND otp = %s',
                   (session['email'], session['otp']))
    # Fetch one record and return result
    account = cursor.fetchall()
    session['uid'] = account[0]

    # Get the column names
    column_names = [column[0] for column in cursor.description]

    # Combine the column names and the data
    result = [{column_name: row[i] for i, column_name in enumerate(column_names)} for row in account]

    # Return the result as a JSON response
    if account is not None:
        is_valid = True
        return jsonify(result[0]), 200
    else:
        return jsonify({"message": "The provided credentials are invalid"}), 400


@app.route('/api/update_password', methods=['PUT'])
def update_password():
    request_data = request.get_json()
    new_password = request_data.get('new_password')
    confirm_password = request_data.get('confirm_password')

    cursor = conn.cursor()

    uid = session.get('uid')

    # Check if the username exists
    cursor.execute('SELECT * FROM user_info WHERE uid = %s', (uid,))
    user = cursor.fetchone()

    if not user:
        return {'message': 'Invalid User'}, 400

    # Check if the new password and confirm password match
    if new_password != confirm_password:
        return {'message': 'New password and confirm password do not match'}, 400

    # Update the password
    cursor.execute(
        'UPDATE user_info SET upass = %s WHERE uid = %s', (new_password, uid))
    conn.commit()

    return {'message': 'Password updated successfully'}


@app.route("/api/login", methods=['GET', 'POST'])
def login():
    session.pop('uid', None)
    cursor = conn.cursor()
    email = request.json["email"]
    password = request.json["password"]

    cursor.execute(
        'SELECT * FROM user_info WHERE uemail = %s AND upass = %s', (email, password))
    # Fetch one record and return result
    account = cursor.fetchall()

    # Get the column names
    column_names = [column[0] for column in cursor.description]

    # Combine the column names and the data
    result = [{column_name: row[i] for i, column_name in enumerate(column_names)} for row in account]

    session['uid'] = result[0]['uid']

    # Return the result as a JSON response
    if account is not None:
        is_valid = True
        return jsonify(result[0]), 200
    else:
        return jsonify({"message": "The provided credentials are invalid"}), 400

# Route to Show list of devices
@app.route("/api/devices", methods=['GET', 'POST'])
def devices():
    global session
    cursor = conn.cursor()
    uid = session['uid']
    cursor.execute("SELECT * FROM device_info WHERE uid=%s", (uid,))

    # Fetch all record and return result
    devices = cursor.fetchall()

    # Get the column names
    column_names = [column[0] for column in cursor.description]

    # Combine the column names and the data
    result = [{column_name: row[i] for i, column_name in enumerate(column_names)} for row in devices]

    # Return the result as a JSON response
    if devices is not None:
        is_valid = True
        return jsonify(result), 200
    else:
        return jsonify({"message": "Invalid Response"}), 400

# Route to Change Device Name
@app.route("/api/change_name", methods=['GET', 'POST'])
def change_name():
    deviceid = request.json["deviceid"]
    new_name = request.json["new_name"]
    cursor = conn.cursor()

    # Update the device name
    cursor.execute(
        'UPDATE device_info SET dname = %s WHERE deviceid = %s', (new_name, deviceid))
    conn.commit()
    return jsonify({'message': 'Name Succesfully Changed'}), 200

@app.route("/api/device_info", methods=['GET', 'POST'])
def device_info():
    dTemp = request.json["dTemp"]
    temp = request.json["temp"]
    deviceid = request.json["deviceid"]
    cursor = conn.cursor()
    #Set Delta Temprature and Temprature

    cursor.execute('UPDATE device_info SET dt = %s, temp = %s WHERE deviceid = %s', (dTemp, temp, deviceid))
    conn.commit()
    return jsonify({'message': 'Successfully Updated'}), 200


# this will be the logout page
@app.route('/api/logout')
def logout():
    if session.get('uid') != None:
        # Remove session data, this will log the user out
        session.pop('uid', None)
        return jsonify({"message": "Sucessfully Logout"})
    # Redirect to login page
    return redirect(url_for('/api/login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)