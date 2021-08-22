# Flume Water Polyglot V3 Node Server

## Installation

Here is how you install this poly.

## Requirements

Fill out all parameters in the Configuration page.  See [Configuration Page](POLYGLOT_CONFIG.md) for more information.

## Drivers

GV1 - Current Interval Flow
GV2 - Usage last 60 minutes
GV3 - Usage last 24 hours
GV4 - Usage today
GV5 - Usage last 30 days
GV6 - Usage week to date
GV7 - Usage month to date

## Revision History

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
