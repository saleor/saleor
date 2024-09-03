#!/bin/bash

echo Started at `date`
echo This script will update the generated code
echo

currdir=`pwd`
cmdlist="generateobjectsfromxsd.sh generatecontrollersfromtemplate.sh"
for cmd in $cmdlist ; do 
    echo Executing Script "$cmd"
    if [ ! -f $currdir/script/$cmd ];then
        echo "Script $currdir/script/$cmd not found"
        exit 1
    fi
    $currdir/script/$cmd
    ERRORCODE=$?
    if [ $ERRORCODE -ne 0 ];then
        echo "########################################################################"
        echo "Encountered error during execution of $cmd"
        echo "See logs or output above."
        echo "Exiting, Update ***NOT*** complete."
        exit $ERRORCODE
    fi
done
echo Exiting, Update completed successfully.
echo Compile, run tests and commit to git-hub.
echo Completed at `date`

