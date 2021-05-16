from ncclient import manager        # NETCONF client library - Needed to interact via NETCONF with the Device
import xmltodict                    # Library to convert XML to Python Dictionary - Needed to work on NETCONF XML DATA received
import xml.dom.minidom              # Library to parse and print "pretty" NETCONF XML data received
import json                         # Library to process JSON data - Needed to output "pretty" JSON converted data from NETCONF XML

# Device Connecting data (Devnet Sandbox IOS-XE)
# Juniper: device_params={‘name’:’junos’}
# Cisco:
#    CSR: device_params={‘name’:’csr’}
#    Nexus: device_params={‘name’:’nexus’}
#    IOS XR: device_params={‘name’:’iosxr’}
#    IOS XE: device_params={‘name’:’iosxe’}
#    Huawei:
#        device_params={‘name’:’huawei’}
#        device_params={‘name’:’huaweiyang’}
#        Nokia SR OS: device_params={‘name’:’sros’}
#        H3C: device_params={‘name’:’h3c’}
#        HP Comware: device_params={‘name’:’hpcomware’}
# Server or anything not in above: device_params={‘name’:’default’}

device1 = {"host":"10.10.20.48",
        "port":"830",
        "username":"developer",
        "password":"C1sco12345",
        "device_params":{"name":"csr"}
        }
device2= {"host":"ios-xe-mgmt.cisco.com",
        "port":"10000",
        "username":"developer",
        "password":"C1sco12345",
        "device_params":{"name":"csr"}
        }


# XML String with {} Variables at key places
# We will use .format to apply an inline replacement and keep this XML portion
# as a template for interface configuration via NETCONF
# NOTE: This was generated with yang-explorer
config_ifc_filter = '''
    <config>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces" xmlns:ip="urn:ietf:params:xml:ns:yang:ietf-ip">
        <interface>
          <name>{interface}</name>
          <description>{description}</description>
          <enabled>{state}</enabled>
          <ip:ipv4>
            <ip:address>
              <ip:ip>{ip}</ip:ip>
              <ip:netmask>{mask}</ip:netmask>
            </ip:address>
          </ip:ipv4>
        </interface>
      </interfaces>
    </config>
'''

config_ifc_filter_loopback = '''
    <config>
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
      <interface>
        <name>{interface}</name>
        <description>{description}</description>
        <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:softwareLoopback</type>
        <enabled>{state}</enabled>
        <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
          <address>
            <ip>{ip}</ip>
            <netmask>{mask}</netmask>
          </address>
        </ipv4>
        <ipv6 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip"/>
      </interface>
    </interfaces>
    </config>
'''

delete_ifc_filter = '''
    <config>
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
      <interface operation="delete">
        <name>{interface}</name>
      </interface>
    </interfaces>
    </config>
'''

delete_ifcip_filter = '''
    <config>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces" xmlns:ip="urn:ietf:params:xml:ns:yang:ietf-ip">
        <interface>
          <name>{interface}</name>
          <ip:ipv4>
            <ip:address operation="delete">
              <ip:ip>{ip}</ip:ip>
            </ip:address>
          </ip:ipv4>
        </interface>
      </interfaces>
    </config>
'''

# XML string to filter received data from NETCONF to only the interface configuration
# NOTE: this was created with yang-explorer
yang_filter = '''
    <filter>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface/>
      </interfaces>
    </filter>
'''


# Creation of the ncclient NETCONF manager object
# use of WITH keyword allows the automatic closure of the session stream once finished
with manager.connect(**device1,hostkey_verify=False) as connection: 
    configuration_xml = connection.get_config(source="running",filter=yang_filter)
    validation_response = connection.validate(source="running")
    if configuration_xml.ok: print("RESPONSE: OK")
    if validation_response.ok: print("VALIDATION: OK")
#    configuration_xml = connection.get(yang_filter)             # This is an alternative

# XMLDOM object to prettify the XML output later
xmldom = xml.dom.minidom.parseString(configuration_xml.xml)

# JSON data of the XML converted via XMLTODICT library
json_response = xmltodict.parse(configuration_xml.xml)

# Print NETCONF XML and JSON data received in a pretty format
print(f"{15 * '-'}|INITIAL CONFIGURATION (XML)|{15 * '-'}")
print(xmldom.toprettyxml(indent="  "))
print(f"{15 * '-'}|INITIAL CONFIGURATION (JSON)|{15 * '-'}")
print(json.dumps(json_response,indent=2))

# Walk through JSON data and print out programmatically some interface information
print(f"{15 * '-'}|PRINT TABLE WITH INTERFACE DETAIL (BEFORE change)|{15 * '-'}")
for interface in json_response["rpc-reply"]["data"]["interfaces"]["interface"]:
    name = interface['name']
    description = interface.get('description')
    state = interface['enabled']
    if interface['ipv4'].get('address'):
        address = interface['ipv4']['address']['ip']
        mask = interface['ipv4']['address']['netmask']
    else:
        address = mask = "No"
    print(f"name:{name:20} state:{state:10} IP:{address+'/'+mask:30} description:{description}")

# From here on we will CONFIGURE via NETCONF

# ----------------------------------------------------------------
# CONFIGURE IP ON GIGABITETHERNET2
# ----------------------------------------------------------------

# Create a specific configuration XML data from the template "config_ifc_filter" for the changes we want to push
change1 = config_ifc_filter.format(interface="GigabitEthernet2",description="Second interface",state="true",ip="1.1.1.1",mask="255.255.255.0")
print(f"{15 * '-'}|XML ENCODING of YANG model to change interface configuration |{15 * '-'}")
print(change1)
# Connection to the device via nccclient NETCONF
with manager.connect(**device1,hostkey_verify=False) as connection:
    connection_reply = connection.edit_config(change1,target="running")
    print(f"{15 * '-'}|REPLY of NETCONF CONFIGURATION CALL|{15 * '-'}")
    print(connection_reply) # reply OK if everything is fine
    # Retrieve updated CONFIGURATION from the device
    configuration_xml = connection.get_config(source="running",filter=yang_filter)

# XMLDOM object to prettify the XML output later
xmldom = xml.dom.minidom.parseString(configuration_xml.xml)

# JSON data of the XML converted via XMLTODICT library
json_response = xmltodict.parse(configuration_xml.xml)

# Print NETCONF XML and JSON data received in a pretty format
print(f"{15 * '-'}|UPDATED CONFIG IN XML FORMAT|{15 * '-'}")
print(xmldom.toprettyxml(indent="  "))
print(f"{15 * '-'}|UPDATED CONFIG IN JSON FORMAT|{15 * '-'}")
print(json.dumps(json_response,indent=2))

# print Again table data about the interfaces
print(f"{15 * '-'}|PRINT TABLE WITH INTERFACE DETAIL (post change)|{15 * '-'}")
for interface in json_response["rpc-reply"]["data"]["interfaces"]["interface"]:
    name = interface['name']
    description = interface.get('description')
    state = interface['enabled']
    if interface['ipv4'].get('address'):
        address = interface['ipv4']['address']['ip']
        mask = interface['ipv4']['address']['netmask']
    else:
        address = mask = "No"
    print(f"name:{name:20} state:{state:10} IP:{address+'/'+mask:30} description:{description}")


# ----------------------------------------------------------------
# DELETE IP OF GIGABITETHERNET2
# ----------------------------------------------------------------

# Create a specific configuration XML data from the template "delete_ifc_filter" for removing the interface IP
change2 = delete_ifcip_filter.format(interface="GigabitEthernet2",ip="1.1.1.1")
print(f"{15 * '-'}|XML ENCODING of YANG model to change interface configuration |{15 * '-'}")
print(change2)
# From here we will remove the configuration we added with NETCONF
with manager.connect(**device1,hostkey_verify=False) as connection:
    connection_reply = connection.edit_config(change2,target="running")
    print(f"{15 * '-'}|REPLY of NETCONF CONFIGURATION CALL|{15 * '-'}")
    print(connection_reply) # reply OK if everything is fine
    # Retrieve updated CONFIGURATION from the device
    configuration_xml = connection.get_config(source="running",filter=yang_filter)

# XMLDOM object to prettify the XML output later
xmldom = xml.dom.minidom.parseString(configuration_xml.xml)

# JSON data of the XML converted via XMLTODICT library
json_response = xmltodict.parse(configuration_xml.xml)

# Print NETCONF XML and JSON data received in a pretty format
print(f"{15 * '-'}|UPDATED CONFIG IN XML FORMAT|{15 * '-'}")
print(xmldom.toprettyxml(indent="  "))
print(f"{15 * '-'}|UPDATED CONFIG IN JSON FORMAT|{15 * '-'}")
print(json.dumps(json_response,indent=2))

# print Again table data about the interfaces
print(f"{15 * '-'}|PRINT TABLE WITH INTERFACE DETAIL (post change)|{15 * '-'}")
for interface in json_response["rpc-reply"]["data"]["interfaces"]["interface"]:
    name = interface['name']
    description = interface.get('description')
    state = interface['enabled']
    if interface['ipv4'].get('address'):
        address = interface['ipv4']['address']['ip']
        mask = interface['ipv4']['address']['netmask']
    else:
        address = mask = "No"
    print(f"name:{name:20} state:{state:10} IP:{address+'/'+mask:30} description:{description}")


# ----------------------------------------------------------------
# CONFIGURE LOOPBACK0
# ----------------------------------------------------------------

# Create a specific configuration XML data from the template "config_ifc_filter" for the changes we want to push
change3 = config_ifc_filter_loopback.format(interface="Loopback0",description="Loop interface",state="true",ip="7.7.7.7",mask="255.255.255.255")
print(f"{15 * '-'}|XML ENCODING of YANG model to change interface configuration |{15 * '-'}")
print(change3)
# Connection to the device via nccclient NETCONF
with manager.connect(**device1,hostkey_verify=False) as connection:
    connection_reply = connection.edit_config(change3,target="running")
    print(f"{15 * '-'}|REPLY of NETCONF CONFIGURATION CALL|{15 * '-'}")
    print(connection_reply) # reply OK if everything is fine
    # Retrieve updated CONFIGURATION from the device
    configuration_xml = connection.get_config(source="running",filter=yang_filter)

# XMLDOM object to prettify the XML output later
xmldom = xml.dom.minidom.parseString(configuration_xml.xml)

# JSON data of the XML converted via XMLTODICT library
json_response = xmltodict.parse(configuration_xml.xml)

# Print NETCONF XML and JSON data received in a pretty format
print(f"{15 * '-'}|UPDATED CONFIG IN XML FORMAT|{15 * '-'}")
print(xmldom.toprettyxml(indent="  "))
print(f"{15 * '-'}|UPDATED CONFIG IN JSON FORMAT|{15 * '-'}")
print(json.dumps(json_response,indent=2))

# print Again table data about the interfaces
print(f"{15 * '-'}|PRINT TABLE WITH INTERFACE DETAIL (post change)|{15 * '-'}")
for interface in json_response["rpc-reply"]["data"]["interfaces"]["interface"]:
    name = interface['name']
    description = interface.get('description')
    state = interface['enabled']
    if interface['ipv4'].get('address'):
        address = interface['ipv4']['address']['ip']
        mask = interface['ipv4']['address']['netmask']
    else:
        address = mask = "No"
    print(f"name:{name:20} state:{state:10} IP:{address+'/'+mask:30} description:{description}")




# ----------------------------------------------------------------
# DELETE LOOPBACK
# ----------------------------------------------------------------

change4 = delete_ifc_filter.format(interface="Loopback0")
print(f"{15 * '-'}|XML ENCODING of YANG model to change interface configuration |{15 * '-'}")
print(change4)
# From here we will remove the configuration we added with NETCONF
with manager.connect(**device1,hostkey_verify=False) as connection:
    connection_reply = connection.edit_config(change4,target="running")
    print(f"{15 * '-'}|REPLY of NETCONF CONFIGURATION CALL|{15 * '-'}")
    print(connection_reply) # reply OK if everything is fine
    # Retrieve updated CONFIGURATION from the device
    configuration_xml = connection.get_config(source="running",filter=yang_filter)

# XMLDOM object to prettify the XML output later
xmldom = xml.dom.minidom.parseString(configuration_xml.xml)

# JSON data of the XML converted via XMLTODICT library
json_response = xmltodict.parse(configuration_xml.xml)

# Print NETCONF XML and JSON data received in a pretty format
print(f"{15 * '-'}|UPDATED CONFIG IN XML FORMAT|{15 * '-'}")
print(xmldom.toprettyxml(indent="  "))
print(f"{15 * '-'}|UPDATED CONFIG IN JSON FORMAT|{15 * '-'}")
print(json.dumps(json_response,indent=2))

# print Again table data about the interfaces
print(f"{15 * '-'}|PRINT TABLE WITH INTERFACE DETAIL (post change)|{15 * '-'}")
for interface in json_response["rpc-reply"]["data"]["interfaces"]["interface"]:
    name = interface['name']
    description = interface.get('description')
    state = interface['enabled']
    if interface['ipv4'].get('address'):
        address = interface['ipv4']['address']['ip']
        mask = interface['ipv4']['address']['netmask']
    else:
        address = mask = "No"
    print(f"name:{name:20} state:{state:10} IP:{address+'/'+mask:30} description:{description}")

