import socket
import time

UDP_IP = "127.0.0.1"  # The IP address of the radar display application
UDP_PORT = 5005       # The port on which the radar display app is listening

# Sample data in the same format as described
sample_data = [
    "100,200,300,10,15,5,Radar1,1,Aircraft,10.5,34.0522,-118.2437,15000,600,90",
    "120,180,290,11,13,4,Radar2,2,Aircraft,20.0,34.1522,-118.3437,14000,620,85",
    "140,160,280,12,11,3,Radar3,3,Helicopter,30.5,34.2522,-118.4437,13000,550,80",
    "160,140,270,13,10,2,Radar4,4,Drone,40.0,34.3522,-118.5437,12000,570,75"
]

# Set up a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    # Send each data entry every 2 seconds
    for data in sample_data:
        print(f"Sending data: {data}")
        sock.sendto(data.encode('utf-8'), (UDP_IP, UDP_PORT))
        time.sleep(2)
finally:
    sock.close()
