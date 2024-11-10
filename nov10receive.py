import sys
import socket
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.animation import FuncAnimation
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QComboBox, 
    QPushButton, QDialog, QDialogButtonBox, QTextEdit, QSplitter, QLineEdit, QFormLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# UDP settings
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
data_buffer = []

# CSS Styling
CSS = """
QMainWindow {
    background-color: #2E2E2E;
    color: white;
}

QLabel {
    font-size: 14px;
}

QPushButton {
    background-color: #4CAF50;
    color: white;
    padding: 8px;
    font-size: 12px;
}

QComboBox, QLineEdit, QTextEdit {
    background-color: #3E3E3E;
    color: white;
}
"""

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
        x, y, z, xv, yv, zv, source, trk_no, types, time, latitude, longitude, altitude, speed, hdng = values
        return {
            "x": float(x),
            "y": float(y),
            "z": float(z),
            "xv": float(xv),
            "yv": float(yv),
            "zv": float(zv),
            "source": source,
            "track_id": int(trk_no),
            "type": types,
            "time": float(time),
            "latitude": float(latitude),
            "longitude": float(longitude),
            "altitude": float(altitude),
            "speed": float(speed),
            "heading": float(hdng)
        }
    except ValueError:
        print("Invalid data format:", data)
        return None

# Start UDP receiver thread
receiver_thread = threading.Thread(target=udp_receiver, daemon=True)
receiver_thread.start()

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration Settings")

        self.range_min = QLineEdit("0")
        self.range_max = QLineEdit("100")
        self.elevation_min = QLineEdit("0")
        self.elevation_max = QLineEdit("180")
        self.azimuthal_marking = QLineEdit("10")

        layout = QFormLayout()
        layout.addRow("Range Minimum:", self.range_min)
        layout.addRow("Range Maximum:", self.range_max)
        layout.addRow("Elevation Minimum:", self.elevation_min)
        layout.addRow("Elevation Maximum:", self.elevation_max)
        layout.addRow("Azimuthal Marking (PPI):", self.azimuthal_marking)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_settings(self):
        if self.exec() == QDialog.Accepted:
            return {
                "range_min": int(self.range_min.text()),
                "range_max": int(self.range_max.text()),
                "elevation_min": int(self.elevation_min.text()),
                "elevation_max": int(self.elevation_max.text()),
                "azimuthal_marking": int(self.azimuthal_marking.text())
            }
        return None

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
        self.setStyleSheet(CSS)

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)

        # Configuration and plot selection buttons
        self.config_button = QPushButton("Configure Settings")
        self.config_button.clicked.connect(self.configure_settings)
        main_layout.addWidget(self.config_button)

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

        # Default plot type and configuration settings
        self.plot_type = "PPI"
        self.config = {"range_min": 0, "range_max": 100, "elevation_min": 0, "elevation_max": 180, "azimuthal_marking": 10}
        self.setup_plot()

        # Timer for updating data display
        self.data_update_timer = QTimer()
        self.data_update_timer.timeout.connect(self.update_data_display)
        self.data_update_timer.start(500)  # Update every 500 ms

    def configure_settings(self):
        dialog = ConfigDialog(self)
        settings = dialog.get_settings()
        if settings:
            self.config = settings
            self.setup_plot()

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
            self.ax.set_ylim(self.config["range_min"], self.config["range_max"])
            self.ax.grid(color="green", linestyle="--", linewidth=0.5)
            self.sweep_line, = self.ax.plot([], [], color="lime", linewidth=2)
            self.anim = FuncAnimation(self.fig, self.update_ppi, frames=np.linspace(0, 2*np.pi, 100),
                                      interval=50, blit=True, repeat=True)

        elif self.plot_type == "RHI":
            self.ax = self.fig.add_subplot(111, facecolor="black")
            self.ax.set_xlim(self.config["range_min"], self.config["range_max"])
            self.ax.set_ylim(self.config["elevation_min"], self.config["elevation_max"])
            self.ax.grid(color="green", linestyle="--", linewidth=0.5)
            self.anim = FuncAnimation(self.fig, self.update_rhi, interval=500)

        elif self.plot_type == "B-Scope":
            self.ax = self.fig.add_subplot(111, facecolor="black")
            self.ax.set_xlim(-180, 180)
            self.ax.set_ylim(self.config["range_min"], self.config["range_max"])
            self.ax.grid(color="green", linestyle="--", linewidth=0.5)
            self.anim = FuncAnimation(self.fig, self.update_bscope, interval=500)

    

        # C-Scope: Displays Range vs Azimuth
        elif self.plot_type == "C-Scope":
            self.ax = self.fig.add_subplot(111, facecolor="black")
            self.ax.set_xlim(-180, 180)  # Azimuth range in degrees
            self.ax.set_ylim(self.config["range_min"], self.config["range_max"])  # Range limits
            self.ax.grid(color="blue", linestyle="--", linewidth=0.5)
            self.ax.set_xlabel("Azimuth (°)")
            self.ax.set_ylabel("Range")
            self.anim = FuncAnimation(self.fig, self.update_cscope, interval=500)

        # Time vs Azimuth
        elif self.plot_type == "Time vs Azimuth":
            self.ax = self.fig.add_subplot(111, facecolor="black")
            self.ax.set_xlim(0, self.config["time_max"])  # Time limit
            self.ax.set_ylim(-180, 180)  # Azimuth range in degrees
            self.ax.grid(color="purple", linestyle="--", linewidth=0.5)
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Azimuth (°)")
            self.anim = FuncAnimation(self.fig, self.update_time_vs_azimuth, interval=500)

        # Time vs Range
        elif self.plot_type == "Time vs Range":
            self.ax = self.fig.add_subplot(111, facecolor="black")
            self.ax.set_xlim(0, self.config["time_max"])  # Time limit
            self.ax.set_ylim(self.config["range_min"], self.config["range_max"])  # Range limits
            self.ax.grid(color="cyan", linestyle="--", linewidth=0.5)
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Range")
            self.anim = FuncAnimation(self.fig, self.update_time_vs_range, interval=500)

        # Time vs Elevation
        elif self.plot_type == "Time vs Elevation":
            self.ax = self.fig.add_subplot(111, facecolor="black")
            self.ax.set_xlim(0, self.config["time_max"])  # Time limit
            self.ax.set_ylim(-90, 90)  # Elevation range in degrees
            self.ax.grid(color="orange", linestyle="--", linewidth=0.5)
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Elevation (°)")
            self.anim = FuncAnimation(self.fig, self.update_time_vs_elevation, interval=500)
    

        self.canvas.draw()

    def update_ppi(self, angle):
        self.ax.clear()
        self.ax.grid(color="green", linestyle="--", linewidth=0.5)
    
        if data_buffer:
            ranges = [np.sqrt(point["x"]**2 + point["y"]**2) for point in data_buffer]
            azimuths = [np.arctan2(point["y"], point["x"]) for point in data_buffer]  # No need for np.radians(np.degrees(...))
            self.ax.scatter(azimuths, ranges, color="lime", s=10, alpha=0.7)

    # Set labels after clearing the axis
        self.ax.set_xlabel("Azimuth (°)")
        self.ax.set_ylabel("Range")
    
        return self.ax,


    def update_rhi(self, frame):
        self.ax.clear()
        self.ax.grid(color="green", linestyle="--", linewidth=0.5)
        if data_buffer:
            ranges = [np.sqrt(point["x"]**2 + point["y"]**2) for point in data_buffer]
            heights = [point["z"] for point in data_buffer]
            self.ax.plot(ranges, heights, 'o', color="lime", markersize=5, alpha=0.7)
        self.ax.set_xlabel("Azimuth (°)")
        self.ax.set_ylabel("Range")

    def update_bscope(self, frame):
        self.ax.clear()
        self.ax.grid(color="green", linestyle="--", linewidth=0.5)
        if data_buffer:
            azimuths = [np.degrees(np.arctan2(point["y"], point["x"])) for point in data_buffer]
            ranges = [np.sqrt(point["x"]**2 + point["y"]**2) for point in data_buffer]
            self.ax.plot(azimuths, ranges, 'o', color="lime", markersize=5, alpha=0.7)
        self.ax.set_xlabel("Azimuth (°)")
        self.ax.set_ylabel("Range")
    
    
    def update_cscope(self, frame):
        self.ax.clear()
        self.ax.grid(color="blue", linestyle="--", linewidth=0.5)
        if data_buffer:
            azimuths = [np.degrees(np.arctan2(point["y"], point["x"])) for point in data_buffer]
            ranges = [np.sqrt(point["x"]**2 + point["y"]**2) for point in data_buffer]
            self.ax.plot(azimuths, ranges, 'o', color="cyan", markersize=5, alpha=0.7)
        self.ax.set_xlabel("Azimuth (°)")
        self.ax.set_ylabel("Range")

    def update_time_vs_azimuth(self, frame):
        self.ax.clear()
        self.ax.grid(color="purple", linestyle="--", linewidth=0.5)
        if data_buffer:
            times = [point["time"] for point in data_buffer]
            azimuths = [np.degrees(np.arctan2(point["y"], point["x"])) for point in data_buffer]
            self.ax.plot(times, azimuths, 'o', color="magenta", markersize=5, alpha=0.7)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Azimuth (°)")        
            
    def update_time_vs_range(self, frame):
        self.ax.clear()
        self.ax.grid(color="cyan", linestyle="--", linewidth=0.5)
        if data_buffer:
            times = [point["time"] for point in data_buffer]
            ranges = [np.sqrt(point["x"]**2 + point["y"]**2) for point in data_buffer]
            self.ax.plot(times, ranges, 'o', color="aqua", markersize=5, alpha=0.7)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Range")     
            
    def update_time_vs_elevation(self, frame):
        self.ax.clear()
        self.ax.grid(color="orange", linestyle="--", linewidth=0.5)
        if data_buffer:
            times = [point["time"] for point in data_buffer]
            elevations = [np.degrees(np.arcsin(point["z"] / np.sqrt(point["x"]**2 + point["y"]**2 + point["z"]**2))) for point in data_buffer]
            self.ax.plot(times, elevations, 'o', color="orange", markersize=5, alpha=0.7)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Elevation (°)")


    

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
if __name__ == "__main__":
    app = QApplication(sys.argv)
    radar_app = RadarDisplayApp()
    radar_app.show()
    sys.exit(app.exec_())

