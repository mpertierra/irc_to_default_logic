#!/usr/bin/env bash

mkdir -p irc/xml
cd irc/xml
curl http://uscode.house.gov/download/releasepoints/us/pl/114/329not328/xml_usc26@114-329not328.zip -o irc.zip
unzip irc.zip
rm irc.zip
mv usc26.xml irc.xml