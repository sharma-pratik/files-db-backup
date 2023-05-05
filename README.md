# File Structure Explaination
1. main.py 
    - This file read from confi yaml file and add appropriate cron jobs on host.
2. backup.py
    - This file will be run by the cron jobs. Depend on the cronjob, it will do the executation of making backup to cloud storage.

3. env.sample
    - Represent as sample file for storage environments variables.
4. config.yaml
    - Represent the configuration file for storing information of files and database backups.
    - The structure contains multiple projects with their names. 
        ```
            PROJECTS:
                - NAME : project_name
        ```
    - Each project can have multiple backups. Each backup can be of two types i.e. file and database backup
        ```
            PROJECTS:
                - NAME : project_name
                  BACKUPS:
                    - FILE_BACKUP :
                    - DB_BACKUPS :
        
        ```

    - Each backup can be run at multipel intervals and can be uploaded to mulitple storage location. The intervals will contain time for cronjob. And storage location contain information of cloud storage name and storage location.
        ```
            PROJECTS:
                - NAME : project_name
                  BACKUPS:
                    - FILE_BACKUP :
                        - INTERVALS:
                            - "3 * 2 * *"
                            - "1 * 1 * *"
                        - UPLOAD_TO:
                            - STORAGE_NAME : ONEDRIVE
                                PATH: from/to/path
                        
                    - DB_BACKUPS :
                        - INTERVALS:
                            - "3 * 2 * *"
                            - "1 * 1 * *"
                        - UPLOAD_TO:
                            - STORAGE_NAME : ONEDRIVE
                                PATH: from/to/path
                        - DB_INFO:
                            USERNAME : username
                            PASSWORD : password
                            PORT : 5432
                            NAME : db_name
                            HOST : localhost
        ```
    - For file backup type, it contain the list of folder/files path that need to be backup in `FILE_PATH` section. All path details will be zipped and get's uploaded. 
        ```
            PROJECTS:
                - NAME : project_name
                BACKUPS:
                    - FILE_BACKUP :
                        - INTERVALS:
                            - "3 * 2 * *"
                            - "1 * 1 * *"
                        - UPLOAD_TO:
                            - STORAGE_NAME : ONEDRIVE
                                PATH: from/to/path
                        - SSH:
                            USERNAME: username
                            IP_ADDRESS: 10.010.110.1
        ```
    - For database backup type, it contain database connection information. There are two case for database backup i.e. postgres can be run in some container or else directly on the host. In cas of doceker, set following details for docker
    ```
        DOCKER : 
            CONTAINER_NAME : container name
    ```
    - Each backup can contain ssh details. In this way, the program will do the backing up over the remote server connecting with ssh otherwise it will do on the local host.
5. requirements.txt
    - List of packages need by the projects.
6. utils.py
    - Contains functions used by the programs


# Project Setup Guidelines
1. Create a .env file in the root project to store env variables. Check .env.sample for list of important env variables used by the project.
2. Structure for config.yaml file
3. Create python virtual env in the root project.
4. Add the cronjob to run `main.py` file
    ```
        crontab -e
    ```
    ```
        * * * * * path/to/env/bin/python path/to/rootproject/main.pys
    ```
5. Add the ssh detials of current host to all the remote server which will be used for backup.


# OneDrive Setup
1. Register an app in azure portal
2. Go to API Permissions, click on Add a permission, click on Microsoft graph, select Application permissions and add following permissions
    - Directory.Read.All
    - Files.Read
    - Files.Read.All
    - Files.Read.All
    - Files.Read.Selected
    - Files.ReadWrite
    - Files.ReadWrite.All
    - Files.ReadWrite.All
    - Files.ReadWrite.AppFolder
    - Files.ReadWrite.Selected
    - User.Read.All
3. Generate secret values. Go to Certificates & secrets, Generate new client secret. Copy Secret ID value to CLIENT_SECRET variable in .env file
4. Go to overview, copy tenant and client id and add to .env file