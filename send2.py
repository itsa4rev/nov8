import csv
import socket
import time

# UDP settings
UDP_IP = "127.0.0.1"  # Localhost
UDP_PORT = 5008

# Define the columns we need to extract from the CSV
# Column names should match the header in your CSV
columns = [
    "F_X", "F_Y", "F_Z", "F_VX", "F_VY", "F_VZ", 
    "trk_id", "types", "P_TIME", "latitude", 
    "longitude", "altitude", "speed", "heading"
]

def format_data(row):
    """
    Format the row into the required structure:
    x,y,z,xv,yv,zv,source, trk_no,types,time,latitude,longitude,altitude,speed,hdng
    """
    try:
        # Extract and format each required field
        x = row["F_X"]
        y = row["F_Y"]
        z = row["F_Z"]
        
        trk_no = row["trk_id"]
        
        time_stamp = row["P_EL"]
        latitude = row["RNG_MAX"]
        longitude = row["RNG_MIN"]
        altitude = row["EL_MAX"]
        speed = row["EL_MIN"]
        heading = row["EL_MAX"]

        # Format as a comma-separated string
        formatted_data = f"{x},{y},{z},{trk_no},{time_stamp},{latitude},{longitude},{altitude},{speed},{heading}"
        return formatted_data
    except KeyError as e:
        print(f"Missing column in CSV row: {e}")
        return None

def send_csv_data_via_udp(csv_file_path):
    # Open a socket for UDP communication
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Read the CSV file and send each row as a UDP packet
    with open(csv_file_path, mode="r") as csv_file:
        csv_reader = csv.DictReader(csv_file)

        for row in csv_reader:
            # Format the row into the required UDP message structure
            message = format_data(row)
            if message:
                # Send the message via UDP
                sock.sendto(message.encode("utf-8"), (UDP_IP, UDP_PORT))
                
                # Print the sent data on the sending end
                print(f"Sent: {message}")

                # Add a delay to simulate real-time data transmission
                time.sleep(0.1)  # Adjust the delay as needed

    # Close the socket after sending all data
    sock.close()

# Path to your CSV file
csv_file_path = "radar_data.csv"

# Start sending data
send_csv_data_via_udp(csv_file_path)
