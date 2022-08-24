import socket
import pickle
import threading
import time
from utils import RangeAdjust

UDP_PORT = 5005
sock = socket.socket(socket.AF_INET,
                     socket.SOCK_DGRAM)
sock.bind(("", UDP_PORT))

clients = {}

def handleSnd():
    global clients
    while True:
        try:
            for key in clients:
                data_to_send = []
                for key1 in clients:
                    if key1 != key:
                        data_to_send.append([clients[key1][0], clients[key1][1], clients[key1][2], clients[key1][3], clients[key1][4]])
                data = pickle.dumps([1, data_to_send])
                sock.sendto(data, (key[0], key[1])) # send back postions over the ip port

            time.sleep(0.1)
        except Exception as err:
            print(err)

def handleRcv():
    global clients, old_clients, pos_x, pos_y
    while True:
        data, addr = sock.recvfrom(1024)
        try:
            decoded_data = pickle.loads(data)
            if decoded_data[0] == 0:
                if addr in clients:
                    if decoded_data[6] > clients[addr][5]:
                        clients[addr] = [decoded_data[1], decoded_data[2], decoded_data[3], decoded_data[4], decoded_data[5], decoded_data[6]]
                    else:
                        print("---paquet client refuse---\n")
                        print("Id paquet recu : " + str(decoded_data[3]))
                        print("Id client actuel : " + str(clients[addr][3]))
                else:
                    clients[addr] = [decoded_data[1], decoded_data[2], decoded_data[3], decoded_data[4], decoded_data[5], decoded_data[6]]


        except Exception as err:
            print(err)

threading.Thread(target=handleRcv).start()
threading.Thread(target=handleSnd).start()