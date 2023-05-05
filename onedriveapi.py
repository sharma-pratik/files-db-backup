from dataclasses import dataclass
import imp
from multiprocessing import parent_process
from pprint import pprint
import msal
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv(os.path.dirname(__file__) + "/.env")

MAX_FILE_LIMIT_FOLDER = int(os.environ["MAX_FILES_COUNT"])


class OneDriveClient:

    TENANT_ID= os.environ["TENANT_ID"]
    CLIENT_SECRET = os.environ["CLIENT_SECRET"]
    CLIENT_ID = os.environ["CLIENT_ID"]
    BASE_GRAPH_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self):
        access_token = self.get_access_token()
        self.headers = {
            "Authorization" : "Bearer "+ access_token
        }
        self.user_id = self.get_user_id()
        self.drive_id = self.get_drive_id()

    def get_drive_id(self):
        """
            Return the default drive from onedrive. There exists atleast one drive over onedrive
            
            RETURN
            ------
                id : string
                    Unqiue drive id.
        """
        my_drive_url = self.BASE_GRAPH_URL + f"/users/{self.user_id}/drive"

        response = requests.get(my_drive_url, headers=self.headers)

        if response.status_code == 200:
            return json.loads(response.content.decode("utf-8"))["id"]
        else:
            return None

    def get_user_id(self):
        """
            Return the user id of admin user

            RETURN
            ------
                id : string
                    Unqiue drive id.
        """
        my_drive_url = self.BASE_GRAPH_URL + f"/users"

        response = requests.get(my_drive_url, headers=self.headers)

        user_id = None
        if response.status_code == 200:
            for user_detail in json.loads(response.content.decode("utf-8"))["value"]:
                if "admin" in user_detail["userPrincipalName"]:
                    user_id = user_detail["id"]    
        
        return user_id
    


    def get_access_token(self):
        """
            Acquire token via MSAL that will used during making 
            successive APIs calls

            RETURN
            ------
                id : string
                    Access token.
        """
        authority_url = f'https://login.microsoftonline.com/{self.TENANT_ID}'
        app = msal.ConfidentialClientApplication(
            authority=authority_url,
            client_id=f'{self.CLIENT_ID}',
            client_credential=f'{self.CLIENT_SECRET}',
        )
        result = app.acquire_token_silent(["https://graph.microsoft.com/.default"], account=None)
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        access_token = result["access_token"]

        return access_token

    def setup_nested_folders(self, folder_list):

        """
            It will create nested folder over OneDrive.
            It will call the drive items API on root level ( in OneDrive ) to 
            first check if root folder exists for not. In case of not exists, it will 
            call create_folder function to create folder else, if exists, it will take
            the unique folder id and assign it to parent_folder_id variable. Again it 
            will check folder exists for nested folder with parent id (parent folder name).

            PARAMS
            ------
                folder_list : list
                    list of folder. first item will be root folder,while other
                    will be nested folder.
        """
        
        parent_folder_id = None
        for folder in folder_list:

            # get list of items in specific folder. 
            drive_items_details = self.get_drive_items(folder_id=parent_folder_id)

            # Create folder if current folder does not exists
            if folder not in drive_items_details["item_list"]:
                parent_folder_id = self.create_folder(folder_id=parent_folder_id, folder_name=folder)
            else:
                # if folder exists, take its id, which will become parent to search next folder 
                for item in drive_items_details["data"]:
                    if folder == item["name"]:
                        parent_folder_id = item["id"]
                        break

    def delete_exceed_files_in_folder(self, folder_path):

        """
            It will delete the files in case if it exceed the list

            PARAMS
            ------
                folder_list : string
                    full path of the folder to check.
        """

        # This API give the id of the folder by passing full path of the folder
        folder_info_url = self.BASE_GRAPH_URL + f'/users/{self.user_id}/drives/{self.drive_id}/root:/{folder_path}'
        response = requests.get(folder_info_url, headers=self.headers)

        if response.status_code == 200:
            response_data = json.loads(response.content.decode("utf-8"))
        
        folder_id = response_data["id"]
        items_count = response_data["folder"]["childCount"]

        if items_count > MAX_FILE_LIMIT_FOLDER:

            # Calling the items API to get list of items in the folder
            children_list_url = self.BASE_GRAPH_URL +  f'/drives/{self.drive_id}/items/{folder_id}/children'
            response = requests.get(children_list_url, headers=self.headers)
            response_data = json.loads(response.content.decode("utf-8"))

            # get first file id within the folder and delete it
            file_id = response_data["value"][0]["id"]
            delete_url =  self.BASE_GRAPH_URL + f'/drives/{self.drive_id}/items/{file_id}'
            
            response = requests.delete(delete_url, headers=self.headers)
            if response.status_code == 204:
                print("successfully deleted")
            else:
                print("Unable to delete item")
            

    def get_drive_items(self, folder_id=None):

        """
            It will give list of items within the folder

            PARAMS
            ------
            folder_id : str

            RETURN
            ------
                items list : list[dict]
                    List of folder items containg item unqiue id
                    and it's name

        """

        # In case of finding the items in the root folder
        if folder_id == None:
            children_list_url = f"/users/{self.user_id}/drive/root/children"

        # In case of finding the items in the specific folder
        else:
            children_list_url = f'/users/{self.user_id}/drives/{self.drive_id}/items/{folder_id}/children'

        url = self.BASE_GRAPH_URL + children_list_url

        response = requests.get(url, headers=self.headers)
        drive_items_details = {"data": [], "item_list" : []}
        if response.status_code == 200:
            response_data = json.loads(response.content.decode("utf-8"))
            for data in response_data["value"]:
                drive_items_details["data"].append({"id" : data["id"], "name" : data["name"]})
                drive_items_details["item_list"].append(data["name"])
        
        return drive_items_details


    def upload_file_to_ondrive(self, file_path, onedrive_upload_path):
        
        """
            Used to upload file over onedrive in specific folder
            
            PARAMS
            ------
                file_path : str
                    path of file that need to be uploaded
                onedrive_upload_path : str
                    path of onedrive folder where file will be uploaded

            RETURN
            ------
                None
        """
        
        try:
            with open(file_path, "rb") as f:
                binary_file_data = f.read()
            
            file_name = file_path.split("/")[-1]

            url = self.BASE_GRAPH_URL + f"/users/{self.user_id}/drive/root:/{onedrive_upload_path +'/'+file_name}:/content"
            response = requests.put(
                url,
                data = binary_file_data,
                headers=self.headers
            )
            response_data = json.loads(response.content.decode("utf-8"))
            print(response_data)
            if response.status_code == 201:
                print({"success" : True, "msg" : "Uploaded successfully"})
            else:
                print({"success" : False, "msg" : f"Error uploading file. Response : {response_data}"})

        except Exception as e:
            print({"success" : False, "msg" : e.args})

    def create_folder(self, folder_id=None, folder_name=None):

        """
            Used to create folder
            
            PARAMS
            ------
                folder_id : str
                    parent folder id to create folder within it.
                folder_name : str
                    name of folder to create

            RETURN
            ------
                id : str
                    Id of the created folder.

        """
        
        if folder_id == None:
            url = self.BASE_GRAPH_URL + f"/users/{self.user_id}/drive/root/children"
        else:
            url = self.BASE_GRAPH_URL + f"/users/{self.user_id}/drives/{self.drive_id}/items/{folder_id}/children"
        
        print("create_folder", url)
        headers = self.headers
        
        headers.update({"Content-Type" : "application/json"})
        response = requests.post(
            url,
            json={"name": folder_name, "folder": {}},
            headers=headers
        )
        print("create_folder", response.content)
        if response.status_code == 201:
            response_data = json.loads(response.content.decode("utf-8"))
            return response_data["id"]
        else:
            print(f"Error creating folder with name {folder_name}")
            return ""