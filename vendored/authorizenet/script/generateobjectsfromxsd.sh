#!/bin/bash

# Script to generate the python contract from XSD
# Requires pyxb module to be installed and available in path

dt=`date '+%m/%d/%Y %H:%M:%S'`

AnetURL=https://apitest.authorize.net/xml/v1/schema/AnetApiSchema.xsd
AnetURLPERL='https:\/\/apitest.authorize.net\/xml\/v1\/schema\/AnetApiSchema.xsd'
LOCALXSDWITHANY=./script/AnetOut.xsd
CONTRACTSDIR=authorizenet
CONTRACTSFILE=apicontractsv1
PYXBGENPATH=`which pyxbgen`
TEMPFILE=binding
TEMPDIRECTORY=./script/temp

echo Starting pyxbgen on ${dt}
which python > /dev/null
if [ $? -eq 0 ]
then
    echo Found python
else
    echo Unable to find python. Make sure python is installed.
    exit 1
fi

which pyxbgen > /tmp/pyxbgenpath.txt
if [ $? -eq 0 ]
then
    echo Found pyxbgen
else
    echo Unable to find pyxbgen. Make sure pyxb package is installed.
    exit 1
fi

which perl > /dev/null
if [ $? -eq 0 ]
then
    echo Found perl
else
    echo Unable to find perl. Make sure perl is installed.
    exit 1
fi

# which wget > /dev/null
# if [ $? -eq 0 ]
# then
    # echo Found wget. Downloading AnetAPISchema file under Script directory.
	# wget -O ./script/AnetApiSchema.xsd ${AnetURL}
	# if [ $? -eq 0 ]
	# then
		# echo AnetAPISchema.xsd downloaded.
	# else
		# echo Unable to download AnetAPISchema.
		# exit 1
	# fi
# else
	# echo Wget not found. Looking for Curl
	# which curl > /dev/null
	# if [ $? -eq 0 ]
	# then
		# echo Found curl. Downloading AnetAPISchema file under Script directory.
		# curl --noproxy '*' ${AnetURL} > ./script/AnetApiSchema.xsd
		# if [ $? -eq 0 ]
		# then
			# echo AnetAPISchema.xsd downloaded.
		# else		
			# curl ${AnetURL} > ./script/AnetApiSchema.xsd
			# if [ $? -eq 0 ]
			# then
				# echo AnetAPISchema.xsd downloaded.
			# else
				# echo Unable to download AnetAPISchema.
				# exit 1
			# fi
		# fi
	# else
		# echo Unable to find wget and curl. Make sure either one is installed
		# exit 1
	# fi
# fi

echo Modifying XSD using perl to support backward compatibility
echo Creating temporary directory 
mkdir -p "$TEMPDIRECTORY"

# Added since UpdateCustomerProfile API was updated for SOAP APIs, thus requiring changes to the contract object UpdateCustomerProfileRequest. 
# Doesn't remove the type declaration for customerProfileInfoExType, but prevents it from being used anywhere else in the contract
perl -pi.back -e 's/type=\"anet:customerProfileInfoExType\"/type=\"anet:customerProfileExType\"/g;' script/AnetApiSchema.xsd 

perl script/addany.pl script/AnetApiSchema.xsd ${TEMPDIRECTORY}/IntermediateAnetOut.xsd ${LOCALXSDWITHANY}
if [ $? -eq 0 ]
then
	: #echo AnetOut.xsd generated #Uncomment for debugging
else
    echo Unable to generate AnetOut.xsd
    exit 1
fi

echo Deleting temporary directory 
rm -rf "$TEMPDIRECTORY"

echo Using pyxb from "${PYXBGENPATH}"
if [ -e "${TEMPFILE}.py" ]; then
    rm ${TEMPFILE}.py
fi

python "${PYXBGENPATH}" -u ${LOCALXSDWITHANY} -m ${TEMPFILE}
if [ $? -eq 0 ]
then
    if [ -e "${CONTRACTSDIR}/${CONTRACTSFILE}.old" ]
    then
        rm "${CONTRACTSDIR}/${CONTRACTSFILE}.old"
    fi
    if [ -e "${CONTRACTSDIR}/${CONTRACTSFILE}.py" ]
    then
        rm "${CONTRACTSDIR}/${CONTRACTSFILE}.py"
    fi
    mv "${TEMPFILE}.py" "${CONTRACTSDIR}/${CONTRACTSFILE}.py"
   echo Bindings have been successfully generated from XSD in the file "${CONTRACTSDIR}/${CONTRACTSFILE}.py"
    echo Old contracts have been moved to .old
else
    echo Error generating bindings from XSD. Review the errors and rerun the script.
    exit 1
fi

perl -i -pe "s/.Location\(\'.*xsd\'/.Location\(\'$AnetURLPERL\'/g" ${CONTRACTSDIR}/${CONTRACTSFILE}.py

exit 0
