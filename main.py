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
from PyQt5.QtGui import QTextCharFormat, QColor
from PyQt5.QtCore import QDate, QEvent


class CustomCalendarWidget(QCalendarWidget):
    def __init__(self, dates_with_data, parent=None):
        super().__init__(parent)
        self.dates_with_data = set(dates_with_data)
        self.update_calendar()

    def update_calendar(self):
        for i in range(1, 32):
            for j in range(1, 13):
                date = QDate(self.yearShown(), j, i)
                if date.isValid() and date <= QDate.currentDate():
                    if date.toString("yyyy-MM-dd") not in self.dates_with_data:
                        self.setDateTextFormat(date, self.disabled_format())

    def disabled_format(self):
        disabled_format = QTextCharFormat()
        disabled_format.setForeground(QColor("gray"))
        disabled_format.setBackground(QColor(240, 240, 240))
        return disabled_format

    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)
        if date.toString("yyyy-MM-dd") not in self.dates_with_data:
            painter.fillRect(rect, QColor(240, 240, 240))
            text_format = QTextCharFormat()
            text_format.setForeground(QColor("gray"))
            painter.drawText(rect, Qt.AlignCenter, str(date.day()))

    def mousePressEvent(self, event):
        date = self.dateAt(event.pos())
        if date.isValid() and date.toString("yyyy-MM-dd") not in self.dates_with_data:
            event.ignore()
        else:
            super().mousePressEvent(event)


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
        self.canvas_layout = QVBoxLayout()
        self.control_panel_layout = QVBoxLayout()

        self.control_panel_layout = self.create_control_panel()

        self.content_layout.addLayout(self.canvas_layout, 2)
        self.content_layout.addLayout(self.control_panel_layout, 1)

        self.update_display_for_plant(1)

        self.plant_label = QLabel(self.get_plant_label_text())
        self.plant_label.setAlignment(Qt.AlignCenter)
        self.plant_label.setFont(QFont("Arial", 16))
        main_layout.addWidget(self.plant_label)

        main_layout.addLayout(self.content_layout)

        self.plant_buttons_layout = self.create_plant_buttons()
        main_layout.addLayout(self.plant_buttons_layout)

        self.setMinimumSize(800, 600)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_layouts()

    def adjust_layouts(self):
        window_width = self.width()
        if window_width < 800:
            self.plant_buttons_layout.setSpacing(10)
        else:
            self.plant_buttons_layout.setSpacing(20)
        if window_width < 1000:
            self.control_panel_layout.setAlignment(Qt.AlignLeft)
        else:
            self.control_panel_layout.setAlignment(Qt.AlignTop)

    def update_display_for_plant(self, plant):
        today_date = datetime.now().strftime("%Y-%m-%d")
        pcd_path = "Flower.ply"

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
        self.update_display_for_plant(plant)

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

        # Create the calendar widget and add it to the layout
        self.calendar = CustomCalendarWidget(self.application_logic.get_dates_with_data())
        self.calendar.clicked.connect(self.update_display_for_selected_date)
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


    def update_calendar(self):
        dates_with_data = self.application_logic.get_dates_with_data()
        dates_with_data = set(dates_with_data)
        today = QDate.currentDate()

        # Format to indicate disabled dates
        disabled_format = QTextCharFormat()
        disabled_format.setForeground(QColor("gray"))
        disabled_format.setBackground(QColor(240, 240, 240))

        # Disable all dates initially
        for i in range(1, 32):
            for j in range(1, 13):
                date = QDate(today.year(), j, i)
                if date.isValid() and date <= today:
                    self.calendar.setDateTextFormat(date, disabled_format)

        # Enable dates that have data
        for date_str in dates_with_data:
            year, month, day = map(int, date_str.split('-'))
            date = QDate(year, month, day)
            if date.isValid():
                self.calendar.setDateTextFormat(date, QTextCharFormat())

    def update_display_for_selected_date(self):
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        
        self.application_logic.update_sensor_data_from_db(selected_date)

        sensor_data = self.application_logic.get_sensor_data()
        for sensor, data in sensor_data.items():
            self.sensor_data_labels[sensor].setText(f"{sensor}: {data}")

        plant = self.application_logic.get_selected_plant()
        pcd_path = "Flower.ply"

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

    sensor_thread = SensorDataThread()
    sensor_thread.data_updated.connect(app_logic.update_sensor_data_from_db)
    sensor_thread.start()

    sys.exit(app.exec_())
