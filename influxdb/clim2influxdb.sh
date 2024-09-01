#!/bin/bash

cd $(dirname $0)

set -e

if [ -z "$VIRTUAL_ENV" ]
then
	source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
	workon panasonic || true
fi

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

# create the file ~/.panasonic-oauth-token with no goup+other read access
umask 077

echo "Using args: $ARGS"
./clim2influxdb.py $ARGS > data.txt

# echo "$res"
curl -XPOST --silent --show-error "$INFLUXDB_SERVER/write?db=$INFLUXDB_DATABASE" \
		--user "$INFLUXDB_USER:$INFLUXDB_PASSWORD" \
		--data-binary \
		@data.txt
