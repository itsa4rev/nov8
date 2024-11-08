import csv
import socket
import time

# UDP settings
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

def send_csv_data(csv_file_path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    with open(csv_file_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            # Prepare the data in the expected format
            try:
                x = row["F_X"]
                y = row["F_Y"]
                z = row["F_Z"]
                xv = row["F_VX"]
                yv = row["F_VY"]
                zv = row["F_VZ"]
                source = "Radar"  # Assumed constant for this example
                trk_no = row["trk_id"]
                types = "TypeA"   # Placeholder for radar type
                time_stamp = row["P_TIME"]
                latitude = row["latitude"]
                longitude = row["longitude"]
                altitude = row["altitude"]
                speed = row["speed"]
                heading = row["heading"]

                # Create the formatted message
                message = f"{x},{y},{z},{xv},{yv},{zv},{source},{trk_no},{types},{time_stamp},{latitude},{longitude},{altitude},{speed},{heading}"
                
                # Send the data
                sock.sendto(message.encode('utf-8'), (UDP_IP, UDP_PORT))
                print(f"Sent: {message}")
                
                # Delay to simulate real-time streaming
                time.sleep(0.1)  # Adjust as needed for your data rate
            
            except KeyError as e:
                print(f"Missing column in CSV row: {e}")

    sock.close()

# Path to your CSV file
csv_file_path = "radar_data.csv"

# Start sending data
send_csv_data(csv_file_path)
