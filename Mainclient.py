import sys
import time
from PIL import Image
import keyboard
import socket
import zlib
import threading
from queue import Queue
from PyQt6 import QtCore, QtWidgets, QtGui
from PIL.ImageQt import ImageQt

HOST = '220.149.128.103'
PORT = 4599
SCREEN_SIZE = 0.7
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SEND_QUEUE = Queue()
IMG_DATA = Image.open('Waiting.png')

CLIENT_NAME = "MainClient"
# 클라이언트의 이름

def send_client_name(client_socket):
    global CLIENT_NAME
    name_data = f"{CLIENT_NAME}\n".encode()
    try:
        client_socket.sendall(name_data)
    except Exception as ex:
        print(ex)

class SendType():
    def __init__(self, type, a, b, time):
        super().__init__()
        self.type = type
        self.first_data = a
        self.sec_data = b
        self.time = time

class Win(QtWidgets.QMainWindow):
    def __init__(self, size=1.0, on_top=False):
        super().__init__()
        self.opacity=1
        self.name = "원격제어"
        self.size = size
        self.on_top = on_top
        self.run_watch = 0
        self.rel_cursor_xy = [0,0]
        self.rel_cursor_ratio = [0,0]
        self.is_left_clicked = False
        self.mouse_movetime = 0
        self.setup_ui()

    def image_manager_pil(self):
        self.img = ImageQt(IMG_DATA).copy()
        self.pixmap = QtGui.QPixmap.fromImage(self.img)
        self.pixmap = self.pixmap.scaled(int(self.pixmap.width()*self.size), int(self.pixmap.height()*self.size))
        self.label.setPixmap(self.pixmap)
        self.label.resize(self.pixmap.width(), self.pixmap.height())

    def setup_ui(self):
        global SCREEN_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.setWindowTitle(self.name)
        self.label = QtWidgets.QLabel(self.central_widget)

        self.setMouseTracking(True)
        self.central_widget.setMouseTracking(True)
        self.label.setMouseTracking(True)

        self.width = int(SCREEN_WIDTH * SCREEN_SIZE)
        self.height = int(SCREEN_HEIGHT * SCREEN_SIZE)
        self.setGeometry(0, 0, self.width, self.height)
        self.image_manager_pil()
        self.show()

    def resizeEvent(self, event):
        self.width = self.central_widget.frameGeometry().width()
        self.height = self.central_widget.frameGeometry().height()

    def wheelEvent(self, event):
        if keyboard.is_pressed('ctrl'):
            self.rel_cursor_xy = [event.x(), event.y()]
            self.rel_cursor_ratio = [(event.x()-self.label.x())/self.label.width(), (event.y()-self.label.y())/self.label.height()]
            print (self.rel_cursor_ratio)
            if event.angleDelta().y() < 0 and not self.size-0.15 <= 0.15:
                print(self.size)
                self.size -= 0.15
            elif event.angleDelta().y() > 0 and not self.size+0.15 >= 5:
                self.size += 0.15
        else:
            SEND_QUEUE.put(SendType("mouse_wheel", event.angleDelta().y(), 0, self.run_watch))

    def mouse_press_event(self, event):
        global SEND_QUEUE, SCREEN_WIDTH, SCREEN_HEIGHT
        self.rel_cursor_xy = [event.pos().x(), event.pos().y()]
        self.rel_cursor_ratio = [(event.pos().x()-self.label.x())/self.label.width(), (event.pos().y()-self.label.y())/self.label.height()]
        if keyboard.is_pressed('ctrl'):
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                self.is_left_clicked = True
        else:
            mouse_x = int((event.pos().x()-self.label.x())/self.label.width()*SCREEN_WIDTH)
            mouse_y = int((event.pos().y()-self.label.y())/self.label.height()*SCREEN_HEIGHT)
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                SEND_QUEUE.put(SendType("mouse_left_down", mouse_x, mouse_y, self.run_watch))
            elif event.button() == QtCore.Qt.MouseButton.RightButton:
                SEND_QUEUE.put(SendType("mouse_right_down", mouse_x, mouse_y, self.run_watch))

    def mouse_release_event(self, event):
        global SEND_QUEUE, SCREEN_WIDTH, SCREEN_HEIGHT
        if keyboard.is_pressed('ctrl'):
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                self.is_left_clicked = False
        else:
            mouse_x = int((event.pos().x()-self.label.x())/self.label.width()*SCREEN_WIDTH)
            mouse_y = int((event.pos().y()-self.label.y())/self.label.height()*SCREEN_HEIGHT)
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                SEND_QUEUE.put(SendType("mouse_left_up", mouse_x, mouse_y, self.run_watch))
            elif event.button() == QtCore.Qt.MouseButton.RightButton:
                SEND_QUEUE.put(SendType("mouse_right_up", mouse_x, mouse_y, self.run_watch))

    def run(self):
        self.run_timer = QtCore.QTimer(self)
        self.run_timer.timeout.connect(self.run_core)
        self.run_timer.start(10)

    def run_core(self):
        self.image_manager_pil()
        self.run_watch += 0.1
        self.run_watch = round(self.run_watch, 2)

def receive_screen(client_socket, addr):
    global SCREEN_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, IMG_DATA
    length = 0
    a = 0
    while True:
        start = time.process_time()
        try:
            data = client_socket.recv(4)
            length = int.from_bytes(data, "little")
            buf = b''
            step = length
            a = 0
            while True:
                a += 1
                data = client_socket.recv(step)
                buf += data
                if len(buf) == length:
                    break
                elif len(buf) < length:
                    step = length - len(buf)
            data = zlib.decompress(buf)
            IMG_DATA = Image.frombytes('RGB', (int(SCREEN_WIDTH*SCREEN_SIZE), int(SCREEN_HEIGHT*SCREEN_SIZE)), data)
        except Exception as ex:
            print(ex)
        finally:
            end = time.process_time()

def send(client_socket, addr):
    global SEND_QUEUE
    length = 0
    last_time = 0
    while True:
        start = time.process_time()
        try:
            if SEND_QUEUE.qsize() != 0:
                send_data = SEND_QUEUE.get()
                data = str(send_data.type) + ":" + str(send_data.first_data) + ":" + str(send_data.sec_data)
                data = data.encode()
                length = len(data)
                client_socket.sendall(length.to_bytes(4, byteorder="little"))
                client_socket.sendall(data)
        except Exception as ex:
            print(ex)
        finally:
            end = time.process_time()

if __name__ == '__main__':
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    send_client_name(client_socket)
   
    th_send = threading.Thread(target=send, args=(client_socket, HOST))
    th_send.start()
    th_receive_screen = threading.Thread(target=receive_screen, args=(client_socket, HOST))
    th_receive_screen.start()

    app = QtWidgets.QApplication(sys.argv)
    window = Win(size=1, on_top=True)
    window.run()
    sys.exit(app.exec())