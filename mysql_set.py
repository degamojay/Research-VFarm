import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Thnksfrthmmrs1234!#",
    database="data_collection"
)

mycursor = mydb.cursor()

#============creating database============#
#mycursor.execute("CREATE DATABASE tester")
#Note:Change "test" to desired database name

#==========dropping tables================#
#sql = "DROP TABLE sensor_data"
#sql = "DROP TABLE captured_images"

#===========creating tables===============#
mycursor.execute("CREATE TABLE sensor_data (id INT AUTO_INCREMENT PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, amb_temp DECIMAL(4,2), water_temp DECIMAL(4,2), ph_value DECIMAL(4,2), ec_value DECIMAL(4,2), lux_top DECIMAL(6,2), lux_bot DECIMAL(6,2))")

mycursor.execute("CREATE TABLE captured_images (id INT AUTO_INCREMENT PRIMARY KEY, filename TEXT)") 

#=============deleting tables==================#
#mycursor.execute("DELETE FROM captured_images")
#mycursor.execute("DELETE FROM sensor_data")

#=============dropping tables==================#
#mycursor.execute(sql)  

#======== creating and altering================#
mydb.commit()  