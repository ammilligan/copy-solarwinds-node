import requests
import socket
import argparse
import ipaddress
import re
import getpass
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

def create_apps(swis:object, targetNodeName:str, hostname:str) -> None:

    try:
        response = swis.query("".join(["SELECT NodeID from Orion.Nodes where Caption ='",targetNodeName,"'"]))
        targetNodeID = response["results"][0]["NodeID"]
    except Exception as e:
        raise Exception(" ".join(["Error getting node ID for target node", targetNodeName, ". Details:", str(e.args)]))

    try:
        response = swis.query("SELECT ApplicationTemplateID FROM Orion.APM.ApplicationTemplate where Name = 'HTTP'")
        applicationTemplateID = response["results"][0]["ApplicationTemplateID"]
    except Exception as e:
        raise Exception(" ".join(["Error getting application template ID for HTTP Monitor. Details:", str(e.args)]))

    try:
        # Create app monitor with inherited credentials. Explicit credentials will copy later.
        appParams = [
            targetNodeID,
            applicationTemplateID,
            -4, # Inherit credentials from the application template
            False
        ]
        
        newAppID = swis.invoke(
            'Orion.APM.Application',
            'CreateApplication',
            *appParams
        )
        print("Created new app on Node ID",targetNodeID,"with application ID",newAppID)

        # Get the URI of the new app monitor
        query = "".join([
            """SELECT Uri
            FROM Orion.APM.Application
            where ApplicationID = '""",
            str(newAppID),
            "'"
        ])
        response = swis.query(query)
        appUri = response["results"][0]["Uri"]
        #print("Uri of Application ID",newAppID,"on Node ID",targetNodeID,"is",appUri)
        
        # Change the name of the new app from the default
        appProperties = {
            "uri":appUri,
            "Name":hostname
        }
        updatedAppID = swis.update(
                    **appProperties
        )
        print("    Updated name of app monitor",appUri,". Output",updatedAppID)

        # Get components of the new app
        query = "".join([
            """SELECT ComponentID
            FROM Orion.APM.Component
            where ApplicationID = '""",
            str(newAppID),
            "'"
        ])
        response = swis.query(query)
        component = response["results"][0]["ComponentID"]

        #print("    URL=","".join(["http://",hostname]))
        properties = {
            "ComponentID":component,
            "Key":"Url",
            "Required":1,
            "Value":"".join(["http://",hostname]),
            "ValueType":0
        }
        newSettingID = swis.create(
            "Orion.APM.ComponentSetting",
            **properties
        )
        print(newSettingID)

    except Exception as e:
        raise Exception(" ".join(["Error creating HTTP app on target node", targetNodeName, ". Details:", str(e.args)]))
        
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Create HTTP apps in bulk on a Solarwinds node")
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
        swis = SwisClient("solarwinds.ci.northwestern.edu", username, password)
        response = swis.query("SELECT Top 1 NodeID from Orion.Nodes")
    except Exception as e:
        print("Unable to connect to SWIS server")
        quit()
    
    # List of hosts for URLs
    hostnames=[
        "aids-dev.fsm.northwestern.edu",
        "bioethics-dev.fsm.northwestern.edu",
        "cancer-dev.fsm.northwestern.edu",
        "careersresearch-dev.fsm.northwestern.edu",
        "cgm-dev.fsm.northwestern.edu",
        "cme-dev.fsm.northwestern.edu",
        "brain-dev.fsm.northwestern.edu",
        "deptcommon-dev.fsm.northwestern.edu",
        "familymedicine-dev.fsm.northwestern.edu",
        "fcvri-dev.fsm.northwestern.edu",
        "feinberg-dev.fsm.northwestern.edu",
        "labs-dev.fsm.northwestern.edu",
        "api-dev.fsm.northwestern.edu",
        "foodallergy-dev.fsm.northwestern.edu",
        "galaxy-dev.fsm.northwestern.edu",
        "globalhealth-dev.fsm.northwestern.edu",
        "lupus-dev.fsm.northwestern.edu",
        "mcgaw-dev.fsm.northwestern.edu",
        "medicine-dev.fsm.northwestern.edu",
        "mss-dev.fsm.northwestern.edu",
        "ncco-dev.fsm.northwestern.edu",
        "neurology-dev.fsm.northwestern.edu",
        "nucats-dev.fsm.northwestern.edu",
        "nupedha-dev.fsm.northwestern.edu",
        "nupoc-dev.fsm.northwestern.edu",
        "nwmedicine-dev.fsm.northwestern.edu",
        "ortho-teaching-dev.fsm.northwestern.edu",
        "orthopaedic-dev.fsm.northwestern.edu",
        "oto-dev.fsm.northwestern.edu",
        "parkinsons-dev.fsm.northwestern.edu",
        "pathology-dev.fsm.northwestern.edu",
        "pediatrics-dev.fsm.northwestern.edu",
        "pharm-dev.fsm.northwestern.edu",
        "physio-dev.fsm.northwestern.edu",
        "prevmed-dev.fsm.northwestern.edu",
        "psychiatry-dev.fsm.northwestern.edu",
        "pph-dev.fsm.northwestern.edu",
        "radiology-dev.fsm.northwestern.edu",
        "scleroderma-dev.fsm.northwestern.edu",
        "scor-dev.fsm.northwestern.edu",
        "secure-dev.fsm.northwestern.edu",
        "skinresearch-dev.fsm.northwestern.edu"
        # "surgery-dev.fsm.northwestern.edu"
    ]

    # Copy applications from source node to target nodes
    for target in args.targets:
        try:
            for hostname in set(hostnames):
                print(hostname)
                create_apps(swis=swis, targetNodeName=target, hostname=hostname)
                print(" ".join(["Create application monitor on",target,"succeeded"]))
        except Exception as e:
            print(" ".join(["Create application monitor on", target, "failed. Details:", str(e.args)]))

