#!/bin/bash

set -e

cd $(dirname $0)

source conf

LAST_DAY="last_day.txt"
if  [ ! -f $LAST_DAY ]
then
    echo "No $LAST_DAY file. Creating one."
    date +%Y/%m/%d > $LAST_DAY
    exit
fi

DAY=$(cat $LAST_DAY)
echo "Last day is: $DAY"

case $(basename $0) in
    clim2influxdb.sh)
        ARGS="--current"
        ;;

    clim2influxdb_day.sh)
        ARGS="--day $DAY"
        ;;

    clim2influxdb_month.sh)
        ARGS="--month $DAY"
        ;;
esac

echo "Using args: $ARGS"
./clim2influxdb.py $ARGS > data.txt

# echo "$res"
curl -XPOST --silent 'https://zotac.apdu.fr:8086/write?db=db_clim' \
		--user $USER:$PASSWORD \
		--data-binary \
		@data.txt

# update last day with today
date +%Y/%m/%d > $LAST_DAY
