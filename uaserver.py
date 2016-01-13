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
import time


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


def makeLog(pathlog, hora, Evento):
    fichero = open(pathlog, 'a')
    hora = time.gmtime(float(hora))
    fichero.write(time.strftime('%Y%m%d%H%M%S', hora))
    Evento = Evento.replace('\r\n', ' ')
    fichero.write(Evento + '\r\n')
    fichero.close()


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
            #Log
            Evento = ' Recived from ' + ipProxy + ':' + portProxy
            Evento += ':' + elemento
            hora = time.time()
            makeLog(pathLog, hora, Evento)
            METHOD = elemento.split(' ')[0]
            if METHOD == 'INVITE':
            #Obtenemos IP del emisor
                ipEmisor = linea[4].split(' ')[1]
                LINE = "SIP/2.0 100 Trying" + "\r\n\r\n"
                LINE += "SIP/2.0 180 Ring" + "\r\n\r\n"
                LINE += "SIP/2.0 200 OK" + "\r\n\r\n"
                LINE += "Content-Type: application/sdp\r\n\r\n"
                LINE += "v=0\r\n"
                LINE += "o=" + username + " "
                LINE += ipServer + "\r\ns=misesion\r\n"
                LINE += "t=0\r\n"
                LINE += "m=audio " + portRtp + " RTP\r\n"
            elif METHOD == 'BYE':
                LINE = "SIP/2.0 200 OK" + "\r\n\r\n"
            elif METHOD == 'ACK':
                #VLC
                aEjecutarVLC = 'cvlc rtp://@127.0.0.1:'
                aEjecutarVLC += portRtp + '2> /dev/null &'
                os.system(aEjecutarVLC)
                #Envio del audio
                aEjecutar = './mp32rtp -i ' + ipServer
                aEjecutar = aEjecutar + ' -p ' + portRtp + '< ' + pathAudio
                print("Vamos a ejecutar", aEjecutar)
                os.system(aEjecutar)
                print("Ejecucion finalizada")
            elif METHOD not in ['INVITE', 'ACK', 'BYE']:
                LINE = "SIP/2.0 405 Method Not Allowed" + "\r\n\r\n"
            else:
                LINE = "SIP/2.0 400 Bad Request" + "\r\n\r\n"

            if METHOD != 'ACK':
                print("Enviando: " + LINE)
                self.wfile.write(bytes(LINE, "utf-8"))
                #Log
                Evento = ' Send to ' + ipProxy + ':' + portProxy
                Evento += ':' + LINE
                hora = time.time()
                makeLog(pathLog, hora, Evento)

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
