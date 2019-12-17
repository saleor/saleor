#!/bin/sh

# Push static to AWS S3

docker run --rm \
    -e SECRET_KEY=dummy \
    -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    -e AWS_LOCATION=${AWS_LOCATION} \
    -e AWS_MEDIA_BUCKET_NAME=${AWS_MEDIA_BUCKET_NAME} \
    -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    -e AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME} \
    -e STATIC_URL=${STATIC_URL} \
    ${IMAGE_NAME} \
    python3 manage.py collectstatic --no-input
