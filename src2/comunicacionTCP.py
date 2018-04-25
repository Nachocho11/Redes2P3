import cv2
import socket
import threading
from PIL import Image, ImageTk
import servidorDescubrimiento as server
import comunicacionUDP as UDP

class ComunicacionTCP:

	# Campos

	# Servidor, para conseguir alguna IP
	server = None
	# Nuestra IP
	publicIP = None
	# Puerto en el que vamos a recibir
	listenPort = None
	# IP del usuario con el que tendremos la comunicacion
	IPdest = None
	# Permanente
	socketRecepcion = None
	# Temporal
	socketEnvio = None	

	udpcom = None
	# Macros
	queueSize = 5


	# Events para controlar la comunicacion UDP

	pauseEvent = None
	endEvent = None



	# Construction, basic 
	def __init__(self, gui, myIP, listenPort, serverPort):
		self.gui = gui
		self.listenPort = listenPort
		self.publicIP = myIP
		self.socketRecepcion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socketRecepcion.bind(('0.0.0.0', int(self.listenPort)))
		self.socketRecepcion.listen(self.queueSize)
		self.server = server.servidorDescubrimiento(serverPort)
		

	# Close socket
	def close_listeningSocket(self):
		self.listenPort.close()

	#### FUNCIONES DE ENVIO DE PETICIONES

	def send_petition(self, ipDest, portDest , petition):
		
		self.socketEnvio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print(ipDest)
		print(portDest)
		try: 
			self.socketEnvio.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.socketEnvio.settimeout(5)
			self.socketEnvio.connect((ipDest, int(portDest)))
			self.socketEnvio.settimeout(None)
		
		except (OSError, ConnectionRefusedError):
			print("No se ha podido establecer una conexion con ese usuario") 
			return "ERROR"

		self.socketEnvio.send(bytes(petition, 'utf-8'))
		self.socketEnvio.close()

	def send_calling(self, ipDest, portDest, myUDPport, username):
		print("hallelujah")
		petition = "CALLING {} {}".format(username, myUDPport)
		self.send_petition(ipDest, portDest, petition)
		print("hallelujah33")
	
	def send_hold(self, ipDest, portDest, username):
		petition = "CALL_HOLD {}".format(username)
		self.send_petition(ipDest, portDest, petition)
		self.pauseEvent.set()
	

	def send_resume(self, ipDest, portDest, username):
		petition = "CALL_RESUME {}".format(username)
		self.send_petition(ipDest, portDest, petition)
		self.pauseEvent.clear()

	def send_end(self, ipDest, portDest, username):
		petition = "CALL_END {}".format(username)
		self.send_petition(ipDest, portDest, petition)
		self.endEvent.set()
		self.gui.inCall = False


	#### FUNCIONES DE ENVIO DE RESPUESTAS

	def send_call_accepted(self, ipDest, portDest, myUDPport, username):
		petition = "CALL_ACCEPTED {} {}".format(username, myUDPport)
		self.send_petition(ipDest, portDest, petition)
	

	def send_call_denied(self, ipDest, portDest, username):
		petition = "CALL_DENIED {}".format(username)
		self.send_petition(ipDest, portDest, petition)
	

	def send_call_busy(self, ipDest, portDest):
		petition = "CALL_BUSY"
		self.send_petition(ipDest, portDest, petition)

	#### FUNCIONES DE RECEPCION DE PETICIONES

	def calling_handler(self, username , srcUDPport):

		print("Estas recibiendo una llamada")

		userInfo = self.server.getInfoUsuario(username)

		if self.gui.inCall == False:

			message = "{} te esta llamando!!! ¿Quieres aceptar?".format(username)
			ret = self.gui.app.yesNoBox("LLamada entrante", message, parent=None)


			if ret == False:

				self.send_call_denied(ipDest = userInfo['ip'], portDest = userInfo['listenPort'] , username = self.gui.username)

			elif ret == True:
				
				self.send_call_accepted(ipDest = userInfo['ip'], portDest = userInfo['listenPort'] , myUDPport =  self.listenPort, username = self.gui.username)					

				self.gui.inCall = True
				self.udpcom = UDP.comunicacionUDP( self.gui, self.publicIP, self.listenPort)
				self.udpcom.configurarSocketEnvio(destIp= userInfo['ip'] , destPort= srcUDPport, cliente= False)
				self.endEvent = threading.Event()
				self.pauseEvent = threading.Event()
				self.webCamThread = threading.Thread(target = self.udpcom.transmisionWebCam, args = (self.endEvent, self.pauseEvent)) 
				self.videoReceptionThread = threading.Thread(target = self.udpcom.recepcionWebCam, args = (self.endEvent, self.pauseEvent)) 
				self.webCamThread.start()
				self.videoReceptionThread.start()

		else:

			self.send_call_busy(ipDest= userInfo['ip'], portDest = userInfo['listenPort'])


	def call_hold_handler(self, username):
		
		if self.gui.inCall == True:

			self.pauseEvent.set()


	def call_resume_handler(self, username):

		if self.gui.inCall == True:

			self.pauseEvent.clear()


	def call_end_handler(self, username):

		if gui.inCall == True:

			# Con esto dejamos de mandar video
			self.endEvent.set()			
			self.gui.inCall = False
				
		
	#### FUNCIONES DE RECEPCION DE RESPUESTAS

	def call_accepted_handler(self, username , destUDPport):

		if self.gui.inCall == False:

			userInfo = self.server.getInfoUsuario(username)

			message = "{} ha aceptado tu llamada!".format(username)
			self.gui.infoBox("LLamada establecida", message, parent=None)

			self.gui.inCall = True

			self.gui.p2pNick = username
			self.gui.p2pIP = userInfo['ip']
			self.gui.p2pListenPort = userInfo['listenPort']

			self.udpcom = UDP.comunicacionUDP(self.gui, self.publicIP, self.listenPort)
			self.udpcom.configurarSocketEnvio(destIp= userInfo['ip'] , destPort= destUDPport, cliente= True)
			self.endEvent = threading.Event()
			self.pauseEvent = threading.Event()
			self.webCamThread = threading.Thread(target = self.UDPself.udpcom.transmisionWebCam, args = (self.endEvent, self.pauseEvent)) 
			self.videoReceptionThread = threading.Thread(target = self.UDPself.udpcom.recepcionWebCam, args = (self.endEvent, self.pauseEvent)) 
			self.webCamThread.setDaemon(True)
			self.videoReceptionThread.setDaemon(True)
			self.webCamThread.start()
			self.videoReceptionThread.start()

		print("Esto no deberia haber ocurrido")

		

	def call_denied_handler(self, username):
		message = "{} no ha aceptado tu llamada.".format(username)
		self.gui.infoBox("LLamada saliente", message, parent=None)

	def call_busy_handler(self):
		message = "{} esta ocupado ahora mismo. Intentalo de nuevo mas tarde!".format(username)
		self.gui.infoBox("LLamada saliente", message, parent=None)

	#### FUNCIONES DE RECEPCION GENERICAS

	def parse_petition(self, text):
		fields = text.split(" ")
		command = fields[0]

		if command == "CALLING":

			self.calling_handler(username= fields[1], srcUDPport= fields[2])
		
		elif command == "CALL_HOLD":

			self.call_hold_handler(username= fields[1])

		elif command == "CALL_RESUME":

			self.call_resume_handler(username= fields[1])

		elif command == "CALL_END":

			self.call_end_handler(username= fields[1])

		elif command == "CALL_ACCEPTED":

			self.call_accepted_handler(username= fields[1], destUDPport= fields[2])

		elif command == "CALL_DENIED":

			self.call_denied_handler(username= fields[1])

		elif command == "CALL_BUSY":

			self.call_busy_handler()


	# Diseñada para funcionar en hilo
	# Esta funcion escucha en el puerto proporcionado en el fichero de configuracion mientras la aplicacion se este ejecutando
	# No se debe cerrar antes o no se podran recibir llamadas de otros usuarios
	def listening(self, endEvent):

		while not endEvent.isSet():

			# Asumimos que estos comandos caben en 1024 bytes
			conn, addr = self.socketRecepcion.accept()
			text = conn.recv(1024)

			if text: 

				self.parse_petition(text.decode('utf-8'))


	