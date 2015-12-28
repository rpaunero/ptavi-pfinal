#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class Xml(ContentHandler):

    def __init__(self):

        self.tags = []
        self.dicc = {'account': ['username', 'passwd'],
                     'uaserver': ['ip', 'puerto'],
                     'rtpaudio': ['puerto'],
                     'regproxy': ['ip', 'puerto'],
                     'log': ['path']
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


if len(sys.argv) != 3:
    sys.exit('Usage: python uaclient.py method option')

FILE = sys.argv[1]
METHOD = sys.argv[2]
OPTION = sys.argv[3]

parser = make_parser()
cHandler = Xml()
parser.setContentHandler(cHandler)
parser.parse(open(FILE))
misDatos = cHandler.get_tags()
print(misDatos)


#if not '@' or ':' in LOGIN:
    #sys.exit('Usage: python client.py method receiver@IP:SIPport')

if METHOD not in ['INVITE', 'BYE']:
    sys.exit('Usage: python client.py method(INVITE/BYE) receiver@IP:SIPport')
else:
    LINE = METHOD
LINE = LINE + ' ' + 'sip:' + LOGIN + ' ' + 'SIP/2.0'

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((IP, PORT))


print("Enviando: " + LINE)
my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
data = my_socket.recv(1024)

instruccion = data.decode('utf-8')
print('Recibido -- ', instruccion)

if METHOD == 'INVITE':
    n1 = instruccion.split()[1]
    n2 = instruccion.split()[4]
    n3 = instruccion.split()[7]
    if n1 == '100' and n2 == '180' and n3 == '200':
        LINE = 'ACK' + ' ' + 'sip:' + LOGIN + ' ' + 'SIP/2.0'
        print("Enviando: " + LINE)
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n\r\n')
        data = my_socket.recv(1024)

print("Terminando socket...")

# Cerramos todo
my_socket.close()
print("Fin.")
