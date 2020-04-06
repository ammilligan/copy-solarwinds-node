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

def update_poller(swis:object, pollerUri:str, pollerType:str) -> None:

    try:
        # Change the poller for the URI
        pollerProperties = {
            "uri":pollerUri,
            "PollerType":pollerType
        }
        response = swis.update(
            **pollerProperties
        )
    except Exception as e:
        raise Exception(" ".join(["Error updating poller with Uri", pollerUri, "to type",pollerType,". Details:", str(e.args)]))
        
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Create HTTP apps in bulk on a Solarwinds node")
    parser.add_argument("-S", "--server", metavar="SW_SERVER", action="store", type=str, dest="swisInfo", default="localhost", help="IP or FQDN of Solarwinds server")
    parser.add_argument("-w", "--wait", metavar="WAIT_TIME", action="store", type=int, dest="waitTime", default=0, required=False, help="Seconds to wait between creating each node and setting custom properties")
    args = parser.parse_args()

    # Sanity test for the command line
    try:
        try:
            validate_ip(args.swisInfo)
        except:
            validate_fqdn(args.swisInfo)

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
    uris=[
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=586329",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=586266",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=586206",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=578997",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=578844",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=578575",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=578209",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=577517",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=577476",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=576844",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=576189",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=576069",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=573736",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=571779",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=571738",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=570883",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=569770",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=567299",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=566817",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=562845",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=562559",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=562540",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=561908",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=560971",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=560894",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=559236",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=559221",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=559206",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=558930",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=558880",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=558830",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=556914",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=555072",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=548179",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=548072",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=546164",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=542493",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=542224",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=531247",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=527348",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=527298",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=525789",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=525739",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=524210",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=524088",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=523972",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=522629",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=514059",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=512195",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=503653",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=503611",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=503579",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=503567",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=502474",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=502378",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=502308",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=502258",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=502188",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=497744",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=496306",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=496256",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=494900",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=494850",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=493326",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=493276",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=493091",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=493059",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=493027",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=492985",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=492971",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=492935",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=492028",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=491536",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=491168",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=486412",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=486362",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=486312",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=486066",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=485966",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=485916",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=485512",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=485462",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=485412",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=485362",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=485200",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=484241",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=484191",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=484106",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=483703",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=480998",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=480944",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=480454",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=480410",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=479546",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=479496",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=479446",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=478789",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=478334",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=471956",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=471428",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=471372",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=471322",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=471016",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470969",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470919",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470869",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470819",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470769",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470719",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470669",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470619",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470569",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470519",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470469",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470419",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470369",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470319",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470269",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470219",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470063",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=470013",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469963",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469947",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469897",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469847",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469687",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469637",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469587",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469537",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469434",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469378",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469328",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469278",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469228",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469128",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469078",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=469028",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468978",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468745",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468692",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468592",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468542",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468492",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468442",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468392",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468342",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468242",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468136",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468086",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=468036",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=467896",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=467846",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=467596",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=467546",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=467492",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=467234",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=466559",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=466387",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=466204",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=466192",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=465021",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463779",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463729",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463679",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463621",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463571",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463521",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463471",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463421",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463371",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463321",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463271",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463221",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463171",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463121",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=463071",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=462937",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=459535",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=459485",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=459435",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=459385",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=459332",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=459229",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=459179",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=459035",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=458935",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=458835",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=458785",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=458735",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=458437",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=458387",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=458287",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=458118",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=458068",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=457915",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=457865",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=457715",
		"swis://SOLARWINDS.ci.northwestern.edu/Orion/Orion.Pollers/PollerID=457665"
    ]

    # Copy applications from source node to target nodes
    for uri in set(uris):
        try:
            print(uri)
            update_poller(swis=swis,pollerUri=uri,pollerType="N.Memory.SNMP.HrStorage")
            print(" ".join(["Updated poller with Uri",uri,"succeeded"]))
        except Exception as e:
            print(" ".join(["Update poller with Uri", uri, "failed. Details:", str(e.args)]))

