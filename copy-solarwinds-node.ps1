# ----------------------------------------------------------------------------
# copy-solarwinds-node.ps1
#
# 
# Copies the properties of a specified Solarwinds node, including its type (SNMP, ICMP, external)
# and all of its custom properties, to create a new Solarwinds node or nodes.
#
# The script assigns the new node to the additional poller with the lightest load.
#
# Message syntax
# --------------
#
# copy-solarwinds-node.ps1 -server localhost -sourceNodeIP 129.105.237.17 -targetNodeName geophysics.earth.northwestern.edu
# copy-solarwinds-node.ps1 -server localhost -sourceNodeIP 129.105.237.17 -targetNodeName geophysics.earth.northwestern.edu,test.earth.northwestern.edu
#
# Command line parameters:
#    -sourceNodeIP (Required): The IP address of the Solarwinds monitored node
#     that you want to copy.
#
#    -targetNodeName (Required): Comma-delimited list of the the FQDN(s) of the node(s) you want to create.
#
#    -server (Required): The name or IP address of the Solarwinds server.
#
# Modifications
# -------------
# 20190731 MM Added code to copy status and response poller configuration from source node to new node


# Command line parameters
Param (
    [Parameter()]
    [string] $server="localhost",

    [Parameter(Mandatory=$True)]
    [string] $sourceNodeIP,

    [Parameter(Mandatory=$True)]
    [array] $targetNodeName
)

# Load the SwisSnapin if not already loaded
if (!(Get-PSSnapin | where {$_.Name -eq "SwisSnapin"})) {
    Add-PSSnapin "SwisSnapin"
}

function get-node-uri () {
    Param (
        [Parameter(Mandatory=$True)]
        [string] $IP
    )

    $swisQuery = "SELECT URI from Orion.Nodes where IPAddress = \@p"
    $sourceNode = @{}

    try {
        $sourceNode = Get-SwisData $SWIS $swisQuery @{p=$IP} -ErrorAction Stop
    } catch {
        throw [System.Exception] "Could not query Solarwinds for nodes matching IP $IP. Error details: ", $_.Exception.Message
    }

    return $sourceNode
}

function copy-node () {
    Param (
        [Parameter(Mandatory=$True)]
        [string] $sourceNodeIP,

        [Parameter(Mandatory=$True)]
        [string] $targetNodeName
    )

    try {

        # Get the IP address for the target node's FQDN
        try {
            $targetNodeIP = get-IP -targetNodeName $targetNodeName
        } catch {
            throw [System.Exception] "Error getting IP address for $targetNodeName. Error details: ", $_.Exception.Message 
        }

        # Get the URI of the source node
        try {
            $sourceNodeURI = get-source-node-uri -sourceNodeIP $sourceNodeIP
        } catch {
            throw [System.Exception] "Error getting URI for $sourceNodeIP. Error details: ", $_.Exception.Message 
        }

        # Get properties from the node being copied
        $sourceNodeProps = Get-SwisObject $SWIS -Uri $sourceNodeURI

        # Define which properties will be copied from the source to the target for Nodes, Interfaces, and Volumes
        $nodePropsToCopy = @("MachineType", "ObjectSubType", "SNMPVersion", "Community") 

        # Make an in-memory copy of the node being copied
        $targetNodeProps = @{}
        $nodePropsToCopy | foreach  {
            $targetNodeProps[$_] = $sourceNodeProps[$_] 
        }
   
        # Set the properties for the new node
        $targetNodeProps["Caption"]=$targetNodeName
        $targetNodeProps["DNS"]=$targetNodeName
        $targetNodeProps["IP"]=$targetNodeIP
        $targetNodeProps["EngineID"] = get-least-used-poller

        #$targetNodeProps.Keys | foreach {
        #    Write-Host "Target node property $_ = $($targetNodeProps.Item($_))"
        #}

        # Create the node on the target system
        $targetNodeURI = New-SwisObject $SWIS -EntityType "Orion.Nodes" -Properties $targetNodeProps
        $targetNode = Get-SwisObject $SWIS -Uri $targetNodeURI

        Write-Host "Created node with NodeID $($targetNode["NodeID"])"

        # Get custom properties from the node being copied
        $sourceNodeCustomProps = Get-SwisObject $SWIS "$sourceNodeURI/CustomProperties"

        # Copy all of the custom properties from the node being copied to the new node
        # We need to exclude the properties in $nodePropsNoCopy - they are not needed OR will break 
        # the node create process
        $nodePropsNoCopy = @("NodeID", "DisplayName", "InstanceSiteId", "Uri", "InstanceType", "Description")
        $targetNodeCustomProps = @{}
        $sourceNodeCustomProps.Keys | foreach  {
            if ($nodePropsNoCopy -notcontains $_) {
                $targetNodeCustomProps[$_] = $sourceNodeCustomProps[$_] 
               Write-Host "Setting custom property $_"
            } else {
                Write-Host "Skipping custom property $_"
            }
        }

        #Write-Host "Custom Properties copied from source node minus exceptions"
        #$targetNodeCustomProps.Keys | foreach {
        #    Write-Host "Custom Property $_ = $($targetNodeCustomProps.Item($_))"
        #}

        # Set the custom properties on the new node
        Set-SwisObject $SWIS -Uri "$targetNodeURI/CustomProperties/" -Properties $targetNodeCustomProps

        # Get poller assignments from the node being copied
        $swisQuery = "SELECT PollerType, Enabled from Orion.Pollers where NetObjectID = \@p"
        try {
            $sourceNodePollers = Get-SwisData $SWIS $swisQuery @{p=$sourceNodeProps["NodeID"]} -ErrorAction Stop
        } catch {
            throw [System.Exception] "Could not get poller assignments for Solarwinds nodeID $($sourceNodeProps["NodeID"]). Error details: ", $_.Exception.Message
        }
        
        # Assign pollers to the new node
        foreach ($poller in $sourceNodePollers)  {
            $targetNodePoller = @{}
            $targetNodePoller["PollerType"] = $poller.PollerType
            $targetNodePoller["NetObject"] = "N:"+ $targetNode["NodeID"]
            $targetNodePoller["NetObjectType"] = "N"
            $targetNodePoller["NetObjectID"] = $targetNode["NodeID"]
            $targetNodePoller["Enabled"] = $poller.Enabled

            try {
                New-SwisObject -SwisConnection $SWIS -EntityType "Orion.Pollers" -Properties $targetNodePoller
            } catch {
                throw [System.Exception] "Could not assign poller$($poller.PollerType) to Solarwinds nodeID $($targetNode["NodeID"]). Error details: ", $_.Exception.Message
            }
        }

    } catch {
        Write-Host "Could not create node $targetNodeName Error details: ", $_.Exception.Message
    }

    return $targetNodeURI

}

function get-ip {
    Param (
        [Parameter(Mandatory=$True)]
        [string] $targetNodeName
    )

    # Check DNS for the new node. Resolve-DnsName throws an error if not found.
    try {
        $targetNodeDNS = Resolve-DnsName $targetNodeName

        # If multiple IPs in DNS, generally the one we want will be the second record
        if ($targetNodeDNS.IPAddress.Count -eq 1) {
            $targetNodeIP = $targetNodeDNS.IPAddress
        } else {
            $targetNodeIP = $targetNodeDNS.IPAddress[1]
        }
    } catch {
        throw [System.Exception] "Cannot resolve $targetNodeName. Error details: ", $_.Exception.Message
    }
    
    return $targetNodeIP
}

function get-source-node-uri {
    Param (
        [Parameter(Mandatory=$True)]
        [string] $sourceNodeIP
    )

    $sourceNodeURI = ""

    # Get the URI of the node being copied
    try {
        $sourceNodeURI = get-node-uri -IP $sourceNodeIP
    } catch {
        throw [System.Exception] "Error getting URI for source node $IP. Error details: ", $_.Exception.Message
        exit 1
    }

    # If there are no Solarwinds nodes matching the source IP address, quit
    if ($sourceNodeURI -eq $null) {
        throw [System.Exception] "Source node $sourceNodeIP not found"
        exit 1
    }

    # If there are multiple Solarwinds nodes matching the source IP address, quit
    if ($sourceNodeURI.Count -gt 1) {
        throw [System.Exception] "Multiple nodes match source node $sourceNodeIP"
        exit 1
    }

    return $sourceNodeURI
}

# get-least-used-poller
# Get the ID of the Additional poller with the lightest load
function get-least-used-poller {
    $swisQuery = "SELECT top 1 EngineID FROM Orion.Engines where ServerType='Additional' and DisplayName not like 'NUQ%' and DisplayName not like 'swpoller04%' order by Elements ASC"
    $EngineID = ""

    try {
        $EngineID = Get-SwisData $SWIS $swisQuery -ErrorAction Stop
    } catch {
        throw [System.Exception] "Could not query Solarwinds for nodes matching IP $IP. Error details: ", $_.Exception.Message
    }

    return $EngineID
}

# Connect to the target system

if ($server -eq $null) {$server='localhost'}
$credential = Get-Credential
$SWIS= Connect-Swis -Credential $credential -Hostname $server

# For each target node FQDN, copy the source node's properties to a new node
$targetNodeName | foreach {
    try {
        Write-Host "Copying $sourceNodeIP to $_"
        $targetNodeURI = copy-node -sourceNodeIP $sourceNodeIP -targetNodeName $_
    } catch {
        Write-Host "Unable to copy $sourceNodeIP to $_ . Error details: ", $_.Exception.Message
    }
}

exit 0;
