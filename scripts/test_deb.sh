#!/bin/sh
# Exercise APT installation/removal in an isolated container, not on the host.
set -eu
package=$(realpath "${1:?Usage: sh scripts/test_deb.sh /path/to/package.deb}")
directory=$(dirname "$package")
filename=$(basename "$package")
docker run --rm -i -v "$directory:/packages:ro" ubuntu:26.04 /bin/bash -s -- "$filename" <<'CONTAINER'
set -eu
export DEBIAN_FRONTEND=noninteractive
trap 'tail -n 45 /tmp/package-test.log' ERR
apt-get update >/tmp/package-test.log 2>&1
apt-get install -y -o 'Dpkg::Options::=--path-include=/usr/share/doc/kamalt-command/*' "/packages/$1" >>/tmp/package-test.log 2>&1
dpkg-query -W kamalt-command
dpkg --verify kamalt-command
/usr/bin/python3 /usr/share/kamalt-command/backend.py status
test ! -e /etc/keyd/kamalt-command.conf
apt-get remove -y kamalt-command >>/tmp/package-test.log 2>&1
test ! -e /usr/bin/kamalt-command
test ! -e /usr/libexec/kamalt-command-backend
/usr/bin/python3 -c 'print("Isolated Ubuntu 26.04 package installation and removal passed")'
CONTAINER
