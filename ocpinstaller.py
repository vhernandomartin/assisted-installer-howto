#!/usr/bin/env python3

import os
import getopt
import sys
import yaml
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import urllib
import wget
import socket
import time
import base64
import logging


class cluster:

    def __init__(self,file,params,deployfile,cluster_id='null'):
        self.file = file
        self.params = params
        self.cluster_id = cluster_id
        self.deployfile = deployfile

    def getParams(self):
        global num_masters
        global bmc_ip
        global bmc_user
        global bmc_password
        global bmc_insertmedia_path
        global bmc_ejectmedia_path
        global bmc_resetsystem_path
        global bmc_system_path
        global http_path
        global hostname
        global headers
        global data
        global ip
        global api_vip
        global ingress_vip
        deployfile = self.deployfile
        file = self.file
        cluster_id = self.cluster_id
        params_type = self.params
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        headers = {'Content-Type': 'application/json'}
        data = 'resources/configs/' + str(deployfile)
        clusterid_string = 'cluster_id'
        if clusterid_string in open(file, 'r').read():
            print('INFO: cluster_id parameter already set in the paramfile.yaml, please remove it before running this program')
            exit(1)

        with open(file, 'a') as param_file:
            if cluster_id == 'null':
                print('INFO: Getting parameters for cluster deployment')
            else:
                print('INFO: appending the cluster_id parameter cluster_id: ' + cluster_id + ' to the paramfile.yaml')
                param_file.write('  cluster_id: ' + cluster_id)

        with open(file) as param_file:
            parsed_param_file = yaml.load(param_file, Loader=yaml.FullLoader)
            fileparams = parsed_param_file[params_type]

        if params_type == 'ocp_infra_configs':
            num_masters = fileparams['num_masters']
            bmc_ip = fileparams['bmc_ip']
            bmc_user = fileparams['bmc_user']
            bmc_password = fileparams['bmc_password']
            bmc_insertmedia_path = fileparams['bmc_insertmedia_path']
            bmc_ejectmedia_path = fileparams['bmc_ejectmedia_path']
            bmc_resetsystem_path = fileparams['bmc_resetsystem_path']
            bmc_system_path = fileparams['bmc_system_path']
            http_path = fileparams['http_path']

        if params_type == 'cluster_configs':
            api_vip = fileparams['api_vip']
            ingress_vip = fileparams['ingress_vip']
        return fileparams

    def insertParams(self,fileparams):
        deployfile = self.deployfile
        print('INFO: writting configs into the ' + deployfile + ' file')
        with open('resources/configs/' + str(deployfile), 'w') as cluster_config_file:
            json.dump(fileparams, cluster_config_file)

    def deployCluster(self,clusterconf):
        deployfile = self.deployfile
        api_url = 'http://'+ str(hostname) + ':8090/api/assisted-install/v2/clusters'

        if clusterconf["high_availability_mode"] == 'None':
            print('INFO: Installing a SNO cluster, high_availability_mode set to: ' + clusterconf["high_availability_mode"])
        elif clusterconf["high_availability_mode"] == 'Full':
            print('INFO: Installing a Multi node cluster, high_availability_mode set to: ' + clusterconf["high_availability_mode"])

        with open(data, 'rb') as payload:
            cluster_api_call = requests.post(api_url, data=payload, headers=headers)

        cluster_json_api = json.loads(requests.get(api_url).text)
        cluster_json = cluster_json_api[0]
        cluster_id = cluster_json['id']
        print('INFO: Cluster deployed with cluster_id: ' + cluster_id)
        return cluster_id

    def deployInfraEnv(self):
        deployfile = self.deployfile
        api_url = 'http://'+ str(hostname) + ':8090/api/assisted-install/v2/infra-envs'

        with open(data, 'rb') as payload:
            infraenv_api_call = requests.post(api_url, data=payload, headers=headers)

        infraenv_json_api = json.loads(requests.get(api_url).text)
        infraenv_json = infraenv_json_api[0]
        infraenv_id = infraenv_json['id']
        print('INFO: InfraEnv deployed with infraenv_id: ' + infraenv_id)
        return infraenv_id

    def getIso(self,infraenv_id):
        api_url = 'http://'+ str(hostname) + ':8090/api/assisted-install/v2/infra-envs/' + infraenv_id + '/downloads/image-url'

        get_iso_json_api = json.loads(requests.get(api_url).text)
        get_iso = get_iso_json_api['url']
        iso_name = http_path + '/ocp_ai.iso'
        wget.download(get_iso, iso_name)

    def getClusterStatus(self,cluster_id,status_message):
        get_clusterstatus = 'Not checked yet'
        while get_clusterstatus != status_message:
            print('INFO: The cluster status is: ' + get_clusterstatus + ' , cluster_id: ' + cluster_id)
            print('INFO: Waiting for: ' + status_message)
            time.sleep(30)
            api_url = 'http://'+ str(hostname) + ':8090/api/assisted-install/v2/clusters/' + cluster_id
            get_clusterstatus_json_api = json.loads(requests.get(api_url).text)
            get_clusterstatus = get_clusterstatus_json_api['status_info']

    def getInfraHostsStatus(self,infraenv_id,num_masters):
        api_url = 'http://'+ str(hostname) + ':8090/api/assisted-install/v2/infra-envs/' + infraenv_id + '/hosts'
        while len(json.loads(requests.get(api_url).text)) == 0:
            print('INFO: Waiting for hosts to be registered')
            time.sleep(30)
        if num_masters > 1:
            for master in range(num_masters):
                get_host_status = 'Not checked yet'
                while get_host_status != "Host is ready to be installed":
                    get_host_status_json_api = json.loads(requests.get(api_url).text)
                    get_host_status_json = get_host_status_json_api[master]
                    master_id = get_host_status_json['id']
                    print('INFO: The infraenv host ' + master_id + ' status is: ' + get_host_status)
                    get_host_status = get_host_status_json['status_info']
                    time.sleep(10)
        elif num_masters == 1:
            get_host_status = 'Not checked yet'
            while get_host_status != "Host is ready to be installed":
                get_host_status_json_api = json.loads(requests.get(api_url).text)
                get_host_status_json = get_host_status_json_api[0]
                master_id = get_host_status_json['id']
                print('INFO: The infraenv host ' + master_id + ' status is: ' + get_host_status)
                get_host_status = get_host_status_json['status_info']
                time.sleep(10)
        else:
            print('ERROR: ' + str(num_masters) + ' servers to install, it is not a valid value')
            exit(2)


    def uploadManifests(self,cluster_id):
        api_url = 'http://'+ str(hostname) + ':8090/api/assisted-install/v2/clusters/' + cluster_id + '/manifests'
        headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
        path = 'resources/manifests'
        for manifest in os.listdir(path):
            file = os.path.join(path, manifest)
            if os.path.isfile(file):
                print('INFO: Adding new manifest: ' + file)
                with open(file, 'rb') as manifest_file:
                    data = manifest_file.read()
                    encoded = base64.b64encode(data)
                    encodedtext = encoded.decode('utf-8')
                    split_name = file.split("/",2)
                    manifest_name = split_name[2]
                    data = '{"folder": "openshift","file_name":"' + manifest_name + '","content":"' + encodedtext + '"}'
                    upload_manifest_api_call = requests.post(api_url, data=data, headers=headers)
        get_manifests_json_api = json.loads(requests.get(api_url).text)
        num_manifests = len(get_manifests_json_api)
        print('INFO: These are the manifests will be deployed with OpenShift:\n')
        for deployed_manifest in range(num_manifests):
            get_manifests_json = get_manifests_json_api[deployed_manifest]
            print(get_manifests_json['file_name'])

    def patchClusterConfig(self,cluster_id,api_vip,num_masters):
        if num_masters > 1:
            data = '{ "api_vip": "' + api_vip + '"}'
            api_url = 'http://'+ str(hostname) + ':8090/api/assisted-install/v2/clusters/' + cluster_id
            headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
            requests.patch(api_url, data=data, headers=headers)

    def patchInstallConfig(self,cluster_id):
        data = 'resources/configs/install-config-patch'
        api_url = 'http://'+ str(hostname) + ':8090/api/assisted-install/v2/clusters/' + cluster_id + '/install-config'
        headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
        with open(data, 'rb') as payload:
            infraenv_api_call = requests.patch(api_url, data=payload, headers=headers)

    def installCluster(self,cluster_id):
        api_url = 'http://'+ str(hostname) + ':8090/api/assisted-install/v2/clusters/' + cluster_id + '/actions/install'
        requests.post(api_url)

    def finishInstallation(self,cluster_id):
        api_url = 'http://'+ str(hostname) + ':8090/api/assisted-install/v2/clusters/' + cluster_id + '/actions/complete-installation'
        headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
        data = '{"is_success":true}'
        requests.post(api_url, data=data, headers=headers)


class redFish:
    def __init__(self,bmc_user,bmc_password,bmc_ip,bmc_insertmedia_path,bmc_ejectmedia_path,bmc_resetsystem_path,bmc_system_path,hostname,ip):
        self.bmc_user = bmc_user
        self.bmc_password = bmc_password
        self.bmc_ip = bmc_ip
        self.bmc_insertmedia_path = bmc_insertmedia_path
        self.bmc_ejectmedia_path = bmc_ejectmedia_path
        self.bmc_resetsystem_path = bmc_resetsystem_path
        self.bmc_system_path = bmc_system_path
        self.hostname = hostname
        self.ip = ip

    def insertVirtualMedia(self):
        iso_path = 'http://' + str(self.ip) + '/ocp_ai.iso'
        api_url = 'https://'+ str(self.bmc_ip) + self.bmc_insertmedia_path
        api_url2 = 'https://'+ str(self.bmc_ip) + self.bmc_system_path
        headers = {'Content-Type': 'application/json'}
        data = '{"Image": "'+ iso_path +'", "Inserted": true}'
        data2 = '{"Boot": {"BootSourceOverrideTarget": "Cd", "BootSourceOverrideMode": "UEFI", "BootSourceOverrideEnabled": "Once"}}'

        print('INFO: Setting the iso image as the virtualmedia device for server: ' + self.bmc_ip)
        insert_iso = requests.post(api_url, data=data, headers=headers, verify=False, auth=(self.bmc_user, self.bmc_password))
        time.sleep(10)
        set_insert_iso = requests.patch(api_url2, data=data2, headers=headers, verify=False, auth=(self.bmc_user, self.bmc_password))
        time.sleep(10)
        return insert_iso, set_insert_iso

    def ejectVirtualMedia(self):
        iso_path = 'http://' + str(self.hostname) + '/ocp_ai.iso'
        api_url = 'https://'+ str(self.bmc_ip) + self.bmc_ejectmedia_path
        headers = {'Content-Type': 'application/json'}
        data = '{}'

        print('INFO: Ejecting any iso image as a virtualmedia device for server: ' + self.bmc_ip)
        eject_iso = requests.post(api_url, data=data, headers=headers, verify=False, auth=(self.bmc_user, self.bmc_password))
        time.sleep(10)
        return eject_iso

    def powerOn(self):
        api_url = 'https://'+ str(self.bmc_ip) + self.bmc_resetsystem_path
        headers = {'Content-Type': 'application/json'}
        data = '{"ResetType": "On"}'

        print('INFO: Powering on the server: ' + str(self.bmc_ip))
        poweron_system = requests.post(api_url, data=data, headers=headers, verify=False, auth=(self.bmc_user, self.bmc_password))
        return poweron_system

    def powerOff(self):
        api_url = 'https://'+ str(self.bmc_ip) + self.bmc_resetsystem_path
        headers = {'Content-Type': 'application/json'}
        data = '{"ResetType": "ForceOff"}'

        print('INFO: Shutting down the server: ' + str(self.bmc_ip))
        poweroff_system = requests.post(api_url, data=data, headers=headers, verify=False, auth=(self.bmc_user, self.bmc_password))
        time.sleep(10)
        return poweroff_system

    def forceRestart(self):
        api_url = 'https://'+ str(self.bmc_ip) + self.bmc_resetsystem_path
        headers = {'Content-Type': 'application/json'}
        data = {'ResetType': 'ForceRestart'}

        print('INFO: Restarting the server: ' + str(self.bmc_ip))
        reset_system = requests.post(api_url, data=data, headers=headers, verify=False, auth=(self.bmc_user, self.bmc_password))
        return reset_system

def helpMenu():
    print('Usage: ' + sys.argv[0] + ' -f <PARAMETERS_FILE>')

def redFishLauncher(num_masters,bmc_user,bmc_password,bmc_ip,bmc_insertmedia_path,bmc_ejectmedia_path,bmc_resetsystem_path,bmc_system_path,hostname,ip):
    if num_masters > 1:
        print('\nINFO: This is a multi-node installation, it will be required to set VirtualMedia in ' + str(num_masters) + ' servers')
        print('------------------------------------------------------------------------------------------------------------------------')
        for masterip in bmc_ip:
            console_ip = masterip
            bmc_ops = redFish(bmc_user,bmc_password,console_ip,bmc_insertmedia_path,bmc_ejectmedia_path,bmc_resetsystem_path,bmc_system_path,hostname,ip)
            bmc_ops.powerOff()
            bmc_ops.ejectVirtualMedia()
            bmc_ops.insertVirtualMedia()
            bmc_ops.powerOn()
            print('------------------------------------------------------------------------------------------------------------------------')

    elif num_masters == 1:
        print('\nINFO: This is a SNO installation, it will be required to set VirtualMedia in ' + str(num_masters) + ' servers')
        print('------------------------------------------------------------------------------------------------------------------------')
        bmc_ip = bmc_ip[0]
        bmc_ops = redFish(bmc_user,bmc_password,bmc_ip,bmc_insertmedia_path,bmc_ejectmedia_path,bmc_resetsystem_path,bmc_system_path,hostname,ip)
        bmc_ops.powerOff()
        bmc_ops.ejectVirtualMedia()
        bmc_ops.insertVirtualMedia()
        bmc_ops.powerOn()
        print('------------------------------------------------------------------------------------------------------------------------')
    else:
        print('ERROR: ' + str(num_masters) + ' servers to install, it is not a valid value')
        exit(2)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:", ["help", "file="])
        if not opts:
            print('No options provided!')
            helpMenu()
            sys.exit(1)
    except getopt.GetoptError as err:
        print(err)
        helpMenu()
        sys.exit(2)
    for opt, arg in opts:
        if len(opts) < 1:
            print('ERROR: Missing required arguments!')
            helpMenu()
            sys.exit(2)
        if opt in ("-h", "--help"):
            helpMenu()
            sys.exit(2)
        elif opt in ("-f", "--file"):
            file = arg

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            ocpinfraconf = cluster(file,"ocp_infra_configs","cluster.json")
            getocpinfraconf = ocpinfraconf.getParams()

            clusterconf = cluster(file,"cluster_configs","cluster.json")
            getclusterconf = clusterconf.getParams()
            insertclusterconf = clusterconf.insertParams(getclusterconf)
            cluster_id = clusterconf.deployCluster(getclusterconf)

            infraconf = cluster(file,"infraenv_configs","infraenv.json",cluster_id)
            getinfraconf = infraconf.getParams()
            insertinfraconf = infraconf.insertParams(getinfraconf)
            infraenv_id = infraconf.deployInfraEnv()
            infraconf.getIso(infraenv_id)

            redFishLauncher(num_masters,bmc_user,bmc_password,bmc_ip,bmc_insertmedia_path,bmc_ejectmedia_path,bmc_resetsystem_path,bmc_system_path,hostname,ip)
            infraconf.getInfraHostsStatus(infraenv_id,num_masters)
            clusterconf.patchClusterConfig(cluster_id,api_vip,num_masters)
            clusterconf.getClusterStatus(cluster_id,"Cluster ready to be installed")

            clusterconf.patchInstallConfig(cluster_id)
            clusterconf.uploadManifests(cluster_id)
            clusterconf.installCluster(cluster_id)

            clusterconf.getClusterStatus(cluster_id,"Cluster is installed")
            clusterconf.finishInstallation(cluster_id)


## MAIN ##
if __name__=='__main__':
    main()
## END MAIN ##
