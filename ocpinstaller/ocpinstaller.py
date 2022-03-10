#!/usr/bin/env python3

import base64
import getopt
import json
import logging
import os
import requests
import socket
import sys
import time
import wget
import yaml

from collections import OrderedDict
from datetime import datetime


logging.basicConfig()
LOG = logging.getLogger(__name__)


class Cluster:
    def __init__(self, file, params, deployfile, cluster_id='null'):
        self.file = file
        self.params = params
        self.cluster_id = cluster_id
        self.deployfile = deployfile
        LOG.setLevel(logging.INFO)
        LOG.warning("Suppressing requests library SSL Warnings")
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )

    def get_params(self):
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
            LOG.info(
                "cluster_id parameter already set in the paramfile.yaml, \
                    please remove it before running this program")
            exit(1)

        with open(file, 'a') as param_file:
            if cluster_id == 'null':
                LOG.info("Getting parameters for cluster deployment")
            else:
                LOG.info(
                    "Appending the cluster_id parameter cluster_id: " +
                    cluster_id +
                    " to the paramfile.yaml")
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

    def insert_params(self, fileparams):
        deployfile = self.deployfile
        LOG.info(
            "writting configs into the " +
            deployfile +
            "file")
        with open(
                'resources/configs/' +
                str(deployfile),
                'w') as cluster_config_file:
            json.dump(fileparams, cluster_config_file)

    def deploy_cluster(self, clusterconf):
        api_url = build_api_url_string(
            "http",
            hostname,
            "8090",
            "/api/assisted-install/v2/clusters")
        cluster_id_dict = {}

        if clusterconf["high_availability_mode"] == 'None':
            LOG.info(
                "Installing a SNO cluster, \
                    high_availability_mode set to: " +
                clusterconf["high_availability_mode"])
        elif clusterconf["high_availability_mode"] == 'Full':
            LOG.info(
                "Installing a Multi node cluster, \
                    high_availability_mode set to: " +
                clusterconf["high_availability_mode"])

        with open(data, 'rb') as payload:
            requests.post(api_url, data=payload, headers=headers)

        cluster_json_api = json.loads(requests.get(api_url).text)
        existing_deployments = len(cluster_json_api)
        for num_deployment in range(existing_deployments):
            cluster_json = cluster_json_api[num_deployment]
            cluster_id = cluster_json['id']
            cluster_creation_time = cluster_json['created_at']
            cluster_id_dict[cluster_id] = cluster_creation_time
        ordered_cluster_id = sort_dict_by_creation_date(
            cluster_id_dict,
            "%Y-%m-%dT%H:%M:%S.%fZ")
        cluster_id = list(ordered_cluster_id.keys())[0]
        created_at = list(ordered_cluster_id.values())[0]

        LOG.info(
            "Cluster deployed with cluster_id: " +
            cluster_id +
            ' , created at: ' +
            created_at)
        return cluster_id

    def deploy_infraEnv(self):
        api_url = build_api_url_string(
            "http",
            hostname,
            "8090",
            "/api/assisted-install/v2/infra-envs")
        infraenv_id_dict = {}

        with open(data, 'rb') as payload:
            requests.post(api_url, data=payload, headers=headers)

        infraenv_json_api = json.loads(requests.get(api_url).text)
        existing_infraenvs = len(infraenv_json_api)
        for num_infraenv in range(existing_infraenvs):
            infraenv_json = infraenv_json_api[num_infraenv]
            infraenv_id = infraenv_json['id']
            infraenv_creation_time = infraenv_json['created_at']
            infraenv_id_dict[infraenv_id] = infraenv_creation_time
        ordered_infraenv_id = sort_dict_by_creation_date(
            infraenv_id_dict,
            "%Y-%m-%dT%H:%M:%S.%fZ")
        infraenv_id = list(ordered_infraenv_id.keys())[0]
        created_at = list(ordered_infraenv_id.values())[0]

        LOG.info(
            "InfraEnv deployed with infraenv_id: " +
            infraenv_id +
            ' , created at: ' +
            created_at)
        return infraenv_id

    def get_iso(self, infraenv_id):
        api_url = build_api_url_string(
            "http",
            hostname,
            "8090",
            "/api/assisted-install/v2/infra-envs/" +
            infraenv_id +
            "/downloads/image-url")
        print(api_url)

        get_iso_json_api = json.loads(requests.get(api_url).text)
        get_iso = get_iso_json_api['url']
        iso_name = http_path + '/ocp_ai.iso'
        wget.download(get_iso, iso_name)

    def get_cluster_status(self, cluster_id, status_message):
        get_clusterstatus = 'Not checked yet'
        while get_clusterstatus != status_message:
            LOG.info(
                "The cluster status is: " +
                get_clusterstatus +
                " , cluster_id: " +
                cluster_id)
            LOG.info(
                "Waiting for: " +
                status_message)
            time.sleep(30)
            api_url = build_api_url_string(
                "http",
                hostname,
                "8090",
                "/api/assisted-install/v2/clusters/" +
                cluster_id)
            get_clusterstatus_json_api = json.loads(requests.get(api_url).text)
            get_clusterstatus = get_clusterstatus_json_api['status_info']

    def get_infra_hosts_status(self, infraenv_id, num_masters):
        api_url = build_api_url_string(
            "http",
            hostname,
            "8090",
            "/api/assisted-install/v2/infra-envs/" +
            infraenv_id +
            "/hosts")
        while len(json.loads(requests.get(api_url).text)) == 0:
            LOG.info("Waiting for hosts to be registered")
            time.sleep(30)
        if num_masters > 1:
            for master in range(num_masters):
                get_host_status = 'Not checked yet'
                while get_host_status != "Host is ready to be installed":
                    get_host_status_json_api = json.loads(
                        requests.get(api_url).text)
                    get_host_status_json = get_host_status_json_api[master]
                    master_id = get_host_status_json['id']
                    LOG.info(
                        "The infraenv host " +
                        master_id +
                        " status is: " +
                        get_host_status)
                    get_host_status = get_host_status_json['status_info']
                    time.sleep(10)
        elif num_masters == 1:
            get_host_status = 'Not checked yet'
            while get_host_status != "Host is ready to be installed":
                get_host_status_json_api = json.loads(
                    requests.get(api_url).text)
                get_host_status_json = get_host_status_json_api[0]
                master_id = get_host_status_json['id']
                LOG.info(
                    "The infraenv host " +
                    master_id +
                    " status is: " +
                    get_host_status)
                get_host_status = get_host_status_json['status_info']
                time.sleep(10)
        else:
            LOG.error(
                str(num_masters) +
                " servers to install, it is not a valid value")
            exit(2)

    def upload_manifests(self, cluster_id):
        api_url = build_api_url_string(
            "http",
            hostname,
            "8090",
            "/api/assisted-install/v2/clusters/" +
            cluster_id +
            "/manifests")
        headers = {
            'Content-Type': 'application/json',
            'accept': 'application/json'}
        path = 'resources/manifests'
        for manifest in os.listdir(path):
            file = os.path.join(path, manifest)
            if os.path.isfile(file):
                LOG.info(
                    "Adding new manifest: " +
                    file)
                with open(file, 'rb') as manifest_file:
                    data = manifest_file.read()
                    encoded = base64.b64encode(data)
                    encodedtext = encoded.decode('utf-8')
                    split_name = file.split("/", 2)
                    manifest_name = split_name[2]
                    data = '{"folder": "openshift","file_name":"' \
                        + manifest_name + \
                            '","content":"' + encodedtext + '"}'
                    upload_manifest_api_call = requests.post(
                        api_url,
                        data=data,
                        headers=headers)
        get_manifests_json_api = json.loads(
            requests.get(api_url).text)
        num_manifests = len(get_manifests_json_api)
        LOG.info("These are the manifests will be deployed with OpenShift:\n")
        for deployed_manifest in range(num_manifests):
            get_manifests_json = get_manifests_json_api[deployed_manifest]
            print(get_manifests_json['file_name'])

    def patch_cluster_config(self, cluster_id, api_vip, num_masters):
        if num_masters > 1:
            data = '{ "api_vip": "' + api_vip + '"}'
            api_url = build_api_url_string(
                "http",
                hostname,
                "8090",
                "/api/assisted-install/v2/clusters/" +
                cluster_id)
            headers = {
                'Content-Type': 'application/json',
                'accept': 'application/json'}
            requests.patch(api_url, data=data, headers=headers)

    def patch_install_config(self, cluster_id):
        data = 'resources/configs/install-config-patch'
        api_url = build_api_url_string(
            "http",
            hostname,
            "8090",
            "/api/assisted-install/v2/clusters/" +
            cluster_id +
            "/install-config")
        headers = {
            'Content-Type': 'application/json',
            'accept': 'application/json'}
        with open(data, 'rb') as payload:
            infraenv_api_call = requests.patch(api_url, data=payload, headers=headers)

    def install_cluster(self, cluster_id):
        api_url = build_api_url_string(
            "http",
            hostname,
            "8090",
            "/api/assisted-install/v2/clusters/" +
            cluster_id +
            "/actions/install")
        requests.post(api_url)

    def finish_installation(self, cluster_id):
        api_url = build_api_url_string(
            "http",
            hostname,
            "8090",
            "/api/assisted-install/v2/clusters/" +
            cluster_id +
            "/actions/complete-installation")
        headers = {
            'Content-Type': 'application/json',
            'accept': 'application/json'}
        data = '{"is_success":true}'
        requests.post(api_url, data=data, headers=headers)


class Redfish:
    def __init__(
            self,
            bmc_user,
            bmc_password,
            bmc_ip,
            bmc_insertmedia_path,
            bmc_ejectmedia_path,
            bmc_resetsystem_path,
            bmc_system_path,
            hostname,
            ip):
        self.bmc_user = bmc_user
        self.bmc_password = bmc_password
        self.bmc_ip = bmc_ip
        self.bmc_insertmedia_path = bmc_insertmedia_path
        self.bmc_ejectmedia_path = bmc_ejectmedia_path
        self.bmc_resetsystem_path = bmc_resetsystem_path
        self.bmc_system_path = bmc_system_path
        self.hostname = hostname
        self.ip = ip

        LOG.setLevel(logging.INFO)
        LOG.warning("Suppressing requests library SSL Warnings")
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )

    def insert_virtual_media(self):
        iso_path = build_api_url_string(
            "http",
            self.ip,
            "80",
            "/ocp_ai.iso")
        api_url = build_api_url_string(
            "https",
            self.bmc_ip,
            "443",
            self.bmc_insertmedia_path)
        api_url2 = build_api_url_string(
            "https",
            self.bmc_ip,
            "443",
            self.bmc_system_path)
        headers = {'Content-Type': 'application/json'}
        data = '{"Image": "'+ iso_path +'", "Inserted": true}'
        data2 = '{"Boot": {"BootSourceOverrideTarget": "Cd", "BootSourceOverrideMode": "UEFI", "BootSourceOverrideEnabled": "Once"}}'

        LOG.info(
            "Setting the iso image as the virtualmedia device for server: " +
            self.bmc_ip)
        insert_iso = requests.post(
            api_url,
            data=data,
            headers=headers,
            verify=False,
            auth=(
                self.bmc_user,
                self.bmc_password))
        time.sleep(10)
        set_insert_iso = requests.patch(
            api_url2,
            data=data2,
            headers=headers,
            verify=False,
            auth=(
                self.bmc_user,
                self.bmc_password))
        time.sleep(10)
        return insert_iso, set_insert_iso

    def eject_virtual_media(self):
        iso_path = build_api_url_string(
            "http",
            self.hostname,
            "80",
            "/ocp_ai.iso")
        api_url = build_api_url_string(
            "https",
            self.bmc_ip,
            "443",
            self.bmc_ejectmedia_path)
        headers = {'Content-Type': 'application/json'}
        data = '{}'

        LOG.info(
            "Ejecting any iso image as a virtualmedia device for server: " + 
            self.bmc_ip)
        eject_iso = requests.post(
            api_url,
            data=data,
            headers=headers,
            verify=False,
            auth=(
                self.bmc_user,
                self.bmc_password))
        time.sleep(10)
        return eject_iso

    def power_on(self):
        api_url = build_api_url_string(
            "https",
            self.bmc_ip,
            "443",
            self.bmc_resetsystem_path)
        headers = {'Content-Type': 'application/json'}
        data = '{"ResetType": "On"}'

        LOG.info(
            "Powering on the server: " +
            str(self.bmc_ip))
        poweron_system = requests.post(
            api_url,
            data=data,
            headers=headers,
            verify=False,
            auth=(
                self.bmc_user,
                self.bmc_password))
        return poweron_system

    def power_off(self):
        api_url = build_api_url_string(
            "https",
            self.bmc_ip,
            "443",
            self.bmc_resetsystem_path)
        headers = {'Content-Type': 'application/json'}
        data = '{"ResetType": "ForceOff"}'
        print(api_url)

        LOG.info(
            "Shutting down the server: " +
            str(self.bmc_ip))
        poweroff_system = requests.post(
            api_url,
            data=data,
            headers=headers,
            verify=False,
            auth=(
                self.bmc_user,
                self.bmc_password))
        time.sleep(10)
        return poweroff_system

    def force_restart(self):
        api_url = build_api_url_string(
            "https",
            self.bmc_ip,
            "443",
            self.bmc_resetsystem_path)
        headers = {'Content-Type': 'application/json'}
        data = {'ResetType': 'ForceRestart'}

        LOG.info(
            "Restarting the server: " +
            str(self.bmc_ip))
        reset_system = requests.post(
            api_url,
            data=data,
            headers=headers,
            verify=False,
            auth=(
                self.bmc_user,
                self.bmc_password))
        return reset_system

def help_menu():
    LOG.info("Usage: " + sys.argv[0] + " -f <PARAMETERS_FILE>")

def redfish_launcher(
        num_masters,
        bmc_user,
        bmc_password,
        bmc_ip,
        bmc_insertmedia_path,
        bmc_ejectmedia_path,
        bmc_resetsystem_path,
        bmc_system_path,
        hostname,ip):
    if num_masters > 1:
        LOG.info(
            "\nThis is a multi-node installation, it will be required to set VirtualMedia in " + 
            str(num_masters) +
            "servers")
        for masterip in bmc_ip:
            console_ip = masterip
            bmc_ops = Redfish(
                bmc_user,
                bmc_password,
                console_ip,
                bmc_insertmedia_path,
                bmc_ejectmedia_path,
                bmc_resetsystem_path,
                bmc_system_path,
                hostname,
                ip)
            bmc_ops.power_off()
            bmc_ops.eject_virtual_media()
            bmc_ops.insert_virtual_media()
            bmc_ops.power_on()

    elif num_masters == 1:
        LOG.info(
            "\nThis is a SNO installation, it will be required to set VirtualMedia in " + 
            str(num_masters) +
            "servers")
        bmc_ip = bmc_ip[0]
        bmc_ops = Redfish(
            bmc_user,
            bmc_password,
            bmc_ip,
            bmc_insertmedia_path,
            bmc_ejectmedia_path,
            bmc_resetsystem_path,
            bmc_system_path,
            hostname,ip)
        bmc_ops.power_off()
        bmc_ops.eject_virtual_media()
        bmc_ops.insert_virtual_media()
        bmc_ops.power_on()
    else:
        LOG.error(
            str(num_masters) +
            " servers to install, it is not a valid value")
        exit(2)

def sort_dict_by_creation_date(dict_data, date_format):
    ordered_data = OrderedDict(reversed(sorted(dict_data.items(), key=lambda x: datetime.strptime(x[1], date_format))))
    return ordered_data

def build_api_url_string(protocol, hostname, port, path):
    api_url = protocol + '://'+ str(hostname) + ':' + port + path
    return api_url

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:", ["help", "file="])
        if not opts:
            LOG.eror("No options provided")
            help_menu()
            sys.exit(1)
    except getopt.GetoptError as err:
        print(err)
        help_menu()
        sys.exit(2)
    for opt, arg in opts:
        if len(opts) < 1:
            LOG.error("Missing required arguments!")
            help_menu()
            sys.exit(2)
        if opt in ("-h", "--help"):
            help_menu()
            sys.exit(2)
        elif opt in ("-f", "--file"):
            file = arg

            ocpinfraconf = Cluster(file, "ocp_infra_configs", "cluster.json")
            ocpinfraconf.get_params()

            clusterconf = Cluster(file, "cluster_configs", "cluster.json")
            getclusterconf = clusterconf.get_params()
            clusterconf.insert_params(getclusterconf)
            cluster_id = clusterconf.deploy_cluster(getclusterconf)

            infraconf = Cluster(file, "infraenv_configs", "infraenv.json", cluster_id)
            getinfraconf = infraconf.get_params()
            infraconf.insert_params(getinfraconf)
            infraenv_id = infraconf.deploy_infraEnv()
            infraconf.get_iso(infraenv_id)

            redfish_launcher(
                num_masters,
                bmc_user,
                bmc_password,
                bmc_ip,
                bmc_insertmedia_path,
                bmc_ejectmedia_path,
                bmc_resetsystem_path,
                bmc_system_path,
                hostname,
                ip)
            infraconf.get_infra_hosts_status(infraenv_id, num_masters)
            clusterconf.patch_cluster_config(cluster_id, api_vip,num_masters)
            clusterconf.get_cluster_status(cluster_id, "Cluster ready to be installed")

            clusterconf.patch_install_config(cluster_id)
            clusterconf.upload_manifests(cluster_id)
            clusterconf.install_cluster(cluster_id)

            clusterconf.get_cluster_status(cluster_id, "Cluster is installed")
            clusterconf.finish_installation(cluster_id)


## MAIN ##
if __name__=='__main__':
    main()
## END MAIN ##
