#   tor.py
#   (C) 2013 jtripper
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 1, or (at your option)
#   any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import socket
import struct
import os
import subprocess
import signal
import shutil

class Tor:
  def __init__(self, tor_instance_number):
    self.tor_host     = "127.0.0.1"
    self.tor_port     = 9052 + tor_instance_number
    self.control_host = "127.0.0.1"
    self.control_port = 10052 + tor_instance_number
    self.tor_instance_number = tor_instance_number
    self.create_tor()

  # Restart this tor instance
  def restart_tor(self):
    self.tor.kill()
    self.create_tor()

  # Kill this tor instance and remove the data directory
  def kill_tor(self):
    try:
      self.tor.kill()
      shutil.rmtree("%s/.tor%d" % (os.getcwd(), self.tor_instance_number), ignore_errors=True)
    except:
      pass

  # Create new tor instance (write out simple configuration and then run in background)
  def create_tor(self):
    torrc  = "SocksPort %d\n" % self.tor_port
    torrc += "RunAsDaemon 0\n"
    torrc += "DataDirectory %s/.tor%d\n" % (os.getcwd(), self.tor_instance_number)
    torrc += "ControlPort %d\n" % self.control_port
    
    try:
      os.mkdir(".tor%d" % self.tor_instance_number, 0700)
    except:
      pass

    torrc_handle = open(".tor%d/torrc" % self.tor_instance_number, "w")
    torrc_handle.write(torrc)
    torrc_handle.close()

    f = open("/dev/null", "w")
    self.tor = subprocess.Popen("tor -f .tor%d/torrc" % self.tor_instance_number, stdout=f, stderr=f, shell=True)

# TorForwarder class
class TorForwarder:
  def __init__(self, tor, proxy, request):
    self.proxy = proxy

    # Connect to socks proxy
    self.forwarder = socket.socket()
    self.forwarder.connect((tor.tor_host, int(tor.tor_port)))

    self.connected = 0
    # Begin socks negotiation
    self.negotiate_socks()

    self.request   = request

  # Socket send wrapper
  def send(self, data):
    self.forwarder.send(data)

  # Socket receive wrapper
  def recv(self, size):
    # If socks negotiation is not complete call the socks negotiation function
    if self.connected <= 2:
      self.negotiate_socks()
    # Else read from socket and return data
    else:
      data = self.forwarder.recv(size)
      return data

  # Negotiate socks connection
  def negotiate_socks(self):
    # First send socks handshake
    if self.connected == 0:
      self.forwarder.send("\x05\x01\x00")

    # Wait for socks handshake response
    elif self.connected == 1:
      # If handshake failed restart 
      if self.forwarder.recv(2) != "\x05\x00":
        self.connected = 0
        self.negotiate_socks()
        return

      # Else send the host handshake
      port   = struct.pack("!H", self.proxy[1])
      length = chr(len(self.proxy[0]))
      self.forwarder.send(("\x05\x01\x00\x03%s%s%s" % (length, self.proxy[0], port)))

    # Wait for confirmation
    elif self.connected == 2:
      # If confirmation is bad, restart
      if self.forwarder.recv(10) != "\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00":
        self.connected = 0
        self.negotiate_socks()
        return

    # Increment connected variable
    self.connected += 1

    # If connection is complete start sending data
    if self.connected == 3:
      self.request.recv()

  def close(self):
    self.forwarder.close()

  def fileno(self):
    return self.forwarder.fileno()
