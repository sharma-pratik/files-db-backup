from utils import *
from onedriveapi import OneDriveClient
import sys,json
import os

BACKUP_DATA = json.loads(sys.argv[1].replace("'", '"')) # Reading json data passed as command line argument


onedrive_client = OneDriveClient()

backup_files_path = BACKUP_DATA.get("FILE_PATH")
db_backup = BACKUP_DATA.get("DB_INFO", False)
ssh_details = BACKUP_DATA.get("SSH", None)

# Backup is of type database
if db_backup:
    to_upload_file = create_backup_sql_file(db_backup, ssh_details)

# Backup is of type file
else:
    to_upload_file = create_backup_zip_file(backup_files_path,ssh_details)

for storage_loc_detial in BACKUP_DATA["UPLOAD_TO"]:

    # Currently only supporting backing up to onedrive
    if storage_loc_detial["STORAGE_NAME"] == "ONEDRIVE":
        
        cloud_storage_path = storage_loc_detial["PATH"]
        # Splitting path into the list of folder names. For e.g : /project/local/database_backup/ --> [project,local,database_backup]
        cloud_folder_list = [path for path in cloud_storage_path.split("/") if path]

        # Create nested folder in cloud storage for uploading file
        onedrive_client.setup_nested_folders(folder_list=cloud_folder_list)

        # Delete the file if it exceed the max limit for files in folder
        onedrive_client.delete_exceed_files_in_folder(folder_path=cloud_storage_path)

        # Start upload
        onedrive_client.upload_file_to_ondrive(
            file_path = to_upload_file,
            onedrive_upload_path = storage_loc_detial["PATH"]
        )

        # removing file as this file is stored in tmp folder of host
        os.remove(to_upload_file)