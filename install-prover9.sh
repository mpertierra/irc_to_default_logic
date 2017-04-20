#!/usr/bin/env bash

cd /tmp
curl -O http://www.cs.unm.edu/~mccune/prover9/download/LADR-2009-11A.tar.gz
tar xzf /tmp/LADR-2009-11A.tar.gz
rm /tmp/LADR-2009-11A.tar.gz
cd /tmp/LADR-2009-11A
make all
mkdir /usr/local/bin/prover9
mv /tmp/LADR-2009-11A/bin/* /usr/local/bin/prover9/
cd ..
rm -rf /tmp/LADR-2009-11A
