#   forwarder.py
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
import select
import struct
from tor import TorForwarder
import random

# Request object for managing a open proxy connection
class Request:
  def __init__(self, tor, client_socket, proxy):
    self.client    = client_socket

    # Create a tor forwarder
    self.forwarder = TorForwarder(tor, proxy, self)
    self.staged    = ""

  # recv wrapper
  def recv(self):
    # if the forwarder is ready
    if self.forwarder.connected > 2:
      # forward any staged data
      if self.staged != "":
        self.forwarder.send(self.staged)
        self.staged = ""
      # receive any new data and forward it
      else:
        data = self.client.recv(1024)
        if not data: return -1

        self.forwarder.send(data)
    # stage data from client
    else:
      self.staged += self.client.recv(1024)

  # call the forwarder receive wrapper
  def send(self):
    data = self.forwarder.recv(10000)
    # forward data to client
    self.client.send(data)

  def fileno(self):
    return self.client.fileno()

  def close(self):
    self.client.close()
    self.forwarder.close()

# Forwarding proxy listener class
class Listener:
  def __init__(self, host, proxy, tor):
    self.host  = host
    self.proxy = proxy
    self.tor   = tor

    # Create the listener socket
    self.s = socket.socket()
    # Bind to given host
    self.s.bind(self.host)
    # Start listener
    self.s.listen(5)

    # Create list of open connections for select
    self.oc = [ self.s ]

  # Accept wrapper function that instantiates a Request object and appends it to our open
  # connections list
  def accept(self):
    client, addr = self.s.accept()
    print " [*] Accepted connection from %s:%d." % (addr[0], addr[1])
    r = Request(self.tor, client, self.proxy)
    self.oc.append(r)
    self.oc.append(r.forwarder)

  # Our select function
  def manage_connections(self):
    readable, writable, exceptional = select.select(self.oc, [], [])
    for s in readable:
      # If it is a Request object then call Request.recv
      if isinstance(s, Request):
        try:
          if s.recv() == -1:
            raise socket.error

        except socket.error as e:
          # If we errored out, remove from open connections list
          if s.forwarder in self.oc:
            self.oc.remove(s.forwarder)
          if s in self.oc:
            self.oc.remove(s)

      # If it is a TorForwarder
      elif isinstance(s, TorForwarder):
        try:
          # If socks negotiation is not complete, call the recv wrapper
          if s.connected <= 2:
            s.recv(1024)
          # Else call the Request.send function
          else:
            s.request.send()

        except socket.error as e:
          # If we errored out, remove from open connections list
          if s.request in self.oc:
            self.oc.remove(s.request)
          if s in self.oc:
            self.oc.remove(s)

      # Call self.accept if the listen socket it ready
      elif s.fileno() == self.s.fileno():
        self.accept()

  def close(self):
    self.s.close()
