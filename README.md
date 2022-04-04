# Flume Water Polyglot V3 Node Server

## Installation

Here is how you install this poly.

## Requirements

Fill out all parameters in the Configuration page.  See [Configuration Page](configdoc.md) for more information.

## Monitoring

You should monitor:
- The Controller Status to confirm the nodeserver is running
- The Controller Authorization Status to confirm authorization
  - This will go to Failed when authorization issues are detected, and should go back to Authorized when issue is resolved.
- The Node Status
  - This will go False when any communication issues happen, like internet is down, PyFlume servers not responding, ...

If you have any questions about these please discuss on the [FlumeWater Subforum](https://forum.universal-devices.com/forum/278-flumewater/) or the Github issue ["Invalid Token" Data stopped being sent to ISY](https://github.com/UniversalDevicesInc-PG3/udi-poly-FlumeWater/issues/6)

## Nodes

### Controller

#### Drivers

- ST: Status: 
  - Connected
  - Disconnected
  - Failed 
- GV1: Authorization Status: 
  - Not Started: Connection has not been started
  - Started: The connection process has been started
  - Authorized: The Authorization is good
  - Failed: The Authorization Failed

#### Commands

- Query
  - Query all values of the controller
- Discover 
  - Run discover to find Hub and Sensors
- Force Authorization Fail
  - Simulates and Authorization Failure to test any monitoring programs
  - Will re-authorize on next poll
  
### Hub

#### Drivers

- ST - Status:
  - True
  - False

### Sensors

#### Drivers

- ST - Node Status
  - True
  - False: Set when any connection error occurs while polling
- GV1 - Current Interval Flow
- GV2 - Usage last 60 minutes
- GV3 - Usage last 24 hours
- GV4 - Usage today
- GV5 - Usage last 30 days
- GV6 - Usage week to date
- GV7 - Usage month to date

## Revision History
- 3.0.10: 04/04/2022
  - Add missing load of re so checking for invalid_token doesn't croak
  - Force latest udi_interface
- 3.0.9: 03/16/2022
  - Fix bug in trapping authorization error from previous release.
- 3.0.8: 02/26/2022
  - Try to trap connection and authorization problems, see documentation above.
    - ["Invalid Token" Data stopped being sent to ISY](https://github.com/UniversalDevicesInc-PG3/udi-poly-FlumeWater/issues/6)
- 3.0.7: 02/15/2022
  - Allow Query on Flume Sensor
- 3.0.6: 02/15/2022
  - Fix log message to report values after querying Flume
  - Fix controller to not poll all nodes
- 3.0.5: 02/04/2022
  - Add traceback when there is an error from pyflume to help debug issues
- 3.0.4: 01/10/2022
  - Fix setting initial params
- 3.0.3: 12/26/2021
  - Added conn_status to Controller so ST is properly set
    - Existing users will need to delete the controller node in the Polyglot UI and restart the NS
- 3.0.2: 11/05/2021
  - Works with udi_interface 3.0.22
- 3.0.1: 11/03/2021
  - Log levels all working with new methods
- 3.0.0: 08/21/2021
  - First Polyglot V3 release
- 2.0.7: 03/10/2021
  - Add --upgrade to pip3 install
- 2.0.6:
  - Improve error trapping and show error message
- 2.0.5:
  - Trap failure to authorize and print the error
  - Added Authorization Status with driver
    - Users on PGC need to delete and re-add nodeserver to see it properly
- 2.0.4
  - Minor profile fix for UD Mobile App.
- 2.0.3
  - Proper error trapping for defining scan_interval
- 2.0.2
  - Many fixes for PGC
- 2.0.1
  - Fixed precision on values
- 2.0.0
  - Initial Version
