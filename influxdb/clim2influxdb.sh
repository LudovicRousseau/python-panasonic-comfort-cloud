#!/bin/bash

set -e

cd $(dirname $0)

source conf

function update_last_day()
{
	LAST_DAY="last_day.txt"
	if  [ ! -f $LAST_DAY ]
	then
		echo "No $LAST_DAY file. Creating one."
		date +%Y/%m/%d > $LAST_DAY
		exit
	fi

	DAY=$(cat $LAST_DAY)
	echo "Last day is: $DAY"

	# update last day with today
	date +%Y/%m/%d > $LAST_DAY
}

case $(basename $0) in
	clim2influxdb.sh)
		ARGS="--current"
		;;

	clim2influxdb_day.sh)
		update_last_day
		ARGS="--day $DAY"
		;;

	clim2influxdb_month.sh)
		update_last_day
		ARGS="--month $DAY"
		;;
esac

echo "Using args: $ARGS"
./clim2influxdb.py $ARGS > data.txt

# echo "$res"
curl -XPOST --silent "$INFLUXDB_SERVER/write?db=$INFLUXDB_DATABASE" \
		--user "$INFLUXDB_USER:$INFLUXDB_PASSWORD" \
		--data-binary \
		@data.txt
