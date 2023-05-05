import requests
import yaml
import os
import tempfile
import uuid
from office365.graph_client import GraphClient
from office365.sharepoint.client_context import ClientContext
from pprint import pprint


def yaml_to_python_obj():
    """
        Used to convert the yaml structure to python objects.
    """
    YAML_FILE_PATH = "config.yaml"
    try:
        with open(os.path.join(get_current_dir(),YAML_FILE_PATH), 'r') as file:
            parse_yaml = yaml.safe_load(file)
        return parse_yaml
    except Exception as e:
        print(e.args)


def create_backup_zip_file(folder_path,ssh_details):
    """
        Used to create zip file by executing zip command.
        In case if files are at remote server, program will
        connect with ssh, run zip command over there, copy zip from 
        remote to local at tmp folder and return the file, otherwise
        it will create zip file locally only.

        PARAMS
        ------
            folder_path : list
                List of folder/files path which will be zipped.
            ssh_details : dict, None
                Details of ssh connection like username and hostname
        
        RETURN
        ------
            zip file path : string
    """

    # create zip file in tmp folder
    zip_file = tempfile.gettempdir()+"/"+ uuid.uuid4().hex+".zip"
    folder_path = " ".join(folder_path)
    command = "zip {} -r {}".format(zip_file, folder_path)
    if ssh_details:
        hostname = ssh_details["USERNAME"]
        ipaddress = ssh_details["IP_ADDRESS"]
        #TODO remove pem file location
        # command that will run over remote server
        command = f"ssh -i /etc/RTFTanksServer.pem {hostname}@{ipaddress} {command}"
       
        command = command + f"; scp -i /etc/RTFTanksServer.pem {hostname}@{ipaddress}:{zip_file} {zip_file}; ssh -i /etc/RTFTanksServer.pem {hostname}@{ipaddress} rm {zip_file}"
    os.system(command)

    return zip_file

def create_backup_sql_file(db_con_details, ssh_details):
    """
        Create sql file over server or locally after using database connection
        info.

        PARAMS
        ------
            db_con_details : dict
                database connection details
            ssh_details : dict, None
                Details of ssh connection like username and hostname
        
        RETURN
        ------
            sql file path : string
    """
    
    USERNAME = db_con_details.get("USERNAME")
    PASSWORD = db_con_details.get("PASSWORD")
    PORT = db_con_details.get("PORT")
    DB_NAME = db_con_details.get("NAME")
    HOST = db_con_details.get("HOST")
    tmp_sql_file_path = tempfile.gettempdir()+"/"+ uuid.uuid4().hex+".sql"
    is_docker = db_con_details.get("DOCKER", False)

    # Pg dump command to generate sql file
    command = f"PGPASSWORD={PASSWORD} pg_dump -U {USERNAME} -h {HOST} -p {PORT} {DB_NAME}"

    if is_docker:
        container_name = db_con_details.get("DOCKER")["CONTAINER_NAME"]
        command = f"docker exec -i {container_name} /bin/bash -c '{command}'"

    command = command + f" > {tmp_sql_file_path}"
    if ssh_details:
        hostname = ssh_details["USERNAME"]
        ipaddress = ssh_details["IP_ADDRESS"]
        #TODO remove pem file location
        command = f"ssh {hostname}@{ipaddress} \"{command}\""
       
        command = command + f"; scp {hostname}@{ipaddress}:{tmp_sql_file_path} {tmp_sql_file_path}; ssh {hostname}@{ipaddress} rm {tmp_sql_file_path}"
    
    os.system(command)  

    return tmp_sql_file_path

def get_current_dir():
    return os.path.dirname(__file__)
