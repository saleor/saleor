# Saleor Core Kustomize Deployment

### Create Manifest
#### make:
```bash
# build yaml manifest
make build
```
#### commands:
```bash
# build yaml manifest
kustomize build .
```

### Deploy Manifest
#### make:
```bash
# preview
make dry-apply
# deploy
make apply
```
#### commands:
```bash
# preview
kustomize build . | kubectl apply -f - --dry-run=client
# deploy
kustomize build . | kubectl apply -f -
```

### Create SuperUser
#### make:
```bash
make superuser
```
#### commands:
```bash
# wait for migrations to complete and web interface to be responsive
# get pod
kubectl get pods -n saleor
# find pod name for saleor-api pod
kubectl exec -i -t $SALEOR_API_POD_NAME -c saleor-api -n saleor -- python manage.py createsuperuser
```

### Delete Resources
#### make:
```bash
# preview
make dry-delete
# delete
make delete
```
#### commands:
```bash
# preview
kustomize build . | kubectl delete -f - --dry-run=client
# delete
kustomize build . | kubectl delete -f -
```
