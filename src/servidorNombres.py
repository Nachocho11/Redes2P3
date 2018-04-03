import socket
import time

class servidorNombres:
	socketCliente = None
	portCliente = None
	portSD = None
	bufferLenght = 1024
	# Devuelve el puerto del cliente

	def inicializacionPuertos(self):
		d = {}
		try:
			with open("client.conf", "r") as f:
				for line in f:
				    (key, val) = line.split()
				    d[key] = val
		except EnvironmentError:
			return None
		self.portSD = d['portSD']
		self.portCliente = d['portCliente']
		return


	# Devuelve el socket creado

	def conectarSocket(self):
		if (self.portSD == None):
			return None
		nombreSevidor = "vega.ii.uam.es"
		self.socketCliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socketCliente.connect((nombreSevidor,int(self.portSD)))
		return 

	def solicitarUsername(self, nick, pwd):
		ip_address = socket.gethostbyname(socket.getfqdn()) # Internet dice que pue fallar pero no se mu bien
		if (self.portCliente == None):
			return None

		mensaje = "REGISTER "+nick+" "+ip_address+" "+self.portCliente+" "+pwd+" "+" V1"
		self.socketCliente.send(bytes(mensaje, 'utf-8'))
		aux = self.socketCliente.recv(1024)

		respuesta = aux.decode('utf-8')

		if respuesta == "NOK WRONG_PASS":
			return None

		# Guardamos los datos

		with open("authentication.dat", "w") as f:
			f.write('username '+ nick+'\n')
			f.write('pwd '+ pwd + '\n')

		return "OK"  # DE MOMENTO NO HAGO NA CON EL NICK Y EL TS, HARA FALTA?

	# lo haremos cada vez que un usuario se conecte automaticamente (sin introducir credenciales)
	# obviamente, antes permitirle iniciar sesion automaticamente , si falla, al login
	def renovarUsername(self, username, pwd):

		ip_address = socket.gethostbyname(socket.getfqdn())

		if self.portCliente == None:
			return None

		mensaje = "REGISTER "+username+" "+ip_address+" "+self.portCliente+" "+pwd+" "+" V1"
		self.socketCliente.send(bytes(mensaje, 'utf-8'))
		aux = self.socketCliente.recv(1024)

		respuesta = aux.decode('utf-8')

		if respuesta == "NOK WRONG_PASS":
			return None

		return "OK"

	def getIPUsuario(self, username):
		mensaje = "QUERY " + username
		self.socketCliente.send(bytes(mensaje, 'utf-8'))
		aux = self.socketCliente.recv(1024)

		respuesta = aux.decode('utf-8')

		if respuesta == "NOK USER_UNKNOWN":
			return None

		fields = respuesta.split(" ")
		ip = fields[3]

		return ip


	def listarUsuarios(self):
		mensaje = "LIST_USERS"
		self.socketCliente.send(bytes(mensaje, 'utf-8'))
		# esperamos este tiempo para asegurarnos de que llegan todos los bloques (?)
		time.sleep(1)
		aux = self.socketCliente.recv(self.bufferLenght).decode('utf-8')
		respuesta = aux
		while len(aux) == self.bufferLenght:
			aux = self.socketCliente.recv(self.bufferLenght).decode('utf-8')
			# + en strings equivale a concatenar
			respuesta += aux


		if respuesta == "NOK USER_UNKNOWN":
			return None

		userList = []
		users = respuesta.split("#")
		# el primer usuario no esta separado de los primeros mensajes (OK USERS_LIST)
		# se le da un tratamiento distinto
		fields = users[0].split(" ")
		userList.append(fields[3])
		
		# no incluimos el ultimo
		for user in users[1:-1]:
			fields = user.split(" ")
			userList.append(fields[0])

		return userList

	#def solicitarConexionUsuario(self, username, port):

		# enviamos solicitud CALLING (debe incluir PUERTO RECEPCION VIDEO)
		# esperamos respuesta CALL_ACCEPTED
		# respuesta incluye: OK/NO, PUERTO AL QUE MANDAR VIDEO
		# se inicia la transmision de video

	def cerrarConexion(self):
		mensaje = "QUIT"
		self.socketCliente.send(bytes(mensaje, 'utf-8'))
		respuesta = self.socketCliente.recv(1024)
		self.socketCliente.close()
		return respuesta