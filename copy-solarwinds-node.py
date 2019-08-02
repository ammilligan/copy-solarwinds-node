import requests
import socket
from orionsdk import SwisClient

def getIP(hostname:str)->str:
    retval = socket.gethostbyname(hostname)
    return retval

def main():
    # Solarwinds connection details
    swServer = 'solarwinds.ci.northwestern.edu'
    username = 'solarwinds\\'
    password = ''

    # Source and target node details
    sourceNodeIP   = ''
    targetNodeName = ''

    # Allow swis to ignore certificate warnings
    verify = False
    if not verify:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Resolve DNS for the new host
    targetNodeIP = getIP(targetNodeName)
   
    # Create the SWIS client
    swis = SwisClient(swServer, username, password)
    
    # Get source node URI
    # Python understands that this is a dict delivered as JSON
    response = swis.query("".join(["SELECT Uri FROM Orion.Nodes WHERE IPAddress='",sourceNodeIP,"'"]))
    sourceNodeURI = response["results"][0]["Uri"]

    # Get source node properties
    # Python understands that this is a dict delivered as JSON
    sourceNode = swis.read(sourceNodeURI)

    # Define which custom properties will be copied from the source to the target
    nodePropsToCopy = ("MachineType", "ObjectSubType", "SNMPVersion", "Community") 

    # Find the polling engine with the smallest current load
    response = swis.query("SELECT top 1 EngineID FROM Orion.Engines where ServerType='Additional' and DisplayName not like 'NUQ%' and DisplayName not like 'swpoller04%' order by Elements ASC")
    engineID = response["results"][0]["EngineID"]

    # set up property bag for the new node
    targetNodeProps = {}
    targetNodeProps["Caption"]=targetNodeName
    targetNodeProps["DNS"]=targetNodeName
    targetNodeProps["IP"]=targetNodeIP
    targetNodeProps["EngineID"]= engineID
    for prop in nodePropsToCopy:
        targetNodeProps[prop] = sourceNode[prop]

    # Create a new node
    targetNodeURI = swis.create('Orion.Nodes', **targetNodeProps)

    # Get the new node so we can refer to its properties
    targetNode = swis.read(targetNodeURI)

    # Get the set of pollers assigned the source node
    response = swis.query("".join(["SELECT PollerType, Enabled from Orion.Pollers where NetObjectID ='",str(sourceNode["NodeID"]),"'"]))
    sourceNodePollers = response["results"]

    targetNodePollers = []
    for poller in sourceNodePollers:
        targetNodePollers.append(
            {
                'PollerType': poller["PollerType"],
                'NetObject': "".join(["N:",str(targetNode["NodeID"]) ]),
                'NetObjectType': "N",
                'NetObjectID': targetNode["NodeID"],
                'Enabled': poller["Enabled"]
            }
        )

    for poller in targetNodePollers:
        response = swis.create('Orion.Pollers', **poller)


if __name__ == '__main__':
    main()
