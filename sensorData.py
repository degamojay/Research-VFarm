import time
from PyQt5.QtCore import QThread, pyqtSignal
import mysql.connector
import serial
from datetime import datetime, timedelta

class SensorDataThread(QThread):
    data_updated = pyqtSignal(str)  # Signal to emit when new data is available

    def run(self):
        try:
            ser = serial.Serial('COM5', 115200)
            time.sleep(1)

            mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Thnksfrthmmrs1234!#",
                database="test"
            )

            mycursor = mydb.cursor()
            start_time = None
            
            while True:
                now = datetime.now()
                if start_time == None and now.hour == 0 and now.minute == 0:
                    start_time = now
                    print("Starting collecting data at 12 AM...")
                    #time.sleep(60)

                if start_time is not None and now >= start_time:
                #if now.hour % 4 == 0 and now.minute == 16:
                    start_time = start_time + timedelta(hours=3)
                    ser.write(b'r')
                    data = ser.readline().decode().strip()
                    print("Received data:", data)
                    values = data.split(",")
                    print(f'Values: {values}')
                    if len(values) == 6:
                        amb_temp, water_temp, ph_value, ec_value, lux_top, lux_bot = map(float, values)
                        try:
                            mycursor.execute("INSERT INTO test (amb_temp, water_temp, ph_value, ec_value, lux_top, lux_bot) VALUES (%s, %s, %s, %s, %s, %s)", (amb_temp, water_temp, ph_value, ec_value, lux_top, lux_bot))
                            mydb.commit()
                            self.data_updated.emit(data)  # Emit signal with new data
                            #time.sleep(60)
                        except ValueError:
                            print("Invalid data format received from Arduino.")
                    else:
                        print("Number of values error...sss")
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
