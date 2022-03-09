# Assisted Installer - How to guide

> [!WARNING]
> The upstream Assisted Installer is not supported officially by Red Hat, the supported AI is the one provided with RHACM. Use this information at your own risk, the upstream AI may contain new features/changes that may not be reflected in this guide.


# Assisted Installer deployment

First of all it is necessary to deploy the upstream Assisted Installer in your environment, choose your deployment option based on your preferences and deploy the AI following these [instructions](https://github.com/openshift/assisted-service/tree/4b4f0f45d897430037039a9282225bf6bd02acfe#deployment).


# Assisted Installer API calls

### Clusters

#### Get OpenShift clusters

```
$ curl -s http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/|jq '.[].name'
```

#### Delete OpenShift clusters

```
$ curl -s -X 'DELETE' http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID} -H 'accept: application/json'
```

### InfraEnvs

#### Get InfraEnvs

```
$ curl -s http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/infra-envs/|jq '.[].name'
```

#### Get InfraEnvs Hosts

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/infra-envs/${YOUR_INFRAENV}/hosts -H 'accept: application/json'|jq '.[].requested_hostname, .[].role, .[].status'
```

#### Delete InfraEnvs Hosts

```
$ curl -s -X DELETE http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/infra-envs/${YOUR_INFRAENV} -H 'accept: application/json'
```

#### Get image from InfraEnv

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/infra-envs/${YOUR_INFRAENV}/downloads/image-url|jq
```

#### Patch InfraEnv

```
$ curl -X 'PATCH' http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/infra-envs/${YOUR_INFRAENV} \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "ignition_config_override": "{\"ignition\": {\"version\": \"3.1.0\"}, \"storage\": {\"files\": [{\"filesystem\": \"root\",\"overwrite\": true,\"path\": \"/etc/pki/ca-trust/source/anchors/openshift-config-user-ca-bundle.crt\", \"contents\": {\"source\": \"data:text/plain;base64,<YOUR_CERT_BASE64_ENCODED>\"},\"mode\": 420}]}}"
}'
```

### Ignition Config

#### Get discovery ignition config

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/infra-envs/${YOUR_INFRAENV}/downloads/files?file_name=discovery.ign -H 'accept:application/octet-stream'
```

#### Get bootstrap ignition config

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/downloads/files?file_name=bootstrap.ign -H 'accept: application/octet-stream'|jq
```

#### Get master ignition config

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/downloads/files?file_name=master.ign -H 'accept: application/octet-stream'|jq
```

#### Get worker ignition config

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/downloads/files?file_name=worker.ign -H 'accept: application/octet-stream'|jq
```

### Install config


#### Get Install config

```
$ curl -s http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/install-config|jq
```


#### Update Install config

```
$ curl -s -X PATCH http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/install-config \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '"{\"baseDomain\": \"newdomain.com\"}"'
```

### Kubeconfig

#### Get the Kubeconfig

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/downloads/credentials?file_name=kubeconfig-noingress -H 'accept: application/octet-stream'
```

### Manifests


#### Get manifests

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/manifests -H 'accept: application/json'|jq '.'
```


#### Get manifest content

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/manifests/files?folder=openshift\&file_name=50-masters-chrony-configuration.yaml -H 'accept: application/octet-stream'
```


#### Upload a new manifest

```
$ curl -s -X POST http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/manifests \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{"folder": "openshift","file_name":"99-disable-operatorhub.yaml","content":"YXBpVmVyc2lvbjogY29uZmlnLm9wZW5zaGlmdC5pby92MQpraW5kOiBPcGVyYXRvckh1YgptZXRhZGF0YToKICBuYW1lOiBjbHVzdGVyCnNwZWM6CiAgZGlzYWJsZUFsbERlZmF1bHRTb3VyY2VzOiB0cnVlCg=="}'
```


### OpenShift versions


#### Get OpenShift versions

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/openshift-versions|jq
```


#### Get components versions

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/component-versions|jq
```

### Operators


#### Supported operators

```
$ curl -s -X GET  http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/supported-operators|jq
```
