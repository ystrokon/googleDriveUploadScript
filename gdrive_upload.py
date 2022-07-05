"""
Authenticate and upload files on Google Drive with PyDrive.

Usage:
    python gdrive_upload.py (--credentials CREDENTIALS_FILE OR --service-account-key SERVICE_ACCOUNT_KEY_FILE --file FILE_TO_UPLOAD
        (optional) --name UPLOADED_FILE_NAME --directory-name GDRIVE_FOLDER_NAME --directory-id GDRIVE_FOLDER_ID

Expected workflow is:
    - Using service account key:
        1. Creating service account and key: https://cloud.google.com/endpoints/docs/openapi/service-account-authentication#create_service_account
        
        2. Create folder on your Google Drive and grant access for this account(via its e-mail) to it. 
        
        3. Get this directory ID. Open the folder and copy it from the url. ID example: 1d3lpRUK7NrabIt_lkt3pNR2vD8LJGcAo
        (Without --directory-id it will upload your file God knows where)
        
        3. Run this script with --service-account-key and --directory-id arguments. 
        
    - Using project OAuth2.0 token:
        (this approach will require your manual interaction on the generating credentials file stage. However if you save credentials.json, you wont need to auth with browser again)
        1. Download the client secret file(client_secret.json). If you haven't one, please follow this tutorial:  https://pythonhosted.org/PyDrive/quickstart.html#authentication
        
        2. Get credentials(credentials.json) via execution of gdrive_get_credentials.py using downloaded client secret file.
        
        3. Run this script with --credentials argument

"""

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFileList
import googleapiclient.errors
from oauth2client.service_account import ServiceAccountCredentials

from argparse import ArgumentParser
import ast


def parse_args():
    """ Parse arguments """

    parser = ArgumentParser(description="Upload local files to Google Drive")
    parser.add_argument('-c', '--credentials', type=str,
                        help='Credentials file for GoogleAuth().LoadCredentialsFile. Use gdrive_get_credentials.py')
    parser.add_argument('-s', '--service-account-key', type=str,
                        help='Service account JSON key file for GoogleAuth()')
    parser.add_argument('-f', '--file', type=str, help='File to upload', required=True)
    parser.add_argument('-n', '--name', type=str, help='Destination name in Google Drive(optional)', required=False)
    parser.add_argument('-dn', '--directory-name', type=str,
                        help='Folder name(in gdrive root dir) to upload in (optional)', required=False)
    parser.add_argument('-di', '--directory-id', type=str, help='Folder id to upload in (optional)', required=False)

    args = parser.parse_args()

    if not args.credentials and not args.service_account_key:
        raise Exception("Specify at least one way to authorize(--credentials or --service-account-key")
    return args


def auth_with_credentials(credentials_file='credentials.json'):
    """ Authentication using credentials_file. Use gdrive_get_credentials.py """

    gauth = GoogleAuth()

    gauth.LoadCredentialsFile(credentials_file)
    # print(f"gauth.credentials: {gauth.credentials}, \ngauth.access_token_expired: {gauth.access_token_expired}")
    if gauth.credentials is None:
        raise Exception(f"Error while loading {credentials_file}")
    elif gauth.access_token_expired:
        print("Token expired. Refreshing token")
        gauth.Refresh()
    else:
        print("Authorizing using current token")
        gauth.Authorize()
    print("Successfully authorized")

    return gauth


def auth_with_service_account_key(service_account_key):
    """
        Authentication using service account key(JSON) (https://cloud.google.com/endpoints/docs/openapi/service-account-authentication)
    """

    gauth = GoogleAuth()
    scope = ["https://www.googleapis.com/auth/drive"]
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(service_account_key, scope)
    gauth.Authorize()

    return gauth


def get_folder_id_by_name(drive, parent_folder_id: str, folder_name: str):
    """ Check if destination folder exists and if so return it's ID """

    # Auto-iterate through all files in the parent folder.
    file_list = GoogleDriveFileList()
    try:
        file_list = drive.ListFile( {'q': "'{0}' in parents and trashed=false".format(parent_folder_id)} ).GetList()
    # Exit if the parent folder doesn't exist
    except googleapiclient.errors.HttpError as err:
        # Parse error message
        message = ast.literal_eval(err.content)['error']['message']
        if message == 'File not found: ':
            print(message + folder_name)
            exit(1)
        # Exit with stacktrace in case of other error
        else:
            raise

    # Find the destination folder in the parent folder's files
    for file1 in file_list:
        if file1['title'] == folder_name:
            print('title: %s, id: %s' % (file1['title'], file1['id']))
            return file1['id']


def upload(drive, file_to_upload: str, parent_folder_id='', uploaded_file_name=''):
    """ Upload file """

    upload_args = {}
    if uploaded_file_name:
        upload_args["title"] = uploaded_file_name
    if parent_folder_id:
        upload_args["parents"] = [{"kind": "drive#fileLink","id": parent_folder_id}]

    file = drive.CreateFile(upload_args)
    file.SetContentFile(file_to_upload)
    print(f"Uploading file")
    file.Upload(param={'supportsTeamDrives': True})


def main():
    """ Main """

    args = parse_args()

    # auth
    gauth = ""
    if args.credentials:
        gauth = auth_with_credentials(args.credentials)
    elif args.service_account_key:
        gauth = auth_with_service_account_key(args.service_account_key)
    else:
        raise Exception("Actually we cannot get here, cause we are filtering this case on parse_args()")

    # drive
    drive = GoogleDrive(gauth)
    parent_folder_id = ''
    if args.directory_id:
        parent_folder_id = args.directory_id
    elif args.directory_name:
        parent_folder_id = get_folder_id_by_name(drive, 'root', args.directory_name)
        if not parent_folder_id:
            raise Exception(f"Cannot find parent directory {args.directory_name}")
    upload(drive, args.file, parent_folder_id, args.name)


if __name__ == "__main__":
    main()
