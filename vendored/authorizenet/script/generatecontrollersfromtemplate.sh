#!/bin/bash

# Script to generate controllers from the generated bindings file, and uses template

currdir=`pwd`

dt=`date '+%m/%d/%Y %H:%M:%S'`
echo Starting ${dt}

CDIR=`pwd`
SRCDIR=${CDIR}
GENFOLDER=authorizenet/apicontractsv1.py
CONTROLLERFOLDER=controllerstemporary

SRCLOG=${CDIR}/log/TestSources
CNTLOG=${CDIR}/log/TestControllers

if [ ! -e "${CDIR}/log" ]; then
	echo "Creating ${CDIR}/log"
	mkdir ${CDIR}/log
else
	echo "Deleting existing ${CDIR}/log/*"
	rm -rf ${CDIR}/log/*.* > /dev/null
fi

echo Identifying Requests\/Responses to process from "${SRCDIR}/${GENFOLDER}"
grep -i -e "request *=" -e "response *=" ${SRCDIR}/${GENFOLDER} | grep -v _AVS | cut -d= -f1 | egrep -v  "^ |\." | sort -u > ${SRCLOG}0.log

echo Getting Unique Request\/Responses
grep -i -e "request *$" -e "response *$" ${SRCLOG}0.log > ${SRCLOG}1.log

echo Identifying Object names
perl -pi -w -e 's/Request *$|Response *$//g;'  ${SRCLOG}1.log
sort -u ${SRCLOG}1.log > ${SRCLOG}2.log

# Create backup for later comparison
cp ${SRCLOG}2.log ${SRCLOG}3.log

echo Creating Final List of Request\/Response to generate code
sort -u ${SRCLOG}2.log   > ${SRCLOG}.log

# make sure the temporary folder exists
if [ ! -e "${CONTROLLERFOLDER}" ]; then
    mkdir ${CONTROLLERFOLDER}
fi
rm -rf ${CONTROLLERFOLDER}/*Controller.py

echo Creating Controllers
for cntrls in `cat ${SRCLOG}.log`  
do
    echo Generating Code for ${cntrls}Controller.py
    cp ${SRCDIR}/script/ControllerTemplate.pyt ${SRCDIR}/${CONTROLLERFOLDER}/${cntrls}Controller.py
    perl -pi -w -e "s/APICONTROLLERNAME/$cntrls/g;" ${SRCDIR}/${CONTROLLERFOLDER}/${cntrls}Controller.py
done

cat ${SRCDIR}/script/headertemplate.pyt ${SRCDIR}/${CONTROLLERFOLDER}/*.py  > ${SRCDIR}/authorizenet/apicontrollers.new

sed -i 's/getTransactionListForCustomerResponse/getTransactionListResponse/g' ${SRCDIR}/authorizenet/apicontrollers.new

echo Controllers generated in module: ${SRCDIR}/authorizenet/apicontrollers.py

echo Finished ${dt}

