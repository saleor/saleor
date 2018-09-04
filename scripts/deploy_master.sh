#!/bin/bash

VERSION=$CIRCLE_SHA1
ZIP=$VERSION.zip

cd deployment/elasticbeanstalk
zip -r /tmp/$ZIP .

aws s3 cp /tmp/$ZIP s3://$VERSIONS_BUCKET/$ZIP

aws elasticbeanstalk create-application-version --application-name saleor-demo \
   --version-label $VERSION --source-bundle S3Bucket=$VERSIONS_BUCKET,S3Key=$ZIP

# Update the environment to use the new application version
aws elasticbeanstalk update-environment --environment-name $MASTER_ENV_NAME \
     --version-label $VERSION
