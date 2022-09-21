# DeShawsample


Telnet Honeypot:

This script listens on port 23 for incoming connections and serves a dummy shell to any host which attempts to connect the server. The host is presented with a username and password prompt and then a warning banner. If the host continues beyond this point several data points are written to an SQLite database. This is a deliberate design choice to remove any false positive results such as port scans.

 

The database is named conn_data.db and will be created in the same directory that the script is run from.

 

The data points that this script collects include:

Source IP address and port

Time

Geolocation of IP address via API

The abuse contact associated with the IP address via API

Username and password provided

Any additional commands entered

 

This script forms part of a wider project which includes a front-end using Grafana to display the data gathered and an additional script which will poll the database weekly and generate a single email to the abuse email associated with each IP address which contains information about all attacks received over the time period originating from IP addresses under their administration.

 

There are currently some issues with how some of the data presented to the host is formatted when using third party telnet clients such as Putty. In my use-case this is less of a concern because the attackers in this scenario are exclusively comprised of bots.

 

On the server side of things the script has proved extremely stable and has been running for 370 days and has over 74,000 entries in its database.

 

The script must run as root due to its utilization of a common port. Required dependencies are:

ip2geotools (https://pypi.org/project/ip2geotools/)

querycontacts (https://pypi.org/project/querycontacts/)

 

Thank you for your consideration,

