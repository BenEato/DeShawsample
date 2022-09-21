#!/usr/bin/python3

from socket import socket, AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET
import time
import sqlite3
import re
from querycontacts import ContactFinder
from ip2geotools.databases.noncommercial import DbIpCity

banner = b"""
THIS IS A DUMMY SERVER TRACKING COMPROMISED HOSTS, CLOSE YOUR CLIENT IMMEDIATELY.
VOILATIONS WILL BE REPORTED TO THE ABUSE CONTACT ASSOCIATED WITH YOUR IP ADDRESS
"""
# Function to get the longitude and latitude from an IP address using API call
def geo(ip):
    try:
        response = DbIpCity.get(ip, api_key='free')
        print(response.latitude)
        print(response.longitude)
        return response.latitude, "#", response.longitude

    # NULL result for RFC1918 addresses
    except:
        return "0", "#", "0"


# Get source ip and port and store as values

def ipandport(inf):
    try:
        srcipandport = inf.split("raddr", 1)[1]
        infip, infprt = srcipandport.split(",")
        infprt = re.sub("[)>]", "", infprt)
        infip = re.sub("[=(']", "", infip)
        return infip, infprt
    except:
        return "0.0.0.0", "0"


# Function for adding entries to the database
def add_entry(uid, srcip, srcport, thetime, abuse, latitude, longitude, user, password, command):
    c.execute(
        '''INSERT INTO information VALUES ("{}","{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}") '''.format(uid,
                                                                                                                 srcip,
                                                                                                                 srcport,
                                                                                                                 thetime,
                                                                                                                 abuse,
                                                                                                                 latitude,
                                                                                                                 longitude,
                                                                                                                 user,
                                                                                                                 password,
                                                                                                            command))  # insert values
    connsq.commit()


# Create my Database
connsq = sqlite3.connect('conn_data.db')
c = connsq.cursor()
c.execute(
    '''CREATE TABLE IF NOT EXISTS information (uid text, source IP text, port text, time text, abuse text, latitude text, longitude text, user text, password text, command text) ''')  # add "information" table to database
connsq.commit()

#Set up my script to listen on port 23
sk = socket(AF_INET, SOCK_STREAM)
sk.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
sk.bind(('0.0.0.0', 23))

# Check if my database already exists and if so to add assign each entry an unique ID
try:
    testuid = c.execute("SELECT uid FROM information ORDER BY uid DESC LIMIT 1").fetchall()
    uid = int(testuid[0][0])

except:
    uid = 0

#Main loop
while True:
    sk.listen()
    conn, addr = sk.accept()
    conn.settimeout(10)
    constr = str(conn)
    # Sanitizing the connection information to place into database (src, prt and abuse)
    srcip, srcprt = ipandport(constr)
    curtime = time.time()
    print(srcip)
    print(srcprt)
    print(time.time())

    #Query API to get abuse email associated with IP address
    try:
        qf = ContactFinder()
        print(qf.find(srcip))
        abuse = qf.find(srcip)
        abuse = abuse[0]
    # Exception for local IP addresses
    except:
        abuse = "localip@localipaddress"
        print(abuse)

    # get geo data from the attacker's IP address
    LonLat = geo(srcip)
    latitude = LonLat[0]
    longitude = LonLat[2]

    # The code here offers a username, logs the response and does the same for the password
    # If this process completes a banner is presented to the host warning them to turn back.
    # If the host continues a dummy shell is presented and all further commands are logged to
    # the database
    try:
        conn.send(b"Welcome to the honeypot\nUsername:")
        username = None
        password = None
        command = None
        timeout = time.time()
        first_pass = True

        while True:
            data = conn.recv(1024)
            decoded_data = data.decode('utf-8', "ignore")
            print(decoded_data)
            print(len(data))

            # set timeout for stuck connections / clients not doing anything
            if time.time() > timeout + 20:
                conn.close()
                break

            if not len(data) > 0:
                continue
            # I need to ignore the data sent by the client when intially connecting,
            #I disovered by testing that this is always in the 20-30 range
            if first_pass and len(data) in range(20, 30):
                first_pass = False
                continue

            if not username:
                username = decoded_data
                conn.send(b"Password:")
                continue

            if not password:
                password = decoded_data
                conn.send(banner)
                conn.send(b"root@honeypie:~$")
                continue

            if not command:
                command = decoded_data
                # Incrementing my UID by 1 for each new entry in the Database
                uid = uid + 1
                add_entry(uid, srcip, srcprt, curtime, abuse, latitude, longitude, username, password, command)
                conn.send(b"root@honeypie:~$")
                continue
            # Any additional commands ran on the dummy shell are logged here and sent to DB
            command = f'{command}{decoded_data}'
            c.execute("""UPDATE information SET command = ? WHERE uid = ?""", (command, uid))
            connsq.commit()
            conn.send(b"root@honeypie:~$")
            continue

    except:

        conn.close()
        continue
