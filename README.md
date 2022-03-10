# Assisted Installer - How to guide

> :warning:
> The upstream Assisted Installer is not supported officially by Red Hat, the supported AI is the one provided with RHACM. Use this information at your own risk, the upstream AI may contain new features/changes that may not be reflected in this guide.


## Assisted Installer deployment

First of all it is necessary to deploy the upstream Assisted Installer in your environment, choose your deployment option based on your preferences and deploy the AI following these [instructions](https://github.com/openshift/assisted-service/tree/4b4f0f45d897430037039a9282225bf6bd02acfe#deployment).

## Assisted Installer wrapper script

> :warning:
> This tool is not supported by Red Hat, this has been prepared for testing, standarization and automation purposes within internal labs.

> Note: This tool allows to deploy either a SNO or a multi-node compact OpenShift cluster (3 masters + 0 workers) based on your preferences, all the settings must be previously provided in the paramfile.yaml file.

This is the tree that represents the file distribution within the repo.

```
tree
.
├── README.md
├── ocpinstaller.py
└── resources
    ├── configs
    │   ├── install-config-patch-3masters
    │   ├── install-config-patch-sno
    │   ├── paramfile-3masters.yaml
    │   └── paramfile-sno.yaml
    └── manifests
        ├── 99-disable-operatorhub.yaml
        ├── 99-disconnected-internal-icsp.yaml
        ├── 99-image-policy-0.yaml
        ├── 99-image-policy-1.yaml
        ├── 99-image-policy-2.yaml
        ├── 99-openshift-master-chrony.yaml
        ├── 99-openshift-worker-chrony.yaml
        ├── 99-redhat-operator-index-catalog.yaml
        └── 99-redhat-operators-catalog.yaml
```

### Pre-requisites

This tool has been designed to run on the same host where the Assisted Installer is deployed.

First of all it is necessary to create a `paramfile.yaml` file based on your preferences, settings will vary between a SNO and a multi-node cluster, you can make a copy from either `paramfile-3masters.yaml` or `paramfile-sno.yaml` files to your own `paramfile.yaml` and customize it afterwards based on your own preferences. Check the next section *paramfile settings* for further references on the settings included.

Once the `paramfile.yaml` file is ready, create your own `install-config-patch` file, you can create a copy from one of the `install-config-patch-*` files available in the repo.

Be aware of some of the paremeters in the paramfile.yaml like the *pull_secret*, *ignition_config_override*, or *static_network_config*, those parameters has something in common, those needs to either escape " characters using a backward slash character \" or separate lines with /n. Those are mandatory conditions in these parameters and must be properly set otherwise the Assisted Installer API call will fail returning an error.

The manifests folder includes some of the custom manifests we may need to include in the OpenShift cluster at installation time, set any of these manifests accordingly (internal registry names are required) and place new manifests if you consider it necessary.

### Paramfile settings

There are 3 different sections:
1. *ocp_infra_configs*: Settings for the underlying infrastructure, like: number of masters, bmc ips, bmc users and passwords, etc.
2. *cluster_configs*: OpenShift cluster object settings, like the networking parameters, platform type, architecture, pull_secrets, etc.
3. *infraenv_configs*: OpenShift InfraEnv object settings, like the nodes static network config (NMState), ssh_key, OpenShift version, etc.


|Parameter type        |Parameter                |Description                                                                                       |
|----------------------|-------------------------|--------------------------------------------------------------------------------------------------|
| ocp_infra_configs    | num_masters             | Number of masters to deploy                                                                      |
|                      | bmc_ip                  | Console Ips                                                                                      |
|                      | bmc_user                | Console user                                                                                     |
|                      | bmc_password            | Console password                                                                                 |
|                      | bmc_system_path         | Console system_path, required to set boot options                                                |
|                      | bmc_insertmedia_path    | Console insermedia_path, required to insert new virtual media device (iso)                       |
|                      | bmc_ejectmedia_path     | Console ejectmedia_path, required to eject existing virtual media                                |
|                      | bmc_resetsystem_path    | Console resetsystem_path, required to power off, on, reset the server                            |
|                      | http_path               | HTTP path to store the RHCOS images required to deploy the OpenShift nodes                       |
| cluster_configs      | name                    | Name of the cluster                                                                              |
|                      | kind                    | Type of object, in this case a Cluster                                                           |
|                      | high_availability_mode  | Full for multi-node cluster, None for SNO                                                        |
|                      | openshift_version       | OpenShift version to deploy, i,e: 4.9                                                            |
|                      | ocp_release_image       | OpenShift release image to pull from a internal registry                                         |
|                      | base_dns_domain         | DNS domain for your cluster                                                                      |
|                      | cluster_networks        | Cluster networks, IP range used for pods                                                         |
|                      | service_networks        | Service networks, IP range for internal and user services                                        |
|                      | machine_networks        | Machine network, IP range for OpenShift nodes, Ingress VIP, API VIP                              |
|                      | pull_secret             | Your pull secret to pull images from registries                                                  |
|                      | ssh_public_key          | Your ssh public key to be added in the RHCOS authorized_keys                                     |
|                      | vip_dhcp_allocation     | Set to true if this a DHCP managed environment, false for static IP settings                     |
|                      | user_managed_networking | Indicates if the network is managed by the user                                                  |
|                      | platform                | Indicates the type of platform, set baremetal for multi-node                                     |
|                      | ingress_vip             | Sets the ingress vip IP, required only for multi-node clusters                                   |
|                      | api_vip                 | Sets the API vip IP, required only for multi-node clusters                                       |
|                      | additional_ntp_source   | Sets and additional NTP source                                                                   |
|                      | hyperthreading          | Enable/Disable hiperthreading                                                                    |
|                      | network_type            | Sets the SDN CNI plugin, choose between OVNKubernetes and OpenShiftSDN                           |
|                      | schedulable_masters     | Set to true since in both SNO and multi-node compact cluster there are no workers                |
|                      | cpu_architecture        | CPU architecture, i.e: x86_64                                                                    |
| infraenv_configs     | kind                    | Type of object, in this case a InfraEnv                                                          |
|                      | name                    | Name of the InfraEnv object                                                                      |
|                      | additional_ntp_sources  | Sets and additional NTP source                                                                   |
|                      | ssh_authorized_key      | Your ssh public key to be added in the RHCOS authorized_keys                                     |
|                      | pull_secret             | Your pull secret to pull images from registries                                                  |
|                      | ignition_config_override| Custom ignition config like the internal registry cert o the registries config for discovery host|
|                      | static_network_config   | Static network config for nodes, be aware of the format and "\n" required to separate lines      |
|                      | image_type              | Full-iso to set a full iso image for booting nodes                                               |
|                      | openshift_version       | OpenShift version to deploy, i,e: 4.9                                                            |
|                      | cpu_architecture        | CPU architecture, i.e: x86_64                                                                    |
|                      | cluster_id              | Cluster ID reference from the Cluster object created before the InfraEnv object                  |

### How to run the OCP Installer wrapper script

Once both the paramfile.yaml and the install-config-patch files are in place and containing the required settings, just run the following command and wait for some time until the cluster is deployed.

```
./ocpinstaller.py -f resources/configs/paramfile.yaml
```

## Assisted Installer API calls

In this section you will find some of the Assisted Installer API calls available to interact with the AI.

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

#### Get the install config

```
$ curl -s http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/install-config|jq
```

#### Update the install config

```
$ curl -s -X PATCH http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/install-config \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '"{\"baseDomain\": \"newdomain.com\"}"'
```

### Kubeconfig

#### Get the kubeconfig

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/downloads/credentials?file_name=kubeconfig-noingress -H 'accept: application/octet-stream'
```

### Manifests

#### Get the manifests

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/manifests -H 'accept: application/json'|jq '.'
```


#### Get manifest content & upload new manifest

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/manifests/files?folder=openshift\&file_name=50-masters-chrony-configuration.yaml -H 'accept: application/octet-stream'
```

```
$ curl -s -X POST http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/clusters/${YOUR_CLUSTER_ID}/manifests \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{"folder": "openshift","file_name":"99-disable-operatorhub.yaml","content":"YXBpVmVyc2lvbjogY29uZmlnLm9wZW5zaGlmdC5pby92MQpraW5kOiBPcGVyYXRvckh1YgptZXRhZGF0YToKICBuYW1lOiBjbHVzdGVyCnNwZWM6CiAgZGlzYWJsZUFsbERlZmF1bHRTb3VyY2VzOiB0cnVlCg=="}'
```

### OpenShift versions

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/openshift-versions|jq
```

#### Get the components versions

```
$ curl -s -X GET http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/component-versions|jq
```

### Operators

#### Get the supported operators

```
$ curl -s -X GET  http://${YOUR_AI_ADDRESS}:8090/api/assisted-install/v2/supported-operators|jq
```
