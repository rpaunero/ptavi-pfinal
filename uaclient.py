#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import os
import sys
from uaserver import Keep_uaXml
from uaserver import makeLog
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import hashlib
import time


if len(sys.argv) != 4:
    sys.exit('Usage: python uaclient.py config method option')

FILE = sys.argv[1]
METHOD = sys.argv[2]
OPTION = sys.argv[3]

# Manejamos el fichero de configuración
parser = make_parser()
cHandler = Keep_uaXml()
parser.setContentHandler(cHandler)
parser.parse(open(FILE))
DatosXml = cHandler.get_tags()
#print(DatosXml)


#Datos del Xml (uan.xml)
username = DatosXml[0][1]['username']
passwd = DatosXml[0][1]['passwd']
ipServer = DatosXml[1][1]['ip']
portServer = DatosXml[1][1]['puerto']
portRtp = DatosXml[2][1]['puerto']
ipProxy = DatosXml[3][1]['ip']
portProxy = DatosXml[3][1]['puerto']
pathLog = DatosXml[4][1]['path']
pathAudio = DatosXml[5][1]['path']


# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((ipProxy, int(portProxy)))

#Log
Evento = ' Starting... '
hora = time.time()
makeLog(pathLog, hora, Evento)
try:
    LINE = METHOD + " sip:"
    if METHOD == 'REGISTER':
        LINE = LINE + username + ":" + portServer
        LINE = LINE + " SIP/2.0\r\n" + "Expires: "
        LINE = LINE + OPTION + "\r\n"
        print("Enviando: " + LINE)
        #Log
        Evento = ' Send to ' + ipProxy + ':' + portProxy
        Evento += ':' + LINE
        hora = time.time()
        makeLog(pathLog, hora, Evento)

        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
        data = my_socket.recv(1024)
        instruccion = data.decode('utf-8')
        linea1 = instruccion.split('\r\n')[1]
        nonce = linea1.split(' ')[2].split(':')[0].split('=')[1]
        print('Recibido -- ', instruccion)
        #Log
        Evento = ' Recived from ' + ipProxy + ':' + portProxy
        Evento += ':' + instruccion
        hora = time.time()
        makeLog(pathLog, hora, Evento) 
        #Autenticacion 
        LINE1 = METHOD + " sip:"
        LINE1 += username + ":" + portServer
        LINE1 += " SIP/2.0\r\n" + "Expires: "
        LINE1 += OPTION + "\r\n"
        nonceB = (bytes(str(nonce), 'utf-8'))
        passwdB = (bytes(passwd, 'utf-8'))
        #Generamos response
        m = hashlib.md5()
        m.update(passwdB + nonceB)
        response = m.hexdigest()
        LINE1 += 'Authorization: response=' + str(response) + " " + 'nonce=' + nonce + "\r\n"


    elif METHOD == 'INVITE':
        LINE1 = METHOD + " sip:"
        LINE1 += OPTION + '\r\n'
        LINE1 += "Content-Type: application/sdp\r\n\r\n"
        LINE1 += "v=0\r\n"
        LINE1 += "o=" + username + " " + ipServer
        LINE1 += "\r\ns=misesion\r\n"
        LINE1 += "t=0\r\n"
        LINE1 += "m=audio " + portRtp +" RTP\r\n"
    elif METHOD == 'BYE':
        LINE1 = METHOD + " sip:"
        LINE1 += OPTION + " SIP/2.0\r\n"
            
        
    print("Enviando: " + LINE1)
    #Log
    Evento = ' Send to ' + ipProxy + ':' + portProxy
    Evento += ':' + LINE1
    hora = time.time()
    makeLog(pathLog, hora, Evento)

    my_socket.send(bytes(LINE1, 'utf-8') + b'\r\n')
    data = my_socket.recv(int(portProxy))

    instruccion = data.decode('utf-8')
    print('Recibido -- ', instruccion)
    #Log
    Evento = ' Recived from ' + ipProxy + ':' + portProxy
    Evento += ':' + instruccion
    hora = time.time()
    makeLog(pathLog, hora, Evento) 

    linea = instruccion.split('\r\n')
    ninstruccion = linea[0].split(' ')[1]
    #ACK
    if METHOD == 'INVITE' and int(ninstruccion) == 100:
        n1 = instruccion.split()[1]
        n2 = instruccion.split()[4]
        n3 = instruccion.split()[7]
        ipEmisor = linea[9].split(' ')[1]
        if n1 == '100' and n2 == '180' and n3 == '200':
            LINE = 'ACK' + ' ' + 'sip:' + OPTION + ' ' + 'SIP/2.0'
            print("Enviando: " + LINE)
            #Log
            Evento = ' Send to ' + ipProxy + ':' + portProxy
            Evento += ':' + LINE
            hora = time.time()
            makeLog(pathLog, hora, Evento)

            my_socket.send(bytes(LINE, 'utf-8') + b'\r\n\r\n')

            #Envio del audio
            aEjecutar = './mp32rtp -i ' + ipEmisor
            aEjecutar = aEjecutar + ' -p ' + portRtp + '< ' + pathAudio
            print("Vamos a ejecutar", aEjecutar)
            os.system(aEjecutar)
            print('Ejecucion finalizada')

    print("Terminando socket...")

    # Cerramos todo
    my_socket.close()
    print("Fin.")
    #Log
    Evento = ' Finishing. '
    hora = time.time()
    makeLog(pathLog, hora, Evento)

except socket.error:
    #Log
    Evento = ' Error: No server listening at '
    Evento += ipProxy + ' port ' + portProxy
    hora = time.time()
    makeLog(pathLog, hora, Evento)
    print(Evento)
