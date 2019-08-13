import requests
import re
import getpass
from orionsdk import SwisClient

if __name__ == '__main__':
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
        

    sourceNodeName = "swlinuxdev"
    targetNodeName = "swlinuxdev"

    response = swis.query("".join(["SELECT NodeID from Orion.Nodes where Caption ='",sourceNodeName,"'"]))
    sourceNodeID = response["results"][0]["NodeID"]

    response = swis.query("".join(["SELECT NodeID from Orion.Nodes where Caption ='",targetNodeName,"'"]))
    targetNodeID = response["results"][0]["NodeID"]

    response = swis.query("".join(["SELECT Uri, ApplicationID, ApplicationTemplateID from Orion.APM.Application where NodeID ='",str(sourceNodeID),"'"]))
    applications = response["results"]

    # for app in applications:
    #     print("Get Components for application ID ",app["ApplicationID"])
    #     response = swis.query("".join(["SELECT Uri, ApplicationID, ComponentID, ComponentName, TemplateID from Orion.APM.Component where ApplicationID ='",str(app["ApplicationID"]),"'"]))
    #     components = response["results"]
    #     for component in components:
    #         print("  Component ID=",component["ComponentID"],"Name=",component["ComponentName"], "Component TemplateID=", component["TemplateID"])
    #         response = swis.query("".join(["SELECT Uri, ComponentID, Key, Value, ValueType, Required from Orion.APM.ComponentSetting where ComponentID ='",str(component["ComponentID"]),"'"]))
    #         settings = response["results"]
    #         for setting in settings:
    #             print("    Key=",setting["Key"],"Value=",setting["Value"],"Type=",setting["ValueType"], "Required=",setting["Required"])
        

    # You can set the credential explicitly later
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
