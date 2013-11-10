#!/bin/bash

REPOSITORY=./repo
PLUGINS=$(echo plugin.video.*)

echo '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' > ./addons.xml
echo "<addons>" >> ./addons.xml
cat ./repository.finnish-tv/addon.xml | grep -v "<?xml" >> ./addons.xml
echo "Release generator.."

for i in $PLUGINS
do
	#echo "check if version of plugin $i exists on repo"
	#VERSION=$(xpath -q -e "/addon/attribute::version" $i/addon.xml | awk -F\" '{ print $2 }')
	VERSION=$(perl -n -e'/^[ ]+version="(.*?)"/ && print $1' $i/addon.xml)
	REPOFILE=$REPOSITORY/$i/$i-$VERSION.zip
	if [ -f $REPOFILE ]
	then
		echo " skip: $i-$VERSION"
	else
		echo " new release: $i-$VERSION"
		zip -r $REPOFILE $i -x@.gitignore > /dev/null
	fi
	cat $i/addon.xml | grep -v "<?xml" >> ./addons.xml
done
echo "</addons>" >> ./addons.xml
md5sum addons.xml > addons.xml.md5

