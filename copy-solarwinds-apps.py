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

def copy_apps(swis:object, sourceNodeIP:str, targetNodeName:str) -> None:
    try:
        response = swis.query("".join(["SELECT NodeID from Orion.Nodes where IPAddress ='",sourceNodeIP,"'"]))
        sourceNodeID = response["results"][0]["NodeID"]
    except Exception as e:
        raise Exception(" ".join(["Error getting node ID for source Node", sourceNodeIP, ". Details:", str(e.args)]))

    try:
        response = swis.query("".join(["SELECT NodeID from Orion.Nodes where Caption ='",targetNodeName,"'"]))
        targetNodeID = response["results"][0]["NodeID"]
    except Exception as e:
        raise Exception(" ".join(["Error getting node ID for target node", targetNodeName, ". Details:", str(e.args)]))

    try:
        response = swis.query("".join(["SELECT Uri, ApplicationID, ApplicationTemplateID from Orion.APM.Application where NodeID ='",str(sourceNodeID),"'"]))
        applications = response["results"]
    except Exception as e:
        raise Exception(" ".join(["Error getting applications for source Node", sourceNodeIP, ". Details:", str(e.args)]))

    try:
        # Create app monitor with inherited credentials. Explicit credentials will copy later.
        for app in applications:
            templateID = (app["ApplicationTemplateID"])
            appParams = [
                targetNodeID,
                templateID,
                -4, # Inherit credentials from the application template
                False
            ]
            newAppID = swis.invoke(
                'Orion.APM.Application',
                'CreateApplication',
                *appParams
            )
            print("Created new app on Node ID",targetNodeID,"with application ID",newAppID)

            # Get any overrides on the components of the app being copied
            # and set them on the components of the new app
            # Setting it up as a separate query string because it's easier to read
            query = "".join([
                """SELECT Source.ComponentID as [Source]
                , Target.ComponentID as [Target]
                , Source.TemplateID
                , CS.Key, CS.Value, CS.ValueType, CS.Required
                FROM Orion.APM.Component Source
                INNER JOIN Orion.APM.ComponentSetting CS on Source.ComponentID=CS.ComponentID
                INNER JOIN Orion.APM.Component Target on Source.TemplateID=Target.TemplateID
                where Source.ApplicationID = '""",
                str(app["ApplicationID"]),
                "' and Target.ApplicationID = '",
                str(newAppID),
                "'"
            ])
            response = swis.query(query)
            componentSettings = response["results"]

            for setting in componentSettings:
                print("    ComponentID=",setting["Target"],"Key=",setting["Key"],"Value=",setting["Value"],"Type=",setting["ValueType"], "Required=",setting["Required"])
                properties = {
                    "ComponentID":setting["Target"],
                    "Key":setting["Key"],
                    "Required":setting["Required"],
                    "Value":setting["Value"],
                    "ValueType":setting["ValueType"]
                }
                newSettingID = swis.create(
                    "Orion.APM.ComponentSetting",
                    **properties
                )
                print(newSettingID)
    except Exception as e:
        raise Exception(" ".join(["Error creating applications on target node", targetNodeName, ". Details:", str(e.args)]))
        
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
        swis = SwisClient("solarwinds.ci.northwestern.edu", username, password)
        response = swis.query("SELECT Top 1 NodeID from Orion.Nodes")
    except Exception as e:
        print("Unable to connect to SWIS server")
        quit()
        
    # Copy applications from source node to target nodes
    for target in args.targets:
        try:
            copy_apps(swis=swis, sourceNodeIP=args.sourceNodeIP, targetNodeName=target)
            print(" ".join(["Copy application monitors from",args.sourceNodeIP,"to",target,"succeeded"]))
        except Exception as e:
            print(" ".join(["Copy application monitors", target, "from", args.sourceNodeIP,"failed. Details:", str(e.args)]))

