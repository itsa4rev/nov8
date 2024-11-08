import sys
import socket
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.animation import FuncAnimation
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel,
    QComboBox, QPushButton, QDialog, QDialogButtonBox, QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt, QTimer

# UDP settings
UDP_IP = "127.0.0.1"
UDP_PORT = 5008
data_buffer = []

# UDP Receiver Thread
def udp_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    while True:
        data, _ = sock.recvfrom(1024)
        parsed_data = parse_udp_data(data.decode("utf-8"))
        if parsed_data:
            data_buffer.append(parsed_data)

def parse_udp_data(data):
    try:
        values = data.split(',')
        x, y, z, trk_no, time, lat, lon, alt, spd, hdng = values
        return {

            "x": float(x),
            "y": float(y),
            "z": float(z),
            "track_id":float(trk_no),
            "time": float(time),
            "latitude": float(lat),
            "longitude": float(lon),
            "altitude": float(alt),
            "speed": float(spd),
            "heading": float(hdng),
        }
    except ValueError:
        print("Invalid data format:", data)
        return None

# Start UDP receiver thread
receiver_thread = threading.Thread(target=udp_receiver, daemon=True)
receiver_thread.start()

class RadarPlotDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Radar Plot")
        self.plot_type = None

        # Dropdown for plot selection
        self.dropdown = QComboBox()
        self.dropdown.addItems(["PPI", "RHI", "B-Scope", "C-Scope", 
                                "Time vs Range", "Time vs Azimuth", "Time vs Elevation"])

        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Choose a Radar Plot Type:"))
        layout.addWidget(self.dropdown)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def get_plot_type(self):
        if self.exec_() == QDialog.Accepted:
            return self.dropdown.currentText()
        return None

class RadarDisplayApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Radar Display System")
        self.setGeometry(100, 100, 1200, 800)

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)

        # Button to open plot selection dialog
        self.select_plot_button = QPushButton("Select Plot")
        self.select_plot_button.clicked.connect(self.select_plot)
        main_layout.addWidget(self.select_plot_button)

        # Splitter to separate plot and data view
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # Radar Plot Figure
        self.fig, self.ax = plt.subplots(facecolor="black")
        self.canvas = FigureCanvas(self.fig)
        splitter.addWidget(self.canvas)

        # Data display area
        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        splitter.addWidget(self.data_display)

        # Default plot type
        self.plot_type = "PPI"
        self.setup_plot()

        # Timer for updating data display
        self.data_update_timer = QTimer()
        self.data_update_timer.timeout.connect(self.update_data_display)
        self.data_update_timer.start(500)  # Update every 500 ms

    def select_plot(self):
        dialog = RadarPlotDialog(self)
        selected_plot_type = dialog.get_plot_type()
        if selected_plot_type:
            self.plot_type = selected_plot_type
            self.setup_plot()

    def setup_plot(self):
        self.ax.clear()

        if self.plot_type == "PPI":
            self.ax = self.fig.add_subplot(111, projection='polar', facecolor="black")
            self.ax.set_ylim(0, 100)  # Set your preferred range here
            self.ax.grid(color="green", linestyle="--", linewidth=0.5)
            self.sweep_line, = self.ax.plot([], [], color="lime", linewidth=2)
            self.anim = FuncAnimation(self.fig, self.update_ppi, frames=np.linspace(0, 2*np.pi, 100),
                                      interval=50, blit=True, repeat=True)

        elif self.plot_type == "RHI":
            self.ax = self.fig.add_subplot(111, facecolor="black")
            self.ax.set_xlim(0, 100)  # Range
            self.ax.set_ylim(0, 100)  # Altitude
            self.ax.set_xlabel("Range (km)")
            self.ax.set_ylabel("Altitude (km)")
            self.ax.grid(color="green", linestyle="--", linewidth=0.5)
            self.anim = FuncAnimation(self.fig, self.update_rhi, interval=500)

        elif self.plot_type == "B-Scope":
            self.ax = self.fig.add_subplot(111, facecolor="black")
            self.ax.set_xlim(-180, 180)  # Azimuth
            self.ax.set_ylim(0, 100)     # Range
            self.ax.set_xlabel("Azimuth (degrees)")
            self.ax.set_ylabel("Range (km)")
            self.ax.grid(color="green", linestyle="--", linewidth=0.5)
            self.anim = FuncAnimation(self.fig, self.update_bscope, interval=500)

        # Other plot setups can be implemented similarly...
        
        self.canvas.draw()

    def update_ppi(self, angle):
        self.sweep_line.set_data([angle, angle], [0, 100])  # Replace with your range
        return self.sweep_line,

    def update_rhi(self, frame):
        self.ax.clear()
        self.ax.grid(color="green", linestyle="--", linewidth=0.5)
        if data_buffer:
            ranges = [np.sqrt(point["x"]**2 + point["y"]**2) for point in data_buffer]
            heights = [point["z"] for point in data_buffer]
            self.ax.plot(ranges, heights, 'o', color="lime", markersize=5, alpha=0.7)

    def update_bscope(self, frame):
        self.ax.clear()
        self.ax.grid(color="green", linestyle="--", linewidth=0.5)
        if data_buffer:
            azimuths = [np.degrees(np.arctan2(point["y"], point["x"])) for point in data_buffer]
            ranges = [np.sqrt(point["x"]**2 + point["y"]**2) for point in data_buffer]
            self.ax.plot(azimuths, ranges, 'o', color="lime", markersize=5, alpha=0.7)

    def update_data_display(self):
        # Display the most recent data
        if data_buffer:
            latest_data = data_buffer[-1]
            display_text = (
                f"X: {latest_data['x']:.2f}, Y: {latest_data['y']:.2f}, Z: {latest_data['z']:.2f}, "
                f"Track ID: {latest_data['track_id']}, Time: {latest_data['time']}, "
                f"Lat: {latest_data['latitude']}, Lon: {latest_data['longitude']}, "
                f"Alt: {latest_data['altitude']}, Speed: {latest_data['speed']}, "
                f"Heading: {latest_data['heading']}\n"
            )
            self.data_display.append(display_text)

# Initialize the Qt Application and start the Radar Display App
app = QApplication(sys.argv)
radar_app = RadarDisplayApp()
radar_app.show()
sys.exit(app.exec_())
