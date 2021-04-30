import datetime
import json
import serial
import MySQLdb
from flask import Flask, render_template, make_response

app = Flask (__name__)

ledpins = {
    3: {'name' : 'Table Lamp Red', 'state' : 0},
    4: {'name' : 'Table Lamp Green', 'state' : 0},
    5: {'name' : 'Table Lamp BLUE', 'state' : 0},
    6: {'name' : 'Light', 'state' : 0}
}

status = {
    1: {'name' : 'Room', 'state' : 0},
    2: {'name' : 'PIR', 'state' : 0},
    3: {'name' : 'Lighting Mode', 'state' : 4},
    4: {'name' : 'LDR', 'state' : 0},
    5: {'name' : 'light level', 'state' : 50},
    6: {'name' : 'light colour', 'state' : 0}
}

user = {
    0:{'name' : 'NO USER', 'state' : 1},
    1:{'name' : 'LAI KOK WUI', 'state' : 0}
}

dbConn = MySQLdb.connect("localhost","pi","","sr_db") or dle("Could not connect to database")
cursor = dbConn.cursor()

@app.route('/')
def index():
    templateData = {
        'ledpins' : ledpins,
        'status' : status,
        'user' : user
    }
    return render_template('index.html', **templateData)


@app.route('/ldrdata', methods=["GET", "POST"])
def LDR_Data():
    if ser.in_waiting > 0: # check any in coming serial message
        line = ser.readline() # read the serial message
        print("Serial Meassage: ",line) # print it out to terminal
        info = line.split(",") # split the the message into a list
        
        if len(info) > 6: # if the length of the serial message is more than 6 it will proceed
            RFID(info[0]) # RFID Check
            SoundModule(info[3]) # sound module
            
            # fill username with all the people that is inside the room
            username = "" # reset username
            for users in user:
                if user[users]['state'] == 1:
                    username += user[users]['name']    
            
            # Insert data into database
            insert_statement = "INSERT INTO SRLOG (RFID,USERNAME,LDR,PIR,SM,LAMP_STATUS,LIGHT_STATUS,ROOM_STATUS,DT) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            data = (info[0],username,info[1],info[2],info[3],info[4],info[5],status[1]['state'],datetime.datetime.now())
            cursor.execute(insert_statement, data)
            dbConn.commit()
            
            # show room status, lighting mode, user now
            print("Room Status: ",status[1]['state'])
            print("Lighting Mode: ",status[3]['state'])
            print("User in The Room: ", username)
    
        # get last ldr value
        cursor.execute("SELECT * FROM SRLOG ORDER BY id DESC LIMIT 1")
        data = cursor.fetchall()
        dbConn.commit()
        
        status[1]['state'] = int(data[0][8]) # room status
        status[2]['state'] = int(data[0][4]) # PIR sensor state
        status[4]['state'] = int(data[0][3]) # LDR state
        
        MotionSensor() # check for motion
        CheckLightingMode() # check lighting mode and perform tasks
        
        # send ldr value to index.html uing json format
        response = make_response(json.dumps(status[4]['state']))
        response.content_type = 'application/json'
        return response


def MotionSensor():
    if status[3]['state'] == 3: # Check motion and turn on table lamp on lighting mode 3
        # Check PIR state is 1 and Room State is 1 and Light level is under light level conditional rule
        if ((status[1]['state'] == 1) and (status[2]['state'] == 1) and (status[4]['state'] < status[5]['state'])):
            ser.write(b"lamp on\n") # send command to turn lamp on
            LampState(1, 1, 1) # change lamp state to 1
        else:
            ser.write(b"lamp off\n") # send command to turn lamp off
            LampState(0, 0, 0) # change lamp state to 0
    

def RFID(card):
    if "NO CARD" not in card: # if card is detected
        if "F7 B2 F7 D8" in card: # if card id is F7 B2 F7 D8
            ser.write(b"buzzer success\n") # buzzer success
            if status[1]['state'] == 0: # if room_status is 0
                status[1]['state'] = 1 # room status turn 1
                status[3]['state'] = 0 # lighting mode turn to 0
                user[0]['state'] = 0 # no user state turn 0
                user[1]['state'] = 1 # user Lai Kok Wui state turn 1
            else:
                status[1]['state'] = 0 # room status turn 0
                status[3]['state'] = 4 # lighting mode turn 4
                user[0]['state'] = 1 # no user status turn 1
                user[1]['state'] = 0 # user Lai Kok Wui state turn 0
        else: # if it is unknown card
            ser.write(b"buzzer fail\n") # buzzer fail
            

def SoundModule(sm):
    if status[1]['state'] == 1: # if room status is 1
        if sm == "1": # if clapping sound detected
            if status[3]['state'] < 4: # if lighting mode is 1, 2 or 3
                status[3]['state'] += 1 # shift to next ighting mode
            else: # else turn the lighting mode to 0
                status[3]['state'] = 0
            

def CheckLightingMode():
    if status[3]['state'] == 0:
        # send two serial commands to turn on lights and than turn off lamp
        ser.write(b"light on\n")
        ser.write(b"lamp off\n")
        LampState(0, 0, 0) # set lamp state to off
        ledpins[6]['state'] = 1 # set lights state to on
    if status[3]['state'] == 1:
        # send two serial commands to turn on lights and than turn on lamp
        ser.write(b"light on\n")
        ser.write(b"lamp on\n")
        LampState(1, 1, 1) # set lamp state to on
        ledpins[6]['state'] = 1 # set lights state to on
    if status[3]['state'] == 2:
        # send two serial commands to turn off lights and than turn on lamp
        ser.write(b"light off\n")
        ser.write(b"lamp on\n")
        LampState(1, 1, 1) # lamp state on
        ledpins[6]['state'] = 0 # lights state off
    if status[3]['state'] == 3:
        ser.write(b"light off\n") # send one serial command to turn off lights
        ledpins[6]['state'] = 0 # set light state to off
        if status[1]['state'] == 0: # if the room status is 0
            ser.write(b"lamp off\n") # send one serial command to turn off lamp
            LampState(0, 0, 0) # set lamp state to off
    if status[3]['state'] == 4:
        # send two serial commands to turn off lights and than turn off lamp
        ser.write(b"light off\n")
        ser.write(b"lamp off\n")
        LampState(0, 0, 0) # set lamp state to off
        ledpins[6]['state'] = 0 # set light state to on
        
        
def ChangeColor():
    if (status[3]['state'] == 1) or (status[3]['state'] == 2): # check lighting mode is 1 or 2
        ser.write(b"lamp on\n") # send a serial command to change the colour immediately

def LampState(ledpin3, ledpin4, ledpin5):
    ledpins[3]['state'] = ledpin3
    ledpins[4]['state'] = ledpin4
    ledpins[5]['state'] = ledpin5


@app.route("/<Input>")
def ChangeLightingMode(Input):
    if Input == 'LightingMode0':
        status[3]['state'] = 0 # set lighting mode to 0
    if Input == 'LightingMode1':
        status[3]['state'] = 1 # set lighting mode to 1
    if Input == 'LightingMode2':
        status[3]['state'] = 2 # lighting mode set to 2
    if Input == 'LightingMode3':
        status[3]['state'] = 3 # set lighting mode to 3
    if Input == 'LightingMode4': 
        status[3]['state'] = 4 # set lighting mode to 4
    if Input == 'LightLevel50':
        status[5]['state'] = 50 # set light level conditional rule to 50
    if Input == 'LightLevel100':
        status[5]['state'] = 100 # set light level conditional rule to 100
    if Input == 'LightLevel150':
        status[5]['state'] = 150 # set light level conditional rule to 150
    if Input == 'LightLevel200':
        status[5]['state'] = 200 # set light level conditional rule to 200
    if Input == 'LightColourWhite':
        ser.write(b"white\n") # send a serial command to change lamp colour to white
        status[6]['state'] = 0 # light colour state set to 0
        ChangeColor()
    if Input == 'LightColourRed':
        ser.write(b"red\n") # send a serial command to change lamp colour to red
        status[6]['state'] = 1 # light colour state set to 1
        ChangeColor()
    if Input == 'LightColourGreen':
        ser.write(b"green\n") # send a serial command to change lamp colour to green
        status[6]['state'] = 2 # light colour state set to 2
        ChangeColor()
    if Input == 'LightColourBlue':
        ser.write(b"blue\n") # send a serial command to change lamp colour to blue
        status[6]['state'] = 3 # light colour state set to 3
        ChangeColor()
    if Input == 'LightColourCyan':
        ser.write(b"cyan\n") # send a serial command to change lamp colour to cyan
        status[6]['state'] = 4 # light colour state set to 4
        ChangeColor()
    if Input == 'LightColourYellow':
        ser.write(b"yellow\n") # send a serial command to change lamp colour to yellow
        status[6]['state'] = 5 # light colour state set to 5
        ChangeColor()
    
    CheckLightingMode() # check lighting mde and perform tasks
        
    templateData = { 
        'ledpins' : ledpins,
        'status' : status,
        'user' : user
    }
    return render_template('index.html', **templateData)


if __name__ == "__main__":
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    ser.flush()
    app.run(host='0.0.0.0', port = 80, debug = True)
    cursor.close()