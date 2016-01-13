#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Servidor que hace funciones de proxy y Registrar
"""

import socketserver
import socket
import sys
import os.path
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import json
import time
import random
from uaserver import makeLog
import hashlib

class Keep_prXml(ContentHandler):

    def __init__(self):

        self.tags = []
        self.dicc = {'server': ['name', 'ip', 'puerto'],
                     'database': ['path', 'passwdpath'],
                     'log': ['path']}

    def startElement(self, name, attrs):
        """
        Método que se llama cuando se abre una etiqueta
        """
        if name in self.dicc:
            tmpdic = {}
            for atributo in self.dicc[name]:
                tmpdic[atributo] = attrs.get(atributo, "")
            self.tags.append([name, tmpdic])

    def get_tags(self):
        return self.tags


class Proxy(socketserver.DatagramRequestHandler):

    dicc = {}

    def register2json(self):
        try:
            with open('registered.json', 'w') as ff:
                json.dump(self.dicc, ff)
        except:
            pass

    """
    Echo server class
    """
    def handle(self):
        """
        Identifica y procesa las peticiones del cliente
        """

        #Datos procedentes del cliente
        IP = self.client_address[0]
        PORT = self.client_address[1]

        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if not line:
                    break
            elemento = line.decode('utf-8')
            print("El cliente nos manda " + elemento)
            #Log
            Evento = ' Recived from ' + IP + ':' + str(PORT)
            Evento += ':' + elemento
            hora = time.time()
            makeLog(pathLog, hora, Evento)
    
            LINEA = elemento.split('\r\n')
            METHOD = elemento.split(' ')[0]
            direccion = LINEA[0].split(' ')[1].split(':')[1]
            nonce = random.randint(0, 999999999999999999999)
            if METHOD == 'REGISTER':
                if LINEA[2].split(' ')[0] != 'Authorization:':
                    LINE = "SIP/2.0 401 Unauthorized\r\n"
                    LINE += "WWW Authenticate: nonce="
                    LINE += str(nonce)
                else:
                    response = LINEA[2].split()[1].split('=')[1]
                    nonce = LINEA[2].split()[2].split('=')[1]
                    #Autenticacion
                    fichero = open(passwdpath)  
                    datos = fichero.readlines()
                    print('DATOS:' + str(datos))
                    registradosdicc = {}
                    for usuario in datos:
                        passwd = usuario.split()[1]
                        name = usuario.split()[0]
                        registradosdicc[name]= passwd
                    print(registradosdicc)
                    passwdClient = registradosdicc[direccion]
                    
                    nonceB = (bytes(str(nonce), 'utf-8'))
                    print('nonce ' + str(nonce))
                    passwdClientB = (bytes(passwdClient, 'utf-8'))
                    print('passwdClientB ' + str(passwdClientB))
                    #Generamos response
                    m = hashlib.md5()
                    m.update(passwdClientB + nonceB)
                    response1 = m.hexdigest()
                    print('response' + response)
                    print('response1' + response1)
                    if response != response1:
                        LINE = "SIP/2.0 401 Unauthorized\r\n" 
                    else:
                        formato = '%Y-%m-%d %H:%M:%S' 
                        time_expires1 = time.gmtime(time.time() + int(LINEA[1].split(' ')[1]))
                        time_expires = time.strftime(formato, time_expires1)
                        current_time1 = time.gmtime(time.time())
                        current_time = time.strftime(formato, current_time1)
                        #Puerto del server
                        PORT_S = LINEA[0].split(' ')[1].split(':')[2]
                        self.dicc[direccion] = [IP, PORT_S, time_expires]
                        print('IP traza:' + IP)
                        print('Expires traza:' + time_expires)
                        print(time_expires + ('....') + current_time)

                        temp_list = []
                        for usuario in self.dicc:
                            usuario_time = self.dicc[usuario][2]
                            if (time.strptime(usuario_time, formato) <= current_time1):
                                temp_list.append(usuario)
                        for usuario in temp_list:
                            del self.dicc[usuario]
                            print('eliminamos:' + usuario)
                        if  LINEA[1].split(' ')[0] == 'Expires:':
                            LINE = "SIP/2.0 200 OK\r\n\r\n"
                            self.register2json()
                        else:
                            LINE = "SIP/2.0 400 Bad Request\r\n\r\n"
                print("Enviando: " + LINE)
                self.wfile.write(bytes(LINE,"utf-8"))
                #Log
                Evento = ' Send to ' + IP + ':' + str(PORT)
                Evento += ':' + LINE
                hora = time.time()
                makeLog(pathLog, hora, Evento)
            else:
                if direccion not in self.dicc:
                    LINE = "SIP/2.0 404 User Not Found\r\n\r\n"
                    print("Enviando: " + LINE)
                    self.wfile.write(bytes(LINE,"utf-8"))
                    #Log
                    Evento = ' Send to ' + IP + ':' + str(PORT)
                    Evento += ':' + LINE
                    hora = time.time()
                    makeLog(pathLog, hora, Evento)
                else:
                    IPs = self.dicc[direccion][0]
                    PORTs = self.dicc[direccion][1]
                    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    my_socket.connect((IPs, int(PORTs)))
                    print("Reenviando: " + elemento)
                    my_socket.send(bytes(elemento, 'utf-8') + b'\r\n')
                    #Log
                    Evento = ' Send to ' + IPs + ':' + str(PORTs)
                    Evento += ':' + elemento
                    hora = time.time()
                    makeLog(pathLog, hora, Evento)

                    data = my_socket.recv(1024)
                    instruccion = data.decode('utf-8')
                    print('Recibido -- ', instruccion)
                    self.wfile.write(data)
                    #Log
                    Evento = ' Recived from ' + IP + ':' + str(PORT)
                    Evento += ':' + instruccion
                    hora = time.time()
                    makeLog(pathLog, hora, Evento)
                     


if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.exit('Usage: python proxyregistrar.py config')

    FILE = sys.argv[1]

    if not os.path.exists(FILE):
        sys.exit('Usage: audio file does not exists')


    # Manejamos el fichero de configuración
    parser = make_parser()
    cHandler = Keep_prXml()
    parser.setContentHandler(cHandler)
    parser.parse(open(FILE))
    DatosXml = cHandler.get_tags()
    #print(DatosXml) 

    #Guardo datos del Xml (pr.xml)
    name = DatosXml[0][1]['name']
    ip = DatosXml[0][1]['ip']
    portProxy = DatosXml[0][1]['puerto']
    pathDatabase = DatosXml[1][1]['path']
    passwdpath = DatosXml[1][1]['passwdpath']
    pathLog = DatosXml[2][1]['path']

    print('Server ' + name + ' listening at port ' + portProxy + '...')

    proxy_serv = socketserver.UDPServer((ip, int(portProxy)), Proxy)
    proxy_serv.serve_forever()
   
