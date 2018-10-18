# Saleor

Saleor is a high-performance e-commerce solution created with Python and Django. 
The app strives towards a service-based architecture means productive developers, 
trying to keep it simple, lightweight, and modular.
Built with top-notch technologies. Django, PostgreSQL, ElasticSearch, GraphQL and Docker.

## Introduction

This chart deploys and instance of the saleor opensource project demo storefront 
along with the technology stack onto a [Kubernetes](http://kubernetes.io) cluster
using the [Helm](https://helm.sh) package manager. 

## Chart components

`Optional app component` => Saleor can function without this component

`Optional helm component` => The helm deployment can exclude the deployment of
this component and instead use an external url for that component by setting
`useExternalUrl: true` and setting the required secrets for the component in
`secrets.yaml`.

| Component         | Optional app component  | Optional helm component  |
|------------------ |------------------------ |------------------------- |
| Saleor            | :x:                     |  :x:                     |
| Elasticsearch     | :heavy_check_mark:      | :heavy_check_mark:       |
| Redis             | :x:                     | :heavy_check_mark:       |
| Postgresql        | :x:                     | :heavy_check_mark:       |

## Chart Architecture

The current architecture of the charts is designed around deployment of the demo 
storefront. Some changes are probably required on forks of saleor to accommodate
tailored storefronts.

Primary Chart (saleor):

```text
./templates/
├── celery-deployment.yaml
├── celery-hpa.yaml
├── custom-settings.yaml
├── db-migrate-job.yaml
├── db-populate-demo-job.yaml
├── django-deployment.yaml
├── django-hpa.yaml
├── env.yaml
├── ingress.yaml
├── pvc.yaml
├── secrets.yaml
└── service.yaml
```

| Template                        | Description                                |
| ------------------------------- | ------------------------------------------ |
| `celery-deployment.yaml`        | Deploys pod replica(s) for the celery worker(s). Handles task queues for emails, image thumbnails, etc |
| `celery-hpa.yaml`               | Horizontal Pod Autoscaling resource for autoscaling for the celery worker pods |
| `django-deployment.yaml`        | Deploys pod replica(s) for the core django application. |
| `django-hpa.yaml`               | Horizontal Pod Autoscaling resource for autoscaling for the django pods |
| `service.yaml`                  | A service resource for the django application |
| `ingress.yaml`                  | Defines how to handle incoming traffic to the service |
| `pvc.yaml`                      | A persitent volume claim resource for storing /app/media content, ie. images, etc |
| `custom-settings.yaml`          | Some additions/amendments to the settings.py file to allow for custom helm template enhancements |
| `env.yaml`                      | A list of non-sensitive environment variables |
| `secrets.yaml`                  | A list of sensitive environment variables |
| `db-migrate-job.yaml`           | Performs the database migrations for saleor |
| `db-populate-demo-job.yaml`     | Performs the database population for the demo storefront |

Secondary charts (subcharts):

```text
./charts/
├── elasticsearch-1.11.1.tgz
├── postgresql-1.0.0.tgz
└── redis-4.2.1.tgz
```

See `helm/charts/stable` for more information about the subcharts

## Saleor external services

Saleor takes advantage of a number of external services to enhance functionality
and externalize development efforts for some parts of the application. If integration
with these components is necessary, read further documentation. Changes to `secrets.yaml`
and/or `values.yaml` with the details of your external provider account may be required.

| Service           | Description             | Essential service               |
|------------------ |------------------------ |-------------------------------- |
| Email Provider    | External email providers, eg mailgun, mailjet, sendgrid, amazon ses, etc, see [docs](https://github.com/mirumee/saleor/blob/master/docs/guides/email_integration.rst)         |   :heavy_check_mark:       |
| Google Recaptcha  | Spam mitigation, see [docs](https://github.com/mirumee/saleor/blob/master/docs/guides/recaptcha.rst)         | ?       |
| Vat Layer API     | Maintaining correct EU vat rates See [docs](https://github.com/mirumee/saleor/blob/master/docs/guides/taxes.rst)    |  :heavy_check_mark:       |
| Open Exchanges API| Maintainance of up-to-date currency exchange rates See open exchanges api [website](https://openexchangerates.org/) | ?       |
| Transifex         | A localization helper service, see [docs](https://github.com/mirumee/saleor/blob/master/docs/architecture/i18n.rst) | :x:       |
| Sentry            | An externalized error monitoring tool, see [docs](https://github.com/mirumee/saleor/blob/master/docs/integrations/sentry.rst) | :x:       |
| Google for retail | Tools for generating product feed which can be used with Google Merchant Center, see [docs](https://github.com/mirumee/saleor/blob/master/docs/integrations/googleforretail.rst) | :x:       |
| Google Analytics  | Google analytics integration, see [docs](https://github.com/mirumee/saleor/blob/master/docs/integrations/googleanalytics.rst) | :x:       |
| Schema.org Markup | Schema.org markup for emails, see [docs](https://github.com/mirumee/saleor/blob/master/docs/integrations/emailmarkup.rst) and read [more here](https://developers.google.com/gmail/markup/overview) | ?       |
| SMO               | Saleor uses opengraph for optimizing social media engagement, see [docs](https://github.com/mirumee/saleor/blob/master/docs/integrations/smo.rst) | :heavy_check_mark:       |
| SEO               | Saleor handles aspects of search engine optimization, see [docs](https://github.com/mirumee/saleor/blob/master/docs/integrations/seo.rst) | :heavy_check_mark:       |

## Prerequisites

- A fully setup kubernetes cluster
- Tiller and helm installed on the cluster
- Correctly configured `values.yaml` specific to ones site 

## Installation

```bash
git clone https://github.com/mirumee/saleor.git && \
cd saleor/deployment/helm && \
helm dependency build && \
helm install --name saleor --namespace dev ./
```

### Uninstalling the saleor stack

To uninstall/delete the `saleor` deployment:

```console
helm delete --purge saleor
```

### Configuration

#### Saleor

Configurable values for the saleor deployment:

| Parameter                       | Description                                | Default                                                    |
| ------------------------------- | ------------------------------------------ | ---------------------------------------------------------- |
| `image.repository`              | The image repository | `mirumee/saleor` |
| `image.tag`                     | The exact version of the image to be pulled | `afce249100f2b90e96bc9b50a8a7b28c710378a0` |
| `image.pullPolicy`              | The image pull policy | `IfNotPresent` |
| `image.pullSecret`              | The secret for gaining access to the image repository if it is private | `nil` |
| `existingSecret`                | The name of the secrets resource for saleor secrets, if set will override the defaul secrets resource | `nil` |
| `service.type`                  | The type of service to be used, preferable to use ClusterIP alongside an ingress resource | `clusterIP` |
| `service.port`                  | The port of service to be used | `80` |
| `ingress.enabled`               | Whether to enabled the ingress resource, recommended to enable and configure this | `false` |
| `ingress.annotations`           | Annotations can customize the ingress controller and are often desireable | `{}` |
| `ingress.path`                  | Path to the saleor store front | `/` |
| `ingress.hosts`                 | A list of host domains for the saleor application. Should be changed to the domain name of your saleor instance | `[]` |
| `ingress.tls`                   | tls settings for saleor instance. Essential for any production instance | `[]` |
| `ingress.tls.secretName`        | tls secret name | `[]` |
| `ingress.tls.hosts`             | tls enabled hosts | `[]` |
| `livenessProbeSettings.initialDelaySeconds` | initial delay before applying liveness probes | `90` |
| `livenessProbeSettings.periodSeconds` | liveness probe period | `90` |
| `livenessProbeSettings.failureThreshold` | liveness probe failures allowed before actually failing | `5` |
| `livenessProbeSettings.successThreshold` | liveness probe successes before actually succeeding | `1` |
| `livenessProbeSettings.timeoutSeconds` | liveness probe timeout duration | `1` |
| `readinessProbeSettings.initialDelaySeconds` | initial delay before applying readiness probes | `30` |
| `readinessProbeSettings.periodSeconds` | readiness probe period | `5` |
| `readinessProbeSettings.failureThreshold` | readiness probe failures allowed before actually failing | `5` |
| `readinessProbeSettings.successThreshold` | readiness probe successes before actually succeeding | `1` |
| `readinessProbeSettings.timeoutSeconds` | readiness probe timeout duration | `1` |

#### Postgresql

Refer directly to the helm/charts/stable/postgresql [README.md](https://github.com/helm/charts/tree/master/stable/postgresql)

There are two custom variables for `.Values.postgresql` which are specific to the saleor context as below:

| Parameter                       | Description                                | Default                                                    |
| ------------------------------- | ------------------------------------------ | ---------------------------------------------------------- |
| `postgresql.enabled` | Whether to deploy the postgresql chart or not | `true`
| `postgresql.useExternalUrl` | Whether to use an external postgresql database for saleor. If set to `true` one should also set `postgresql.enabled` to `false` and also add the postgresql secrets to `secrets.yaml` | `false`

#### Redis

Refer directly to the helm/charts/stable/redis [README.md](https://github.com/helm/charts/tree/master/stable/redis)

There are two custom variables for `.Values.redis` which are specific to the saleor context as below:

| Parameter                       | Description                                | Default                                                    |
| ------------------------------- | ------------------------------------------ | ---------------------------------------------------------- |
| `redis.enabled` | Whether to deploy the redis chart or not | `true`
| `redis.useExternalUrl` | Whether to use an external redis database for saleor. If set to `true` one should also set `redis.enabled` to `false` and also add the redis secrets to `secrets.yaml` | `false`

#### Elasticsearch

Refer directly to the helm/charts/stable/elasticsearch [README.md](https://github.com/helm/charts/tree/master/stable/elasticsearch)

| Parameter                       | Description                                | Default                                                    |
| ------------------------------- | ------------------------------------------ | ---------------------------------------------------------- |
| `elasticsearch.enabled` | Whether to deploy the redis chart or not | `true`
| `elasticsearch.useExternalUrl` | Whether to use an external elasticsearch database for saleor. If set to `true` one should also set `elasticsearch.enabled` to `false` and also add the elasticsearch secrets to `secrets.yaml` | `false`

### Upgrade

To update the saleor deployment

```console
git clone https://github.com/mirumee/saleor.git && \
cd saleor/deployment/helm && \
helm dependency build && \
helm upgrade --reuse-values saleor deployments/helm ./
```
