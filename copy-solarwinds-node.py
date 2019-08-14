import requests
import socket
import argparse
import ipaddress
import re
import getpass
import time
from orionsdk import SwisClient

def getIP(hostname:str)->str:
    retval = socket.gethostbyname(hostname)
    return retval

def validate_ip (ip_eval:str) -> None:
    try:
        ipaddress.ip_address(ip_eval)
    except ValueError as e:
        raise Exception(" ".join([ip_eval, "is not a valid IP address. Details:", str(e.args)]))
    except Exception as e:
        raise Exception(" ".join(["Error evaluating", ip_eval, ". Details:", str(e.args)]))

def validate_fqdn (fqdn_eval:str) -> None:
    maxLen = 255
    if len(fqdn_eval) > maxLen:
        raise Exception(" ".join([fqdn_eval, "too long for FQDN. Max length is", str(maxLen)]))

    if fqdn_eval[-1] == ".":
        fqdn_eval = fqdn_eval[:-1] # strip exactly one dot from the right, if present
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    
    for x in fqdn_eval.split("."):
        if allowed.match(x) == None:
            raise Exception(" ".join([fqdn_eval, "is not a valid FQDN. Details:", fqdn_eval, "is not part of a valid FQDN", x]))

def copy_node(swis:object, sourceNodeIP:str, targetNodeName:str, waitTime:int=0) -> None:

    # Resolve DNS for the new host
    try:
        targetNodeIP = getIP(targetNodeName)
    except Exception as e:
        raise Exception(" ".join(["Unable resolve IP for target FQDN", targetNodeName, ". Details:", str(e.args)]))
   
    # Get source node URI
    # Python understands that this is a dict delivered as JSON
    try:
        response = swis.query("".join(["SELECT Uri FROM Orion.Nodes WHERE IPAddress='",sourceNodeIP,"'"]))
        sourceNodeURI = response["results"][0]["Uri"]
    except Exception as e:
        raise Exception(" ".join(["Unable get source node URI from Solarwinds. Details:", str(e.args)]))

    # Get source node properties
    # Python understands that this is a dict delivered as JSON
    try:
        sourceNode = swis.read(sourceNodeURI)
    except Exception as e:
        raise Exception(" ".join(["Unable get properties of source node. Details:", str(e.args)]))

    # Define which custom properties will be copied from the source to the target
    nodePropsToCopy = ("MachineType", "ObjectSubType", "SNMPVersion", "Community") 

    # Find the polling engine with the smallest current load
    try:
        response = swis.query("SELECT top 1 EngineID FROM Orion.Engines where ServerType='Additional' and DisplayName not like 'NUQ%' and DisplayName not like 'swpoller04%' order by Elements ASC")
        engineID = response["results"][0]["EngineID"]
    except Exception as e:
        raise Exception(" ".join(["Unable get polling engine ID from Solarwinds. Details:", str(e.args)]))

    # set up property bag for the new node
    targetNodeProps = {}
    targetNodeProps["Caption"]=targetNodeName
    targetNodeProps["DNS"]=targetNodeName
    targetNodeProps["IP"]=targetNodeIP
    targetNodeProps["EngineID"]= engineID
    for prop in nodePropsToCopy:
        targetNodeProps[prop] = sourceNode[prop]

    # Create a new node
    try:
        targetNodeURI = swis.create('Orion.Nodes', **targetNodeProps)
    except Exception as e:
        raise Exception(" ".join(["SWIS error creating new node", targetNodeName ,". Details:", str(e.args)]))

    print(" ".join(["Created new node",targetNodeName]))

    # Pause to give Solarwinds time to perform any actions on node creation
    if (waitTime > 0):
        print(" ".join(["Wait",str(waitTime),"seconds while Solarwinds executes new node tasks"]))
        time.sleep(waitTime)

    # Get the new node so we can refer to its properties and its NodeID
    try:
        targetNode = swis.read(targetNodeURI)
    except Exception as e:
        raise Exception(" ".join(["SWIS error reading properties of new node", targetNodeName ,". Details:", str(e.args)]))

    print(" ".join(["New node",targetNodeName,"created with Node ID",str(targetNode["NodeID"])]))

    # Get the set of custom properties values from the source node
    # Populate a dict with custom properties from the source node. Some members of this structure should not be copied.
    # Update the custom properties on the new node.
    try:
        sourceNodeCustomProps = swis.read(sourceNodeURI + "/CustomProperties")
    except Exception as e:
        raise Exception(" ".join(["SWIS error reading custom properties from source node",sourceNodeIP,". Details:", str(e.args)]))

    nodePropsNoCopy = ["NodeID", "DisplayName", "InstanceSiteId", "Uri", "InstanceType", "Description"]
    targetNodeCustomProps = {}
    try:
        for prop in sourceNodeCustomProps:
            if prop not in nodePropsNoCopy:
                targetNodeCustomProps[prop]=sourceNodeCustomProps[prop]
        
        swis.update(targetNodeURI + "/CustomProperties", **targetNodeCustomProps)
    except Exception as e:
        print("SWIS error updating custom properties for node %s (nodeID %s). Details: %s", targetNodeName, targetNode["NodeID"], str(e.args))

    # Get the set of pollers assigned the source node
    # Create a list of poller info
    # Create pollers on the new node
    try:
        response = swis.query("".join(["SELECT PollerType, Enabled from Orion.Pollers where NetObjectID ='",str(sourceNode["NodeID"]),"'"]))
        sourceNodePollers = response["results"]
    except Exception as e:
        raise Exception(" ".join(["SWIS error reading pollers from source node",sourceNodeIP,". Details:", str(e.args)]))

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
        try:
            response = swis.create('Orion.Pollers', **poller)
        except Exception as e:
            print("SWIS error creating pollers for node %s (nodeID %s). Details: %s", targetNodeName, targetNode["NodeID"], str(e.args))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Copy a Solarwinds node")
    parser.add_argument("-s", "--sourceNodeIP", metavar="SOURCE_NODE_IP", action="store", type=str, dest="sourceNodeIP", required=True, help="Source node IP in Solarwinds")
    parser.add_argument("-S", "--server", metavar="SW_SERVER", action="store", type=str, dest="swisInfo", default="localhost", help="IP or FQDN of Solarwinds server")
    parser.add_argument("-t", "--targetNodeName", metavar="TARGET_NODE", action="append", type=str, dest="targets", required=True, help="FQDN of new node")
    parser.add_argument("-w", "--wait", metavar="WAIT_TIME", action="store", type=int, dest="waitTime", default=0, required=False, help="Seconds to wait between creating each node and setting custom properties")
    args = parser.parse_args()

    # Sanity test for the command line
    try:
        try:
            validate_ip(args.swisInfo)
        except:
            validate_fqdn(args.swisInfo)

        validate_ip(args.sourceNodeIP)
        for target in args.targets:
            validate_fqdn(target)
    except Exception as e:
        print(" ".join(["Illegal value on command line. Details:", str(e.args)]))
        quit()

    username = input("Username: ")
    password = getpass.getpass("Password: ")
    
    # Allow swis to ignore certificate warnings
    verify = False
    if not verify:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Create the SWIS connection and run a simple test
    try:
        swis = SwisClient(args.swisInfo, username, password)
        response = swis.query("SELECT Top 1 NodeID from Orion.Nodes")
    except Exception as e:
        print(" ".join(["Unable to connect to SWIS server", args.swisInfo, "Details:", str(e.args)]))
        quit()
        
    # Create new nodes
    for target in args.targets:
        try:
            copy_node(swis=swis, sourceNodeIP=args.sourceNodeIP, targetNodeName=target, waitTime=args.waitTime)
            print(" ".join(["Copy node from",args.sourceNodeIP,"to",target,"succeeded"]))
        except Exception as e:
            print(" ".join(["Copy node", target, "from", args.sourceNodeIP,"failed. Details:", str(e.args)]))