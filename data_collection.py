import serial
import cv2
import os
import re
import threading
import queue
import numpy as np
import mysql.connector
import time
from datetime import datetime, timedelta

class CNCController:
    def __init__(self, port='COM10', baud_rate=115200, timeout=1):
        self.ser = serial.Serial(port, baud_rate)

    def connect(self):
        time.sleep(5)  # Wait for the connection to establish
        resp = self.ser.readline()
        print(f"First Message: {resp}")
        resp = self.ser.readline()
        print(f"Second Message: {resp}")
        print("Connected to CNC machine.")

    def centerX(self):
        command = "$J=G21G91X-2.5F100\n"
        self.ser.write(command.encode())
        self.poll_idle()
    
    def home(self):
        try:
            self.ser.write(b"$H\n")
            time.sleep(2)
            resp = b""
            while resp.decode("utf-8") != "ok\r\n":
                resp = self.ser.readline()
                print(f"Response Go Home: {resp.decode('utf-8')}")
            print("CNC machine homed.")
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
        

    def setup(self):
        self.ser.write(b"G21\n")  # Set units to millimeters
        self.ser.write(b"G91\n")  # Set to relative positioning
        self.ser.write(b"F500\n")  # Set feed rate to 100 mm/min
        #self.ser.write(b"G0 X0 Y0\n")  # Move to the starting position
        print("CNC machine set up.")

    # def move(self, direction, distance):
    #     command = f"G0 {direction}{distance}\n"
    #     try:
    #         self.ser.write(command.encode())
    #         print(f"Moved {direction} by {distance} mm.")
    #     except serial.SerialException as e:
    #         print(f"Serial communication error: {e}")

    def plant1(self):
        try:
            command = "$J=G21G91Y-3F100\n"
            self.ser.write(command.encode())
            #resp = self.ser.readline()
            #print(f"Plant 1 Pos Y: {resp.decode("utf-8")}")
            #self.move_done()
            #command = "$J=G21G91X-1F100\n"
            self.ser.write(command.encode())
            #resp = self.ser.readline()
            #print(f"Plant 1 Pos X: {resp.decode("utf-8")}")
            #self.move_done()
            print("Moving to Plant 1 done...")
            #self.poll_idle()
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")

    def plant2(self):
        try:
            #command = "$J=G21G91X-3.9F100\n"
            command = "$J=G21G91X-4.5F100\n"
            self.ser.write(command.encode())
            print("Moving to Plant 2 done...")
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
    
    def plant3(self):
        try:
            #command = "$J=G21G91X-3.7F100\n"
            command = "$J=G21G91X-4.3F100\n"
            self.ser.write(command.encode())
            print("Moving to Plant 3 done...")
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")

    def plant4(self):
        try:
            command = "$J=G21G91Y-37F100\n"
            self.ser.write(command.encode())
            print("Moving to Plant 4 done...")
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
    
    def plant5(self):
        try:
            command = "$J=G21G91X4.3F100\n"
            self.ser.write(command.encode())
            print("Moving to Plant 5 done...")
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
    
    def plant6(self):
        try:
            command = "$J=G21G91X4.5F100\n"
            self.ser.write(command.encode())
            print("Moving to Plant 6 done...")
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")

    #moving to diff sides
    def move_side(self):
        try:
            command = "$J=G21G91Z-0.8F100\n"   
            self.ser.write(command.encode())
            resp = self.ser.readline().decode("utf-8")
            print("Moving side done...")
            #self.poll_idle()
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")

    #moving back to def loc
    def move_def(self):
        try:
            command = "$J=G21G91Z2.4F100\n"   
            self.ser.write(command.encode())
            resp = self.ser.readline().decode("utf-8")
            print("Moving to def loc done...")
            #self.poll_idle()
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")

    def poll_idle(self, who):
        try:
            resp = b""
            while not ("Idle" in resp.decode("utf-8")):
                command = "$?\n"
                self.ser.write(command.encode())
                resp = self.ser.readline()
                #print(f"Response: {resp.decode('utf-8')}")
                time.sleep(1)
            self.ser.timeout = 1
            while resp.decode("utf-8") != "":
                resp = self.ser.readline()
                #print(f"Response: {resp.decode('utf-8')}")
            #resp = self.ser.readline()
            print(f"Machine is in IDLE State -- {who}")
            self.ser.timeout = None
            return True
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
            return False

    def move_done(self):
        try:
            #command = "?"
            #self.ser.write(command.encode())
            resp = b""
            while resp.decode("utf-8") != "ok\r\n":
                resp = self.ser.readline()
                print(f"Response: {resp.decode('utf-8')}")
                time.sleep(1)
            return True
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
            return False

        return False

    def disconnect(self):
        self.ser.write(b"$X\n")  # Kill alarm lock if any
        self.ser.write(b"$H\n")  # Move back to the origin
        print("Disconnected from CNC machine.")
        self.ser.close()

class Access_cam:
    def __init__(self,):

        self.capture = False
    
        stream_thread = threading.Thread(target=self.Streaming, args=())
        stream_thread.start()
        
        self.frame = queue.Queue(2)

    def Streaming(self, ):

        cap1 = cv2.VideoCapture(0)
        cap2 = cv2.VideoCapture(1)

        width = int(cap1.get(3))
        height = int(cap1.get(4))

        # Check if the cameras are opened successfully
        if not cap1.isOpened():
            print("Error: Unable to access Camera 0.")
            return

        if not cap2.isOpened():
            print("Error: Unable to access Camera 1.")
            return
        
        while True:
            ret1, frame1 = cap1.read()
            ret2, frame2 = cap2.read()

            dual = np.ones((frame1.shape[0], frame1.shape[1]*2, 3), np.uint8)
            smaller_left = cv2.resize(frame1, (0,0), fx=1, fy=1)
            smaller_right = cv2.resize(frame2, (0,0), fx=1, fy=1)
            dual[:height, :width] = frame1
            dual[:height, width:] = frame2

            # if ret1: #and ret2:
            #     # Display the frame
            #     cv2.imshow('Camera Feed1', frame1)
            #     cv2.imshow('Camera Feed2', frame2)

            cv2.imshow('Camera', dual)
            
            if self.capture:
                self.capture = False
                self.frame.put(frame1)
                self.frame.put(frame2)

            # Check for a key press
            key = cv2.waitKey(1) & 0xFF
            # If 'q' is pressed, exit the loop
            if key == ord('q'):
                break

        cap1.release()
        cap2.release()
        cv2.destroyAllWindows()

    def connect_database(self):
        # Connect to the database
        self.mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Thnksfrthmmrs1234!#",
            database="data_collection"
        )
        self.mycursor = self.mydb.cursor()

    def insert_filename(self, filename):
        # Insert filename into the database
        sql = "INSERT INTO captured_images (filename) VALUES (%s)"
        val = (filename,)
        self.mycursor.execute(sql, val)
        self.mydb.commit()

    def next_available_index(self, output_folder, camera_id, current_date):
        index = 1
        base_filename = f"{current_date}_{camera_id}_{index}.jpg"
        while os.path.exists(os.path.join(output_folder, base_filename)):
            base_filename = f"{current_date}_{camera_id}_{index}.jpg"
            index += 1
        return base_filename
        
    def capture_images(self, output_folder=None):
        self.connect_database()

        self.capture = True
        time.sleep(2)

        frame1 = self.frame.get(block=True)
        frame2 = self.frame.get(block=True)

        current_date = datetime.now().strftime("%Y-%m-%d")
        image_path1 = os.path.join(output_folder, self.next_available_index(output_folder, 'left', current_date))
        cv2.imwrite(image_path1, frame1)
        print(f"Image captured and saved: {image_path1}")
        self.insert_filename(image_path1)

        image_path2 = os.path.join(output_folder, self.next_available_index(output_folder, 'right', current_date))
        cv2.imwrite(image_path2, frame2)
        print(f"Image captured and saved: {image_path2}")
        self.insert_filename(image_path2)
       
def run_collection():
    #================================Plant 1=====================================#
    time.sleep(1)
    cnc_machine.plant1()
    cnc_machine.poll_idle("Move to Plant 1")

    # 1st Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 2nd Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 1")

    # 2nd Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 3rd Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 1")

    # 3rd Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 4th Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 1")

    # 4th Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # Move to default location
    time.sleep(10)
    cnc_machine.move_def()
    cnc_machine.poll_idle("Reset - Plant 1")

    #================================Plant 2=====================================#
    # time.sleep(1)
    cnc_machine.plant2()
    cnc_machine.poll_idle("Move to Plant 2")

    # 1st Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 2nd Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Size - Plant 2")

    # 2nd Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 3rd Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Size - Plant 2")

    # 3rd Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 4th Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 2")

    # 4th Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # Move to default location
    time.sleep(10)
    cnc_machine.move_def()
    cnc_machine.poll_idle("Reset - Plant 2")

    #================================Plant 3=====================================#
    # time.sleep(1)
    cnc_machine.plant3()
    cnc_machine.poll_idle("Move to Plant 3")

    # 1st Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 2nd Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 3")

    # 2nd Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 3rd Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 3")

    # 3rd Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 4th Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 3")

    # 4th Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # Move to default location
    time.sleep(10)
    cnc_machine.move_def()
    cnc_machine.poll_idle("Reset - Plant 3")

    #================================Plant 4=====================================#
    # time.sleep(1)
    cnc_machine.plant4()
    cnc_machine.poll_idle("Move to Plant 4")

    # 1st Set of Pic
    time.sleep(30)
    access_cam.capture_images(output_folder="captured_images")

    # 2nd Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 4")

    # 2nd Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 3rd Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 4")

    # 3rd Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 4th Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 4")

    # 4th Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # Move to default location
    time.sleep(10)
    cnc_machine.move_def()
    cnc_machine.poll_idle("Reset - Plant 4")

    #================================Plant 5=====================================#
    # time.sleep(1)
    cnc_machine.plant5()
    cnc_machine.poll_idle("Move to Plant 5")

    # 1st Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 2nd Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 5")

    # 2nd Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 3rd Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 5")

    # 3rd Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 4th Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 5")

    # 4th Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # Move to default location
    time.sleep(10)
    cnc_machine.move_def()
    cnc_machine.poll_idle("Reset - Plant 5")

    #================================Plant 6=====================================#
    # time.sleep(1)
    cnc_machine.plant6()
    cnc_machine.poll_idle("Move to Plant 6")
    # 1st Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 2nd Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 6")

    # 2nd Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 3rd Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 6")

    # 3rd Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # 4th Side
    time.sleep(10)
    cnc_machine.move_side()
    cnc_machine.poll_idle("Move Side - Plant 6")

    # 4th Set of Pic
    time.sleep(1)
    access_cam.capture_images(output_folder="captured_images")

    # Move to default location
    time.sleep(10)
    cnc_machine.move_def()
    cnc_machine.poll_idle("Reset - Plant 6")

    # Going back to home
    time.sleep(3) 
    cnc_machine.home()

cnc_machine = CNCController(port='COM10')  # Replace with the correct port
cnc_machine.connect()
cnc_machine.home()
time.sleep(1)
access_cam = Access_cam()
time.sleep(1)
#run_collection()

try:
    ser = serial.Serial('COM7', 115200)
    #time.sleep(1)

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Thnksfrthmmrs1234!#",
        database="data_collection"
    )
    mycursor = mydb.cursor()

    print("Waiting for time to start...")
    collection_start = False
    start_time = None
    
    while True:
        now = datetime.now()

        if start_time == None and now.hour == 15 and now.minute == 13: #edit time (now.hour == n), n = 3,6,9,12,15,18, 15 = 3 pm, 18 = 6 pm
            start_time = now
            print("Starting collecting data at 12 AM...")
            #time.sleep(60)

        if start_time is not None and now >= start_time:
        #if now.hour % 4 == 0 and now.minute == 16:
            start_time = start_time + timedelta(hours=3)
            #start_time = start_time + timedelta(minutes=10)
            ser.write(b'r')
            data = ser.readline().decode().strip()
            print("Received data:", data)
            values = data.split(",")
            print(f'Values: {values}')
            if len(values) == 6:
                try:
                    amb_temp, water_temp, ph_value, ec_value, lux_top, lux_bot = map(float, values)
                    mycursor.execute("INSERT INTO sensor_data (amb_temp, water_temp, ph_value, ec_value, lux_top, lux_bot) VALUES (%s, %s, %s, %s, %s, %s)", (amb_temp, water_temp, ph_value, ec_value, lux_top, lux_bot))
                    mydb.commit()
                    #time.sleep(60)
                except ValueError:
                    print("Invalid data format received from Arduino.")
            else:
                print("Number of values error...sss")
            if now.hour == 9 and now.minute >= 0:
                    # Perform CNC movements
                    print("Performing automatic movements...")
                    run_collection()
                    print("Waiting for next collection schedule...")            

except mysql.connector.Error as err:
    print("MySQL error:", err)
except serial.SerialException as err:
    print("Serial port error:", err)
finally:
    if 'mycursor' in locals():
        mycursor.close()
    if 'mydb' in locals():
        mydb.close()
    if 'ser' in locals() and ser.is_open:
        ser.close()
    if 'cnc_machine' in locals():
        cnc_machine.disconnect()




