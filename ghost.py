import socket, threading
import pyautogui
import time
import zlib

screen_size = 0.7      #스크린샷 사이즈
scroll = 0.02

def send(client_socket, addr):      #전송함수
   global screen_size
   print('connect: ', addr)
   try:
      while(True):
         image = pyautogui.screenshot()         #스크린샷 촬영
         image = image.resize(( int( image.size[0]*(screen_size) ), int( image.size[1]*(screen_size) ) ))   #크기조정
         data = image.tobytes()            #바이트화
         data = zlib.compress(data)         #압축
         length = len(data)
         client_socket.sendall(length.to_bytes(4, byteorder="little"))      #데이터 크기 전송
         client_socket.sendall(data)            #데이터 전송
   except Exception as ex:
      return 0
   finally:
      client_socket.close()

def receive(client_socket, addr):      #데이터 받기 함수
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
         data = buf.decode('utf-8').split(":")
         if (data[0] == "mouse_move"): mouse_control(data[1], data[2], "move")
         elif (data[0] == "mouse_left_down"): mouse_control(data[1], data[2], "down", "left")
         elif (data[0] == "mouse_left_up"): mouse_control(data[1], data[2], "up", "left")
         elif (data[0] == "mouse_right_down"): mouse_control(data[1], data[2], "down", "right")
         elif (data[0] == "mouse_right_up"): mouse_control(data[1], data[2], "up", "right")
         elif (data[0] == "mouse_wheel"): mouse_control(data[1], data[2], "wheel")

      except Exception as ex:
         print(ex)
         client_socket.close()
      finally:
         end = time.process_time()      #끝 시간 기록
         print("receive -> " + str(length) + " : " + str(a) + " : " + str(end - start))      #소요시간 출력

def mouse_control(first, sec, control_type, button="none"):
   global scroll
   tx = int(first)
   ty = int(sec)

   if (control_type == "move"): pyautogui.moveTo(int(tx), int(ty))
   elif (control_type == "down"): pyautogui.mouseDown(int(tx), int(ty), button)
   elif (control_type == "up"): pyautogui.mouseUp(int(tx), int(ty), button)
   elif (control_type == "wheel"): pyautogui.scroll(int(tx*scroll))





server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         #서버 생성
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', 9900))
server_socket.listen()

try:
   while True:
      client_socket, addr = server_socket.accept()         #연결 기다리기
      th_send = threading.Thread(target=send, args = (client_socket,addr))
      th_receive = threading.Thread(target=receive, args = (client_socket,addr))
      th_send.start()         #send함수 실행
      th_receive.start()         #receive함수 실행
except:
   server_socket.close()