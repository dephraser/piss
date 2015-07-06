#!/usr/bin/env bash

# Get the directory we're working from
if [ -d /home/vagrant/sync ]; then
    DIR="/home/vagrant/sync"
else
    DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
fi

# Update packages
yum -y update

# Install build dependencies
yum groupinstall -y 'development tools'
yum install -y zlib-devel bzip2-devel openssl-devel xz-libs wget

# Download the Python source and unpack it
cd /tmp
wget --no-verbose http://www.python.org/ftp/python/2.7.10/Python-2.7.10.tar.xz
xz -d Python-2.7.10.tar.xz
tar -xvf Python-2.7.10.tar

# Enter the directory, configure, and install
cd Python-2.7.10
./configure --prefix=/usr/local
make
make altinstall

# Make sure `/usr/local/bin` is on your $PATH
export PATH="/usr/local/bin:$PATH"

# Install `setuptools`
cd /tmp
wget --no-verbose --no-check-certificate https://pypi.python.org/packages/source/s/setuptools/setuptools-18.0.1.tar.gz
tar -xvf setuptools-18.0.1.tar.gz
cd setuptools-18.0.1
python2.7 setup.py install

# Install `pip`
cd /tmp
curl -sS https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py | python2.7 -

# Install `virtualenv`
pip2.7 install virtualenv

# Install MongoDB
cd /etc/yum.repos.d/
wget --no-verbose https://repo.mongodb.org/yum/redhat/mongodb-org.repo
yum install -y mongodb-org

# Configuration for MongoDB
# Set the `ulimit` to a higher number
cd /etc/security/limits.d/
touch /etc/security/limits.d/99-mongodb-nproc.conf
cat <<EOF >> /etc/security/limits.d/99-mongodb-nproc.conf
*          soft    nproc     32768
root       soft    nproc     unlimited
EOF

# Disable `transparent_hugepage`
cat <<EOF >> /etc/rc.local
if test -f /sys/kernel/mm/transparent_hugepage/khugepaged/defrag; then
  echo 0 > /sys/kernel/mm/transparent_hugepage/khugepaged/defrag
fi
if test -f /sys/kernel/mm/transparent_hugepage/defrag; then
  echo never > /sys/kernel/mm/transparent_hugepage/defrag
fi
if test -f /sys/kernel/mm/transparent_hugepage/enabled; then
  echo never > /sys/kernel/mm/transparent_hugepage/enabled
fi
EOF

# Set readahead settings to 256 for MongoDB data device
echo "blockdev --setra 256 /dev/dm-1" >> /etc/rc.local

# Set the ulimit to a higher number
echo "ulimit -n 32768" >> /etc/rc.local

# Source the rc.local file so the changes take effect
source /etc/rc.local

# Change permissions so rc.local runs at boot
chmod +x /etc/rc.d/rc.local

# Start MongoDB
# NOTE: You can test that mongod is running by checking for a line reading
#     [initandlisten] waiting for connections on port <port>
# in /var/log/mongodb/mongod.log
service mongod start
chkconfig mongod on

# Restart MongoDB at the end of rc.local (We do this because Mongo starts
# earlier in the boot process than rc.local)
echo "service mongod restart" >> /etc/rc.local

