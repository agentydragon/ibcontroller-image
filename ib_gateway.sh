#!/bin/bash
set -e

sed -i "s/^IbLoginId=.*/IbLoginId=${IB_LOGIN_ID}/" ~/IBController/IBController.ini
sed -i "s/^IbPassword=.*/IbPassword=${IB_PASSWORD}/" ~/IBController/IBController.ini
sed -i "s/^ReadOnlyLogin=.*/ReadOnlyLogin=yes/" ~/IBController/IBController.ini

IBC_PATH=~/IBController
IBC_INI=~/IBController/IBController.ini
TWS_MAJOR_VRSN=972
TWS_PATH=~/Jts
TWS_CONFIG_PATH="${TWS_PATH}"

export DISPLAY=:1
"${IBC_PATH}/Scripts/IBController.sh" "${TWS_MAJOR_VRSN}" \
     "--tws-path=${TWS_PATH}" "--tws-settings-path=${TWS_CONFIG_PATH}" \
     "--ibc-path=${IBC_PATH}" "--ibc-ini=${IBC_INI}" \
     >>/var/log/ibcontroller.log 2>&1
