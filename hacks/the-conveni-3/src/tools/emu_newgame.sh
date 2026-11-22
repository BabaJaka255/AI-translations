#!/bin/sh
# From a fresh boot (emu.sh start <iso>) to the running map of Campaign scenario 1 with LAWSON, defaults
# everywhere, owner slot 1. Uses holds because short taps are sometimes dropped. Screens are saved in $1.
E=$(dirname "$0")/emu.sh
O=${1:-/tmp/c3/ng}
mkdir -p "$O"
p() { sh $E hold "$1" "${2:-0.25}"; sleep "${3:-1.5}"; }
sleep 35
p Return 0.2 2; p Return 0.2 2; p Return 0.2 2      # logos, intro
p Return 0.2 8                                      # title -> owner select
sh $E shot "$O/01_owner.png"
p l 0.2 3                                           # owner 1 -> main menu
sh $E shot "$O/02_menu.png"
p l 0.2 3                                           # campaign
p l 0.2 3                                           # scenario 1
p l 0.2 5                                           # LAWSON
p l 0.2 3                                           # scenario card -> site choice
p Left 1.5 1.5                                      # walk to a free lot
sh $E shot "$O/03_site.png"
p l 0.2 2                                           # site
p l 0.2 2                                           # store size
sh $E shot "$O/04_lic.png"
p Down; p Down; p Down; p Down; p Left; p l 0.2 3   # licenses: OK
p j 0.2 2; p l 0.2 3                                # interior: menu -> Done Editing
p Up; p Up; p Up; p l 0.2 2; p l 0.2 3; p l 0.2 2   # manager slot -> Hire -> first applicant
p Down; p Down; p Down; p Down; p Left; p l 0.2 3   # staff: OK
sh $E shot "$O/05_pay.png"
p Left; p l 0.2 3; p Left; p l 0.2 3; p Left; p l 0.2 4   # pay, hours, prices
sh $E shot "$O/06_map.png"
