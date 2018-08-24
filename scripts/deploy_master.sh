#!/bin/bash

VERSION=$CIRCLE_SHA1
ZIP=$VERSION.zip

zip -r $ZIP Dockerrun.aws.json

aws s3 cp $ZIP s3://$VERSIONS_BUCKET/$ZIP

aws elasticbeanstalk create-application-version --application-name saleor-demo \
    --version-label $VERSION --source-bundle S3Bucket=$VERSIONS_BUCKET,S3Key=$ZIP

# Update the environment to use the new application version
aws elasticbeanstalk update-environment --environment-name $MASTER_ENV_NAME \
      --version-label $VERSION
