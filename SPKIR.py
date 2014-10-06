#!/usr/bin/env python

USAGE = """

GP- This has been modified to make it a generic raw socket connection, with <CR><LF>

This program allows direct user iteraction with the RASPPS instrument via a socket.


USAGE:
    RAS_PPS_testing.py address port  # connect to instrument on address:port
    RAS_PPS_testing.py port          # connect to instrument on localhost:port

Example:
    RAS_PPS_testing.py 10.31.8.7 4002
    
To save output to screen and to a log file:

    RAS_PPS_testing.py 10.31.8.7 4002 | tee file.txt

It establishes a TCP connection with the provided service, starts a thread to
print all incoming data from the associated socket, and goes into a loop to
dispach commands from the user.

The commands are:
    - an empty string --> sends a '\r\n' (<CR><LF>)
    - the command 'wake' sends 5 control-Cs that wake and enable the RAS and PPS
    - the command 'autoTemp' starts a query of the Temp probe, only when connected to the correct port (4002)
    - once autoTemp enabled, any key followed by enter will exit autosample mode
    - the command 'autoRAS' starts a 200 burn-in simulation of the RAS, only when connected to the correct port (4001)
    - once autoRAS enabled, any key followed by enter will exit autosample mode
    - the command 'autoPPS' starts a 200 burn-in simulation of the PPS, only when connected to the correct port (4003)
    - once autoPPS enabled, any key followed by enter will exit autosample mode
    - The letter 'q' --> quits the program
    - Any other non-empty string --> sends the string followed by a '\r\n' (<CR><LF>)


"""

__author__ = 'Giora Proskurowski modified original Carlos Rueda'
__license__ = 'Apache 2.0'

import sys
import socket
import os
import time
import select

from threading import Thread


class _Recv(Thread):
    """
    Thread to receive and print data.
    """

    def __init__(self, conn):
        Thread.__init__(self, name="_Recv")
        self._conn = conn
        self._last_line = ''
        self._new_line = ''
        self.setDaemon(True)

    def _update_lines(self, recv):
        if recv == '\n':
            self._last_line = self._new_line
            self._new_line = ''
            return True
        else:
            self._new_line += recv
            return False

    def run(self):
        print "### _Recv running."
        while True:
            recv = self._conn.recv(1)
            newline = self._update_lines(recv)
            os.write(sys.stdout.fileno(), recv)
            sys.stdout.flush()


class _Direct(object):
    """
    Main program.
    """

    def __init__(self, host, port):
        """
        Establishes the connection and starts the receiving thread.
        """
        print "### connecting to %s:%s" % (host, port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((host, port))
        self._bt = _Recv(self._sock)
        self._bt.start()

    def run(self):
        #        """
        #         Dispaches user commands.
        #         """
        while True:

            cmd = sys.stdin.readline()

            cmd = cmd.strip()

            if cmd == "^C":
                #print "### sending '%s'" % cmd
                self.send_control('c')

            elif cmd == "^S":
                print "### sending '%s'" % cmd
                self.send_control('s')

            elif cmd == "^A":
                #print "### sending '%s'" % cmd
                self.send_control('A')

            elif cmd == "^P":
                #print "### sending '%s'" % cmd
                self.send_control('P')

            elif cmd == "^U":
                #print "### sending '%s'" % cmd
                self.send_control('U')

            elif cmd == "^R":
                #print "### sending '%s'" % cmd
                self.send_control('R')

            elif cmd == "q":
                #print "### exiting"
                break

            else:
                #print "### sending '%s'" % cmd
                self.sendCharacters(cmd)
                self.send('\r')

        self.stop()


    def stop(self):
        self._sock.close()

    def send(self, s):
        """
        Sends a string. Returns the number of bytes written.
        """
        c = os.write(self._sock.fileno(), s)
        return c

    def send_control(self, char):
        """
        Sends a control character.
        @param char must satisfy 'a' <= char.lower() <= 'z'
        """
        char = char.lower()
        assert 'a' <= char <= 'z'
        a = ord(char)
        a = a - ord('a') + 1
        return self.send(chr(a))


    def sendCharacters(self, s):
        """
        Sends a string one char at a time with a delay between each
        """
        for c in s:
            self.send(c)
            time.sleep(.1)


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print USAGE
        exit()

    if len(sys.argv) == 2:
        host = 'localhost'
        port = int(sys.argv[1])
    else:
        host = sys.argv[1]
        port = int(sys.argv[2])

    direct = _Direct(host, port)
    direct.run()
