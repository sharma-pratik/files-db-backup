from utils import yaml_to_python_obj, get_current_dir
from crontab import CronTab
import os


DATA = yaml_to_python_obj() # Read the yaml file
LOGGED_USER = os.getlogin()
FILE_BACKUP_SCRIPT = "backup.py" # Actual script that will be run by the cronjob

# Cron setup. Remove all existing jobs
CRON = CronTab(user=LOGGED_USER)
jobs = CRON.find_comment("backup-jobs")

# removing jobs
for j in jobs:
    CRON.remove(j)

CRON.write()

# itervate over each project
for project_details in DATA["PROJECTS"]:
    
    # work with each backups types like file and/or database
    for backup_details in project_details["BACKUPS"]:

        # iterate over each backup types
        for backup_type in backup_details.keys():
            # iterate over list of back types
            for each_backup_detail in backup_details[backup_type]:
                
                # cron_job_details will in json format that will be pass a command line value for cronjob statement
                cron_job_details = each_backup_detail
                intervals = cron_job_details.pop("INTERVALS")
                
                # Getting python executable
                python = os.environ['_'] 

                # For e.g - /path/to/env/bin/python /path/to/root_project/backup.py
                base_command = "{} {}".format(python, os.path.join(get_current_dir(), FILE_BACKUP_SCRIPT)) 

                # Creating multiple cronjob for each intervals
                for interval in intervals:
                    command = base_command +' "{}"'.format(cron_job_details)
                    job = CRON.new(command=command, comment="backup-jobs")
                    job.setall(interval)
                
                CRON.write()