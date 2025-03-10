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
from PyQt6.QtGui import QMovie

HOST = '172.20.10.4'         #접속ip
PORT = 9900         #접속포트
screen_size = 0.7         #스크린샷 크기
screen_width = 1920         #스크린샷 가로길이
screen_height = 1080         #스크린샷 세로길이
send_queue = Queue()
img_data = Image.open('Waiting.png')

class send_type():
   def __init__(self, type, a, b, time):
      super().__init__()
      self.type = type
      self.first_data = a
      self.sec_data = b
      self.time = time

class win(QtWidgets.QMainWindow):
   def __init__(self, size=1.0, on_top=False):
      super().__init__()
      self.opacity=1                        #투명도
      self.name = "원격제어"                  #창 이름
      self.size = size                     #크기
      self.on_top = on_top                  #항상 위에 있을지
      self.run_watch = 0                     #실행타이머
      self.rel_cursur_xy = [0,0]         #커서 좌표
      self.rel_cusur_ratio = [0,0]      #커서 상대위치%
      self.is_left_clicked = False
      self.mouse_movetime = 0
      self.setupUi()

   def imagemanager_pil(self):         #이미지 변경
      self.img = ImageQt(img_data).copy()
      self.pixmap = QtGui.QPixmap.fromImage(self.img)      #pixmap 생성
      self.pixmap = self.pixmap.scaled(int(self.pixmap.width()*self.size), int(self.pixmap.height()*self.size))   #사이즈 변경
      self.label.setPixmap(self.pixmap)   #적용
      self.label.resize(self.pixmap.width(), self.pixmap.height())   #라벨 크기 변경
      self.label.move(self.rel_cursur_xy[0] - self.rel_cusur_ratio[0]*self.label.width(), self.rel_cursur_xy[1] - self.rel_cusur_ratio[1]*self.label.height())   #이동

   def setupUi(self):
      global screen_size, screen_width, screen_height
      self.centralWidget = QtWidgets.QWidget(self)
      self.setCentralWidget(self.centralWidget)

      self.setWindowTitle(self.name)                  #윈도우 제목 지정
      self.label = QtWidgets.QLabel(self.centralWidget)

      self.setMouseTracking(True)
      self.centralWidget.setMouseTracking(True)
      self.label.setMouseTracking(True)

      self.width = int(screen_width*screen_size)
      self.height = int(screen_height*screen_size)
      self.setGeometry(0, 0, self.width, self.height)
      self.imagemanager_pil()
      self.show()

   def resizeEvent(self, event):
      self.width = self.centralWidget.frameGeometry().width()
      self.height = self.centralWidget.frameGeometry().height()

   def wheelEvent(self, event):         #마우스휠 확대
      if (keyboard.is_pressed('ctrl')):         #컨트롤을 누를경우 크기조정
         self.rel_cursur_xy = [event.pos().x(), event.pos().y()]      #커서 위치 저장
         self.rel_cusur_ratio = [(event.pos().x()-self.label.x())/self.label.width(), (event.pos().y()-self.label.y())/self.label.height()]   #커서 상대위치% 저장
         print (self.rel_cusur_ratio)
         if (event.angleDelta().y() < 0 and not self.size-0.15 <= 0.15):         #크기변수 수정
            print(self.size)
            self.size -= 0.15
         elif (event.angleDelta().y() > 0 and not self.size+0.15 >= 5):
            self.size += 0.15
      else:
         send_queue.put(send_type("mouse_wheel", event.angleDelta().y(), 0, self.run_watch))   #큐 추가


   def mousePressEvent(self, event):
      global send_queue, screen_width, screen_height
      self.rel_cursur_xy = [event.pos().x(), event.pos().y()]      #커서 위치 저장
      self.rel_cusur_ratio = [(event.pos().x()-self.label.x())/self.label.width(), (event.pos().y()-self.label.y())/self.label.height()]   #커서 상대위치% 저장
      if (keyboard.is_pressed('ctrl')):
         if (event.button() == QtCore.Qt.MouseButton.LeftButton):
            self.is_left_clicked = True
      else:
         mouse_x = int((event.pos().x()-self.label.x())/self.label.width()*screen_width)   #마우스 좌표 계산
         mouse_y = int((event.pos().y()-self.label.y())/self.label.height()*screen_height)
         if (event.button() == QtCore.Qt.MouseButton.LeftButton):
            send_queue.put(send_type("mouse_left_down", mouse_x, mouse_y, self.run_watch))   #큐 추가
         elif (event.button() == QtCore.Qt.MouseButton.RightButton):
            send_queue.put(send_type("mouse_right_down", mouse_x, mouse_y, self.run_watch))   #큐 추가


   def mouseMoveEvent(self, event):
      global send_queue, screen_width, screen_height
      if (keyboard.is_pressed('ctrl') and self.is_left_clicked):
         self.label.move(self.label.x() + (event.pos().x() - self.rel_cursur_xy[0]), self.label.y() + (event.pos().y() - self.rel_cursur_xy[1]))
         self.rel_cursur_xy = [event.x(), event.y()]      #커서 위치 저장
         self.rel_cusur_ratio = [(event.pos().x()-self.label.x())/self.label.width(), (event.pos().y()-self.label.y())/self.label.height()]   #커서 상대위치% 저장
      elif (not keyboard.is_pressed('ctrl')):
         if (self.label.x() < event.pos().x() < self.label.x()+self.label.width() and self.label.y() < event.pos().y() < self.label.y()+self.label.height()):
            mouse_x = int((event.pos().x()-self.label.x())/self.label.width()*screen_width)   #마우스 좌표 계산
            mouse_y = int((event.pos().y()-self.label.y())/self.label.height()*screen_height)
            send_queue.put(send_type("mouse_move", mouse_x, mouse_y, self.run_watch))   #큐 추가

   def mouseReleaseEvent(self, event):
      global send_queue, screen_width, screen_height
      if (keyboard.is_pressed('ctrl')):
         if (event.button() == QtCore.Qt.MouseButton.LeftButton):
            self.is_left_clicked = False
      else:
         mouse_x = int((event.pos().x()-self.label.x())/self.label.width()*screen_width)   #마우스 좌표 계산
         mouse_y = int((event.pos().y()-self.label.y())/self.label.height()*screen_height)
         if (event.button() == QtCore.Qt.MouseButton.LeftButton):
            send_queue.put(send_type("mouse_left_up", mouse_x, mouse_y, self.run_watch))   #큐 추가
         elif (event.button() == QtCore.Qt.MouseButton.RightButton):
            send_queue.put(send_type("mouse_right_up", mouse_x, mouse_y, self.run_watch))   #큐 추가

   def run(self):            #행동함수
      self.run_timer = QtCore.QTimer(self)
      self.run_timer.timeout.connect(self.__runCore)            #0.01초마다 self.__runCore 호출
      self.run_timer.start(10)
   def __runCore(self):
      self.imagemanager_pil()               #화면 업데이트

      self.run_watch += 0.01
      self.run_watch = round(self.run_watch, 2)



def receive_screen(client_socket, addr):      #데이터 받기 함수
   global screen_size, screen_width, screen_height, img_data
   length = 0
   a = 0
   while (True):
      start = time.process_time()      #시작시간 기록
      try:
         data = client_socket.recv(4)   #데이터 길이를 먼저 받음
         length = int.from_bytes(data, "little")
         buf = b''
         step = length
         a=0
         while True:            #데이터가 전부 받아질 때까지 반복
            a += 1
            data = client_socket.recv(step)
            buf += data
            if len(buf) == length:
               break
            elif len(buf) < length:
               step = length - len(buf)
         data = zlib.decompress(buf)         #압축풀기
         img_data = Image.frombytes('RGB', (int(screen_width*screen_size), int(screen_height*screen_size)), data)   #이미지 저장
      except Exception as ex:
         print(ex)
      finally:
         end = time.process_time()      #끝 시간 기록
         print("receive -> " + str(length) + " : " + str(a) + " : " + str(end - start))      #소요시간 출력




def send(client_socket, addr):
   global send_queue
   length = 0
   last_time = 0
   while (True):
      start = time.process_time()      #시작시간 기록`
      try:
         if (send_queue.qsize() != 0):
            send_data = send_queue.get()      #큐에서 꺼내옴
            if ((send_data.type == "mouse_move" and (last_time + 0.3 > send_data.time or send_queue.qsize() == 0))): continue   #드래그라면 0.3초마다 전송
            last_time = send_data.time
            data = str(send_data.type) + ":" + str(send_data.first_data) + ":" + str(send_data.sec_data)
            data = data.encode()
            length = len(data)
            client_socket.sendall(length.to_bytes(4, byteorder="little"))      #데이터 크기 전송
            client_socket.sendall(data)            #데이터 전송
      except Exception as ex:
         print(ex)
      finally:
         end = time.process_time()      #끝 시간 기록
         print("send -> " + str(length) + " : " + str(end - start))      #소요시간 출력
      time.sleep(0.01)





if __name__ == '__main__':
   client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   client_socket.connect((HOST, PORT))         #접속

   th_send = threading.Thread(target=send, args = (client_socket, HOST))      #전송함수 쓰레드
   th_send.start()
   th_receive_screen = threading.Thread(target=receive_screen, args = (client_socket, HOST))      #받기함수 쓰레드
   th_receive_screen.start()

   app = QtWidgets.QApplication(sys.argv)      #윈도우 창
   window = win(size=1, on_top=False)
   window.run()
   sys.exit(app.exec())