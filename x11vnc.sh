#!/bin/bash
exec x11vnc -ncache 10 -ncache_cr -display :1 -forever -shared -logappend /var/log/x11vnc.log -noipv6
