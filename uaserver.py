#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import os.path
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

class Keep_uaXml(ContentHandler):

    def __init__(self):

        self.tags = []
        self.dicc = {'account': ['username', 'passwd'],
                     'uaserver': ['ip', 'puerto'],
                     'rtpaudio': ['puerto'],
                     'regproxy': ['ip', 'puerto'],
                     'log': ['path'],
                     'audio': ['path']}

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
        

class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if not line:
                    break
            elemento = line.decode('utf-8')
            linea = elemento.split('\r\n')
            print("El cliente nos manda " + elemento)
            METHOD = elemento.split(' ')[0]
            if METHOD == 'INVITE':
            #Obtenemos IP del emisor
                ipEmisor = linea[4].split(' ')[1]

                self.wfile.write(b"SIP/2.0 100 Trying" + b"\r\n\r\n")
                self.wfile.write(b"SIP/2.0 180 Ring" + b"\r\n\r\n")
                self.wfile.write(b"SIP/2.0 200 OK" + b"\r\n\r\n")
                self.wfile.write(b"Content-Type: application/sdp\r\n\r\n")
                self.wfile.write(b"v=0\r\n")
                self.wfile.write(b"o=" + bytes(username, 'utf-8') + b" ")
                self.wfile.write(bytes(ipServer, 'utf-8') + b"\r\ns=misesion\r\n")
                self.wfile.write(b"t=0\r\n")
                self.wfile.write(b"m=audio " + bytes(portRtp, 'utf-8') + b" RTP\r\n")
            elif METHOD == 'BYE':
                self.wfile.write(b"SIP/2.0 200 OK" + b"\r\n\r\n")
            elif METHOD == 'ACK':
       # aEjecutar es un string con lo que se ha de ejecutar en la shell
                aEjecutar = './mp32rtp -i ' + ipServer
                aEjecutar = aEjecutar + ' -p ' + portRtp + '< ' + pathAudio
                print("Vamos a ejecutar", aEjecutar)
                os.system(aEjecutar)
                print("Ejecucion finalizada")
            elif METHOD not in ['INVITE', 'ACK', 'BYE']:
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed" +
                                 b"\r\n\r\n")
            else:
                self.wfile.write(b"SIP/2.0 400 Bad Request" + b"\r\n\r\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage: python uaserver.py config')

    FILE = sys.argv[1]

    if not os.path.exists(FILE):
        sys.exit('Usage: audio file does not exists')

    parser = make_parser()
    cHandler = Keep_uaXml()
    parser.setContentHandler(cHandler)
    parser.parse(open(FILE))
    DatosXml = cHandler.get_tags()
    #print(DatosXml)    

#Guardo datos del Xml (uan.xml)
    username = DatosXml[0][1]['username']
    passwd = DatosXml[0][1]['passwd']
    ipServer = DatosXml[1][1]['ip']
    portServer = DatosXml[1][1]['puerto']
    portRtp = DatosXml[2][1]['puerto']
    ipProxy = DatosXml[3][1]['ip']
    portProxy = DatosXml[3][1]['puerto']
    pathLog = DatosXml[4][1]['path']
    pathAudio = DatosXml[5][1]['path']


    print('Listening...')

    serv = socketserver.UDPServer((ipServer, int(portServer)), EchoHandler)
    print("Lanzando servidor UDP de eco...")
    serv.serve_forever()
