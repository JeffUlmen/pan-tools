import requests
import socket
import sys, getopt

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from dns import resolver,reversename

#use beautifulsoup to parse xml tags easily and effortlessly. Much easier than lxml module
from bs4 import BeautifulSoup as bs

import ulmenutils


def show_sys_info( hostname, key ):
   cmd = """<show><system><info></info></system></show>"""
   r = requests.get("https://" + hostname + "/api/?type=op&cmd={}&key={}".format(cmd,key),verify=False)
   output = bs(r.content,'html.parser')
   print("The hostname is " + (output.response.result.system.hostname).text)
   print("The management ip address and mask is " + (output.find('ip-address')).text + " " + (output.response.result.system.netmask).text)
   print("The management interface default gateway is " + (output.find('default-gateway')).text)
   print("PAN OS version is " + (output.find('sw-version')).text)
   return


#Get PTR record
def get_ptr( ip ):
   myresolver = resolver.Resolver()
   myresolver.timeout = 4
   myresolver.lifetime = 4
   addr = reversename.from_address( ip )
   try:
      x = myresolver.query(addr,"PTR")[0]
   except:
      x = "--"
      pass
   return str( x )


#Get MAC OUI
def get_mac( mac ):
   url = "http://macvendors.co/api/vendorname/" + mac
   myResponse = requests.get(url)
   oui = ""
   if myResponse.ok:
      v1 = str( myResponse.content ).lstrip( "b'" )
      oui = v1.rstrip( "'" )
   return oui


def main(argv):

   if len( argv ) != 1:
      print( "ipandmac.py <hostname>\n" )
      sys.exit()

   key = ulmenutils.u_get_key( argv[0] )
   show_sys_info( argv[0], key )

   cmd = """<show><arp><entry name='all'/></arp></show>"""
   r = requests.get("https://" + argv[0] + "/api/?type=op&cmd={}&key={}".format(cmd,key),verify=False)
   output = bs(r.content,'html.parser')

   x = 1
   ip_addr = ""
   mac_addr = ""
   interface = ""
   prior_interface = ""
   zone = ""
   for div in ( output.find_all(["ip", "mac", "interface"]) ):
      if x == 1:
         ip_addr = div.text
         ip_ptr = get_ptr( div.text )
      if x == 2:
         mac_addr = div.text
         mac_oui = get_mac( div.text )
      if x == 3:
         interface = div.text
         if prior_interface != interface:
            cmd = "<show><interface>" + interface + "</interface></show>"
            r = requests.get("https://" + argv[0] + "/api/?type=op&cmd={}&key={}".format(cmd,key),verify=False)
            int_output = bs(r.content,'html.parser')
            zone = int_output.zone.text

         print( interface.ljust( 15 ), zone.ljust( 25 ), ip_addr.ljust( 15 ), ip_ptr.ljust( 30 ), mac_addr.ljust( 18 ), mac_oui )
         prior_interface = interface
         x = 0
      x = x+1

if __name__== "__main__":
   #main(sys.argv)
   main(sys.argv[1:])  ##Doesn't pass script name
