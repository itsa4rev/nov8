import sys
import socket
import struct
import math
import threading
import numpy as np
#import mplcursor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton,
                             QWidget, QLabel, QHBoxLayout)
from PyQt5.QtCore import Qt
import csv

# Update the format string to include all required fields
FORMAT = "fffffffffffffff"  # Adjust this according to your actual data structure

class UDPReceiver(threading.Thread):
    def __init__(self, udp_ip, udp_port, callback):
        super().__init__()
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        self.callback = callback
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.udp_ip, self.udp_port))
        self.data = []
        self.running = True

    def run(self):
        print(f"Listening for UDP packets on {self.udp_ip}:{self.udp_port}...")
        try:
            while self.running:
                packed_data, _ = self.sock.recvfrom(1024)  # Size of the buffer
                unpacked_data = struct.unpack(FORMAT, packed_data)
                x, y, z, xv, yv, zv, source, trk_no, types, time, latitude, longitude, altitude, speed, hdng = unpacked_data
                print(f"Received data: {x}, {y}, {z}, {xv}, {yv}, {zv}, {source}, {trk_no}, {types}, {time}, "
                      f"{latitude}, {longitude}, {altitude}, {speed}, {hdng}")
                
                self.data.append((x, y,z))
                self.callback(self.data)
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.sock.close()

    def stop(self):
        self.running = False
        self.join()

class RadarGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Radar System GUI")
        self.setGeometry(100, 100, 800, 600)
        self.data = []
        self.udp_receiver = None  # To hold the UDPReceiver instance
        self.plot_type = 'PPI'  # Default mode is PPI
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Setup Matplotlib figure and canvas
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Buttons for different radar modes
        self.mode_layout = QHBoxLayout()

        self.ppi_button = QPushButton("PPI")
        self.ppi_button.clicked.connect(self.select_ppi_mode)
        self.mode_layout.addWidget(self.ppi_button)

        self.rhi_button = QPushButton("RHI")
        self.rhi_button.clicked.connect(self.select_rhi_mode)
        self.mode_layout.addWidget(self.rhi_button)

        self.bscope_button = QPushButton("BSCOPE")
        self.bscope_button.clicked.connect(self.select_bscope_mode)
        self.mode_layout.addWidget(self.bscope_button)

        self.cscope_button = QPushButton("CSCOPE")
        self.cscope_button.clicked.connect(self.select_cscope_mode)
        self.mode_layout.addWidget(self.cscope_button)

        self.time_vs_range_button = QPushButton("Time vs Range")
        self.time_vs_range_button.clicked.connect(self.select_time_vs_range)
        self.mode_layout.addWidget(self.time_vs_range_button)

        self.time_vs_azimuth_button = QPushButton("Time vs Azimuth")
        self.time_vs_azimuth_button.clicked.connect(self.select_time_vs_azimuth)
        self.mode_layout.addWidget(self.time_vs_azimuth_button)

        self.time_vs_elevation_button = QPushButton("Time vs Elevation")
        self.time_vs_elevation_button.clicked.connect(self.select_time_vs_elevation)
        self.mode_layout.addWidget(self.time_vs_elevation_button)

        self.layout.addLayout(self.mode_layout)

        self.start_receiving()  # Start receiving UDP data immediately

    def start_receiving(self):
        if not self.udp_receiver or not self.udp_receiver.is_alive():
            self.udp_receiver = UDPReceiver('127.0.0.1', 5005, self.update_plot)
            self.udp_receiver.start()
            print("Started receiving data...")

    def update_plot(self, data):
        print(f"Updating plot with {len(data)} data points.")
        if self.plot_type == 'PPI':
            self.plot_ppi(data)
        elif self.plot_type == 'RHI':
            self.plot_rhi(data)
        elif self.plot_type == 'BSCOPE':
            self.plot_bscope(data)
        elif self.plot_type == 'CSCOPE':
            self.plot_cscope(data)
        elif self.plot_type == 'Time vs Range':
            self.plot_time_vs_range(data)
        elif self.plot_type == 'Time vs Azimuth':
            self.plot_time_vs_azimuth(data)
        elif self.plot_type == 'Time vs Elevation':
            self.plot_time_vs_elevation(data)

    def plot_ppi(self, data):
        """ Plan Position Indicator (PPI) mode """
        self.ax.clear()
        x_values = [d[0] for d in data]  # X
        y_values = [d[1] for d in data]  # Y
        self.ax.scatter(x_values, y_values, c='blue')
        self.ax.set_title("PPI Mode")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.canvas.draw()

    def plot_rhi(self, data):
        """ Range Height Indicator (RHI) mode """
        self.ax.clear()
        x_values = [d[0] for d in data]  # X
        z_values = [d[2] for d in data]  # Z
        self.ax.plot(x_values, z_values, 'r')
        self.ax.set_title("RHI Mode")
        self.ax.set_xlabel("Range (X)")
        self.ax.set_ylabel("Height (Z)")
        self.canvas.draw()

    def plot_bscope(self, data):
        """ B-Scope mode """
        self.ax.clear()
        x_values = [d[0] for d in data]  # X
        y_values = [d[1] for d in data]  # Y
        self.ax.plot(x_values, y_values, 'g')
        self.ax.set_title("BSCOPE Mode")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.canvas.draw()

    def plot_cscope(self, data):
        """ C-Scope mode """
        self.ax.clear()
        x_values = [d[0] for d in data]  # X
        y_values = [d[1] for d in data]  # Y
        z_values = [d[2] for d in data]  # Z
        self.ax.scatter(x_values, y_values, c=z_values, cmap='viridis')
        self.ax.set_title("CSCOPE Mode")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.canvas.draw()

    def plot_time_vs_range(self, data):
        """ Time vs Range mode """
        self.ax.clear()
        time_values = [d[9] for d in data]  # Time
        range_values = [math.sqrt(d[0]**2 + d[1]**2 + d[2]**2) for d in data]  # Range
        self.ax.plot(time_values, range_values, 'm')
        self.ax.set_title("Time vs Range Mode")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Range")
        self.canvas.draw()

    def plot_time_vs_azimuth(self, data):
        """ Time vs Azimuth mode """
        self.ax.clear()
        time_values = [d[9] for d in data]  # Time
        azimuth_values = [math.degrees(math.atan2(d[1], d[0])) for d in data]  # Azimuth
        self.ax.plot(time_values, azimuth_values, 'orange')
        self.ax.set_title("Time vs Azimuth Mode")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Azimuth (degrees)")
        self.canvas.draw()

    def plot_time_vs_elevation(self, data):
        """ Time vs Elevation mode """
        self.ax.clear()
        time_values = [d[9] for d in data]  # Time
        elevation_values = [math.degrees(math.asin(d[2] / (math.sqrt(d[0]**2 + d[1]**2 + d[2]**2))))
                            for d in data]  # Elevation
        self.ax.plot(time_values, elevation_values, 'purple')
        self.ax.set_title("Time vs Elevation Mode")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Elevation (degrees)")
        self.canvas.draw()

    # Mode selection methods
    def select_ppi_mode(self):
        self.plot_type = 'PPI'
        print("PPI mode selected.")

    def select_rhi_mode(self):
        self.plot_type = 'RHI'
        print("RHI mode selected.")

    def select_bscope_mode(self):
        self.plot_type = 'BSCOPE'
        print("BSCOPE mode selected.")

    def select_cscope_mode(self):
        self.plot_type = 'CSCOPE'
        print("CSCOPE mode selected.")

    def select_time_vs_range(self):
        self.plot_type = 'Time vs Range'
        print("Time vs Range mode selected.")

    def select_time_vs_azimuth(self):
        self.plot_type = 'Time vs Azimuth'
        print("Time vs Azimuth mode selected.")

    def select_time_vs_elevation(self):
        self.plot_type = 'Time vs Elevation'
        print("Time vs Elevation mode selected.")

# Application Entry Point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = RadarGUI()
    gui.show()
    sys.exit(app.exec_())
