import mysql.connector
from PyQt5.QtCore import QObject, pyqtSignal
from sensorData import SensorDataThread
from datetime import datetime
import random


class ApplicationLogic(QObject):
    data_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.status = "Ready"
        self.selected_plant = 1
        self.sensor_data = {
            "Water Temperature": "No data available",
            "EC Level": "No data available",
            "Ambient Temperature": "No data available",
            "pH Level": "No data available",
            "Lux Top": "No data available",
            "Lux Bottom": "No data available",
        }
        self.sensor_thread = SensorDataThread()
        self.update_sensor_data_from_db()
        today_date = datetime.now().strftime("%Y-%m-%d")
        self.update_sensor_data_from_db(today_date) 
        self.available_dates = self.fetch_dates_with_data()

    def fetch_dates_with_data(self):
        dates_with_data = []
        try:
            mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="12345",
                database="tester"
            )
            mycursor = mydb.cursor()
            query = "SELECT DISTINCT DATE(timestamp) FROM tester.sensor_data"
            mycursor.execute(query)
            dates = mycursor.fetchall()
            dates_with_data = [date[0].strftime("%Y-%m-%d") for date in dates]
        except mysql.connector.Error as e:
            print("MySQL error:", e)
        finally:
            if mycursor:
                mycursor.close()
            if mydb:
                mydb.close()
        return dates_with_data

    def update_sensor_data_from_db(self, selected_date=None):
        try:
            mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="12345",
                database="tester"
            )
            mycursor = mydb.cursor()
            if selected_date:
                query = "SELECT amb_temp, water_temp, ph_value, ec_value, lux_top, lux_bot FROM tester.sensor_data WHERE DATE(timestamp) = %s ORDER BY timestamp DESC LIMIT 1"
                mycursor.execute(query, (selected_date,))
            else:
                mycursor.execute("SELECT amb_temp, water_temp, ph_value, ec_value, lux_top, lux_bot FROM tester.sensor_data ORDER BY timestamp DESC LIMIT 1")
            
            data = mycursor.fetchone()
            if data:
                amb_temp, water_temp, ph_value, ec_value, lux_top, lux_bot = data
                self.sensor_data["Ambient Temperature"] = amb_temp
                self.sensor_data["Water Temperature"] = water_temp
                self.sensor_data["pH Level"] = ph_value
                self.sensor_data["EC Level"] = ec_value
                self.sensor_data["Lux Top"] = lux_top
                self.sensor_data["Lux Bottom"] = lux_bot
                self.data_updated.emit(self.sensor_data)
            else:
                self.sensor_data = {
                    "Water Temperature": "No data available",
                    "EC Level": "No data available",
                    "Ambient Temperature": "No data available",
                    "pH Level": "No data available",
                    "Lux Top": "No data available",
                    "Lux Bottom": "No data available",
                }
                self.data_updated.emit(self.sensor_data)
        except mysql.connector.Error as e:
            print("MySQL error:", e)
        finally:
            if mycursor:
                mycursor.close()
            if mydb:
                mydb.close()

    def get_sensor_data(self):
        return self.sensor_data

    def get_status(self):
        return self.status

    def get_selected_plant(self):
        return self.selected_plant

    def set_selected_plant(self, plant):
        self.selected_plant = plant

    def get_dates_with_data(self):
        return self.available_dates
