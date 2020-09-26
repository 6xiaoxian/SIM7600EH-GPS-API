import RPi.GPIO as GPIO
import serial
import time
import json

ser = serial.Serial('/dev/ttyS0', 115200)
ser.flushInput()

power_key = 6
rec_buff = ''
rec_buff2 = ''
time_count = 0
sent_flag = 1


def send_at(command, back, timeout):
    rec_buff = ''
    ser.write((command + '\r\n').encode())
    time.sleep(timeout)
    if ser.inWaiting():
        time.sleep(0.1)
        rec_buff = ser.read(ser.inWaiting())
    if rec_buff != '':
        if back not in rec_buff.decode():
            print(command + ' ERROR')
            print(command + ' back:\t' + rec_buff.decode())
            return 0
        else:
            print(rec_buff.decode())
            return 1
    else:
        print(command + ' no responce')


def logToFile(msg):
    f = open('gps.info', 'w')
    f.write(msg)
    f.close()


def readFromFile():
    print("Reading")
    f = open('gps.info', 'r')
    data = f.read()
    f.close()
    print("done read")
    return data


def appendToFile(msg):
    print("appending")
    f = open('gps.info', 'a')
    f.write(msg)
    f.write("\n")
    f.close()


def clearFile():
    print("clear")
    f = open('gps.info', 'r+')
    f.truncate(0)
    f.close()


def sendData(message):
    appendToFile(message)
    send_at('AT+HTTPINIT', 'OK', 1)
    storedData = readFromFile()
    data_array = storedData.split('\n')
    print(data_array)
    data_len = len(data_array)
    clearFile()
    for item in data_array:
        print('checkng...')
        if item != '':
            print("1" + '\r\n')
            time.sleep(1)

            send_at(
                'AT+HTTPPARA=\"URL\",\"https://proteus-nvocc.bubbleapps.io/version-test/api/1.1/obj/TrackerDevice?api_token=503c93358648aabae7f2312f4e0a421a\"',
                'OK', 1)
            send_at('AT+HTTPPARA=\"CONTENT\",\"application/json\"', 'OK', 1)
            print('stored Data: ', item)
            send_at('AT+HTTPDATA=' + str(len(item.encode())) + ',5000', 'DOWNLOAD', 1)
            send_at(item, 'OK', 5)
            time.sleep(1)

            rec_buff = ''
            ser.write(('AT+HTTPACTION=1' + '\r\n').encode())
            time.sleep(3)
            rec_buff = ser.read(ser.inWaiting())
            if rec_buff != '':
                if 'OK' not in rec_buff.decode():
                    print(command + ' ERROR')
                    print(command + ' back:\t' + rec_buff.decode())
                    appendToFile(item)
                else:
                    sent_flag = 1;
                    print("sent")
                    print(rec_buff.decode())

            else:
                print('AT+HTTPACTION=1' + ' no responce')
    send_at('AT+HTTPTERM', 'OK', 1)


def get_gps_position():
    gps_status = 0
    rec_null = True
    answer = 0
    gprs_check = 0
    print('Start GPS session...')
    rec_buff = ''
    send_at('AT+CGPS=1,1', 'OK', 1)
    time.sleep(2)
    while rec_null:
        # gprs_flag = send_at('AT+CGPSINFO','+CGPSINFO: ',1)
        ser.write(('AT+CGPSINFO' + '\r\n').encode())
        time.sleep(1)
        if ser.inWaiting():
            time.sleep(0.01)
            rec_buff = ser.read(ser.inWaiting())
        if rec_buff != '':
            if '+CGPSINFO: ' not in rec_buff.decode():
                print(command + ' ERROR')
                print(command + ' back:\t' + rec_buff.decode())
                gps_status = 0
            else:
                print("---- write buffer : ")
                print(rec_buff.decode())
                rec_buff2 = rec_buff.decode()
                gps_status = 1
                if ',,,,,,' not in rec_buff2:
                    print(" ------ get info -------" + '\r\n')
                    start_at = rec_buff2.find(':') + 2
                    end_at = len(rec_buff2) - 1
                    gpsinfo = rec_buff2[start_at:end_at]
                    gps_array = gpsinfo.split(',')
                    print(gps_array)
                    gps_data = gps_array[0] + "," + gps_array[2]
                    print(gps_data)
                    print(">>>")
                    message_json = {"ID": "track-0001", "Location": gps_data}
                    print("message_json", message_json)
                    message = json.dumps(message_json)
                    print(message)
                    sendData(message)
                    gps_status = 1
        else:
            print('GPS is not ready')
            gps_status = 0

        if gps_status == 0:
            print('error')
            rec_buff = ''
            send_at('AT+CGPS=0', 'OK', 1)
            power_down(power_key)
            time.sleep(5)
            power_on(power_key)
            send_at('AT+CGPS=1,1', 'OK', 1)
            # return False
        time.sleep(1.5)


def power_on(power_key):
    print('SIM7600X is starting:')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(power_key, GPIO.OUT)
    time.sleep(0.1)
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(20)
    ser.flushInput()
    print('SIM7600X is ready')


def power_down(power_key):
    print('SIM7600X is loging off:')
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(3)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(18)
    print('Good bye')


try:
    power_on(power_key)
    get_gps_position()
    power_down(power_key)
except:
    if ser != None:
        ser.close()
    power_down(power_key)
    GPIO.cleanup()
if ser != None:
    ser.close()
    GPIO.cleanup()
