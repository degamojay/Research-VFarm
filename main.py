import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QGridLayout
from PyQt5.QtWidgets import QCalendarWidget, QHBoxLayout, QGroupBox, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5 import QtGui, QtCore
import open3d as o3d
import win32gui
from application_logic import ApplicationLogic
from sensorData import SensorDataThread
from volumetricRepresentation import VolumetricRepresentation
from PyQt5.QtCore import pyqtSlot
import mysql.connector
from PyQt5.QtCore import QDate

class App(QMainWindow):
    def __init__(self, application_logic):
        super().__init__()
        self.application_logic = application_logic
        self.setWindowTitle("Volumetric Visualization")
        self.setGeometry(100, 100, 1200, 800)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)

        header_label = QLabel("Volumetric Visualization", self)
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setFont(QFont("Arial", 20, QFont.Bold))
        main_layout.addWidget(header_label)

        self.content_layout = QHBoxLayout()
        self.canvas_layout = QVBoxLayout()  # Layout for the 3D model viewer
        self.control_panel_layout = QVBoxLayout()  # Layout for control panel

        self.control_panel_layout = self.create_control_panel()

        self.content_layout.addLayout(self.canvas_layout, 2)  # Set canvas layout with larger stretch factor
        self.content_layout.addLayout(self.control_panel_layout, 1)  # Set control panel layout with smaller stretch factor

        self.update_display_for_plant(1)  # Initialize with plant 1

        self.plant_label = QLabel(self.get_plant_label_text())
        self.plant_label.setAlignment(Qt.AlignCenter)
        self.plant_label.setFont(QFont("Arial", 16))
        main_layout.addWidget(self.plant_label)

        main_layout.addLayout(self.content_layout)

        self.plant_buttons_layout = self.create_plant_buttons()  # Assign layout to class attribute
        main_layout.addLayout(self.plant_buttons_layout)

        self.setMinimumSize(800, 600)  # Set minimum size to maintain responsiveness

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_layouts()

    def adjust_layouts(self):
        # Adjust layout sizes and alignments based on window size
        window_width = self.width()

        if window_width < 800:
            # Adjust plant buttons layout for smaller window width
            self.plant_buttons_layout.setSpacing(10)
        else:
            # Adjust plant buttons layout for larger window width
            self.plant_buttons_layout.setSpacing(20)

        # Adjust control panel layout alignment based on window width
        if window_width < 1000:
            self.control_panel_layout.setAlignment(Qt.AlignLeft)
        else:
            self.control_panel_layout.setAlignment(Qt.AlignTop)

    def update_display_for_plant(self, plant):
        today_date = datetime.now().strftime("%Y-%m-%d")
        pcd_path = "Flower.ply"
        #pcd_path = os.path.join(os.path.dirname(__file__), 'captured_images', f"{today_date}_left_{plant}.ply")

        # Clear previous widgets in the canvas layout
        for i in reversed(range(self.canvas_layout.count())):
            widget_to_remove = self.canvas_layout.itemAt(i).widget()
            if widget_to_remove:
                self.canvas_layout.removeWidget(widget_to_remove)
                widget_to_remove.setParent(None)
                widget_to_remove.deleteLater()

        if os.path.exists(pcd_path):
            self.create_3d_viewer(pcd_path)
        else:
            no_data_label = QLabel(f"No 3D model found for Plant {plant} today")
            no_data_label.setAlignment(Qt.AlignCenter)
            self.canvas_layout.addWidget(no_data_label)

    def create_3d_viewer(self, pcd_path):
        pcd = o3d.io.read_point_cloud(pcd_path)
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window()
        self.vis.add_geometry(pcd)

        hwnd = win32gui.FindWindowEx(0, 0, None, "Open3D")
        self.window = QtGui.QWindow.fromWinId(hwnd)
        self.windowcontainer = self.createWindowContainer(self.window, self)
        self.canvas_layout.addWidget(self.windowcontainer)

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_vis)
        timer.start(1)

    def update_vis(self):
        self.vis.poll_events()
        self.vis.update_renderer()

    def get_plant_label_text(self):
        return f"Plant {self.application_logic.get_selected_plant()}"

    def create_plant_buttons(self):
        plant_buttons_layout = QHBoxLayout()
        plant_buttons_layout.setAlignment(Qt.AlignLeft)
        plant_buttons_layout.setSpacing(20)

        self.plant_buttons = []

        for i in range(1, 7):
            plant_button = QPushButton(f"Plant {i}")
            plant_button.setMinimumSize(125, 20)
            plant_button.clicked.connect(lambda checked, plant=i: self.on_plant_button_clicked(plant))
            plant_buttons_layout.addWidget(plant_button)
            self.plant_buttons.append(plant_button)

        return plant_buttons_layout

    def on_plant_button_clicked(self, plant):
        self.application_logic.set_selected_plant(plant)
        self.plant_label.setText(self.get_plant_label_text())
        self.update_display_for_plant(plant)  # Update the display for the selected plant

    def create_control_panel(self):
        control_panel_layout = QVBoxLayout()
        control_panel_layout.setAlignment(Qt.AlignTop)
        control_panel_layout.setSpacing(5)

        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel(self.application_logic.get_status())
        self.status_label.setAlignment(Qt.AlignCenter)
        font = self.status_label.font()
        font.setPointSize(10)
        self.status_label.setFont(font)
        status_layout.addWidget(self.status_label)
        control_panel_layout.addWidget(status_group)

        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self.update_display_for_selected_date)  # Connect clicked signal
        control_panel_layout.addWidget(self.calendar)

        sensor_data_group = QGroupBox("Sensor Data")
        sensor_data_layout = QVBoxLayout(sensor_data_group)
        self.sensor_data_labels = {}

        for sensor, data in self.application_logic.get_sensor_data().items():
            sensor_label = QLabel(f"{sensor}: {data}")
            sensor_label.setStyleSheet("QLabel { margin-bottom: 30px; }")
            font = sensor_label.font()
            font.setPointSize(10)
            sensor_label.setFont(font)
            sensor_data_layout.addWidget(sensor_label)
            self.sensor_data_labels[sensor] = sensor_label

        spacer_item = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        sensor_data_layout.addItem(spacer_item)

        control_panel_layout.addWidget(sensor_data_group)

        return control_panel_layout

    def update_display_for_selected_date(self):
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        
        # Fetch the last sensor data for the selected date from the database
        self.application_logic.update_sensor_data_from_db(selected_date)

        # Update the sensor data labels in the GUI
        sensor_data = self.application_logic.get_sensor_data()
        for sensor, data in sensor_data.items():
            self.sensor_data_labels[sensor].setText(f"{sensor}: {data}")

        # Update the 3D model display
        plant = self.application_logic.get_selected_plant()
        pcd_path = "Flower.ply"
        #pcd_path = os.path.join(os.path.dirname(__file__), 'captured_images', f"{selected_date}_left_{plant}.ply")

        # Clear previous widgets in the canvas layout
        for i in reversed(range(self.canvas_layout.count())):
            widget_to_remove = self.canvas_layout.itemAt(i).widget()
            if widget_to_remove:
                self.canvas_layout.removeWidget(widget_to_remove)
                widget_to_remove.setParent(None)
                widget_to_remove.deleteLater()

        if os.path.exists(pcd_path):
            self.create_3d_viewer(pcd_path)
        else:
            no_data_label = QLabel(f"No 3D model found for Plant {plant} on {selected_date}")
            no_data_label.setAlignment(Qt.AlignCenter)
            self.canvas_layout.addWidget(no_data_label)


if __name__ == "__main__":
    app_logic = ApplicationLogic()
    app = QApplication(sys.argv)
    window = App(app_logic)
    window.show()

    # Start the sensor data collection thread
    sensor_thread = SensorDataThread()
    sensor_thread.data_updated.connect(app_logic.update_sensor_data_from_db)  # Corrected signal-slot connection
    sensor_thread.start()

    sys.exit(app.exec_())
