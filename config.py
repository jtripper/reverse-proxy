# Host to forward traffic to
remote_host   = "xxxxxxxxxxxxxxxxxxx.onion"
remote_port   = 80

# Host to listen on
listener_host = "127.0.0.1"
listener_port = 8081

# User / group to drop priviledges to (useful if running on a port < 1024)
#set_user      = "nobody"
#set_group     = "nobody"

# Daemonize process
daemon        = True
