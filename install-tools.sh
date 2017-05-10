#!/usr/bin/env bash


# Clean install
# cd scripts
# rm -rf lib
# mkdir lib
# cd lib
# touch __init__.py

# Install smatch
# git clone https://github.com/snowblink14/smatch.git
# touch smatch/__init__.py

# cd ../..

# Clean install
rm -rf tools
mkdir tools
cd tools

# Install Java C&C Parser
# mkdir java-candc
# cd java-candc
# wget https://www.cl.cam.ac.uk/~sc609/java-candc/java-candc-v0.95.tgz
# tar xzf java-candc-v0.95.tgz
# rm java-candc-v0.95.tgz
# ./compile
# cd ..

# Install GraphParser
# git clone git@github.com:sivareddyg/graph-parser.git
# cd graph-parser
# ./install.py ungrounded
# cd ..

# Install CAMR Parser
git clone https://github.com/c-amr/camr.git
cd camr
./scripts/config.sh
wget http://www.cs.brandeis.edu/~cwang24/files/amr-anno-1.0.train.m.tar.gz
tar xzf amr-anno-1.0.train.m.tar.gz
rm amr-anno-1.0.train.m.tar.gz
mv amr-anno-1.0/amr-anno-1.0.train.basic-abt-brown-verb.m ./
rm -rf amr-anno-1.0
cd ..

# Install Cornell AMR tool
git clone https://github.com/cornell-lic/amr.git
mv amr cornell-amr
cd cornell-amr
./getres.sh
ant dist
wget https://bitbucket.org/yoavartzi/amr-resources/downloads/amr.sp
