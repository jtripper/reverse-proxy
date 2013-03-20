#!/usr/bin/python2

#   proxy.py
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


from tor import Tor
from forwarder import Listener
from pwd import getpwnam
from grp import getgrnam
import config
import sys
import os
import signal

def handler(signum, frame):
  raise KeyboardInterrupt

if len(sys.argv) != 2:
  print "Usage: %s [start|stop|restart]" % sys.argv[0]
  quit() 

if sys.argv[1] == "start":
  if os.path.exists(".proxy.pid"):
    print " [*] Proxy already started, quitting! If it is not started, delete the lock file (.proxy.pid)."
    quit()

elif sys.argv[1] == "stop":
  if os.path.exists(".proxy.pid"):
    f = open(".proxy.pid")
    pid = int(f.readlines()[0])
    f.close()
    os.kill(pid, signal.SIGUSR1)
    os.remove(".proxy.pid")
  else:
    print " [*] Proxy not running!"
  quit()

elif sys.argv[1] == "restart":
  print " [*] Restarting proxy."
  if os.path.exists(".proxy.pid"):
    f = open(".proxy.pid")
    pid = int(f.readlines()[0])
    f.close()
    os.kill(pid, signal.SIGUSR1)
    os.remove(".proxy.pid")

proxy  = (config.remote_host, config.remote_port)
listen = (config.listener_host, config.listener_port)

print " [*] Starting tor instance."
tor = Tor(1)

print " [*] Starting proxy."
listener = Listener(listen, proxy, tor)
print " [*] Proxy ready to accept connections."

if config.__dict__.has_key("set_user"):
  print " [*] Dropping uid to %s" % config.set_user
  try:
    os.setuid(getpwnam(config.set_user)[2])
  except:
    print " [*] Cannot drop priviledges! Quitting."
    quit()

if config.__dict__.has_key("set_group"):
  print " [*] Dropping gid to %s" % config.set_group
  try:
    os.setgid(getgrnam(config.set_user)[2])
  except:
    print " [*] Cannot drop privideges! Quitting."
    quit()

if config.__dict__.has_key("daemon") and config.daemon:
  print " [*] Backgrounding process."
  if os.fork() != 0: quit()
  if os.fork() != 0: quit()
  signal.signal(signal.SIGUSR1, handler)

f = open(".proxy.pid", "w")
f.write("%d" % os.getpid())
f.close()

while 1:
  try:
    listener.manage_connections()
  except KeyboardInterrupt:
    print " [*] Stopping tor instance and quitting."

    if os.path.exists(".proxy.pid"):
      os.remove(".proxy.pid")

    tor.kill_tor()
    listener.close()
    quit()
