"""
Getting credentials file.

Usage: python gdrive_get_credentials.py --client-secret CLIENT_SECRETS_FILE
    (optional) --output-file WHERE_TO_SAVE_CREDENTIALS_FILE

Expected workflow is:
    1. Download the client secret file(client_secret.json). If you haven't one, please follow this tutorial:  https://pythonhosted.org/PyDrive/quickstart.html#authentication

    2. Execute this script. It will open a browser tab in which you have to login with your 
    Google account. It will create a credentials file (file path will be printed).

    3. You can use created credentials(output_file) for GoogleAuth().LoadClientConfigFile for authentication.
"""

from pydrive.auth import GoogleAuth
import os
from argparse import ArgumentParser


def parse_args():
    """ Parse arguments """

    parser = ArgumentParser(description="Get Google Drive credentials for client secret.")
    parser.add_argument('-c', '--client-secret', type=str, help='Client secret file from Google Drive Console',
                        required=True)
    parser.add_argument('-o', '--output-file', type=str, help='Credentials file path/name')

    return parser.parse_args()


def get_credentials(client_secret: str, output_file=''):

    gauth = GoogleAuth()
    # changing flow settings. These changes are replacing settings.get_refresh_token: True
    gauth.GetFlow()
    gauth.flow.params.update({'access_type': 'offline'})
    gauth.flow.params.update({'approval_prompt': 'force'})
    # Authenticate using client-secret
    gauth.LoadClientConfigFile(client_secret)
    gauth.LocalWebserverAuth()
    # Save credentials to file
    if not output_file:
        output_file = os.path.join(os.getcwd(), 'credentials.json')
    gauth.SaveCredentialsFile(output_file)

    print(f"Credentials file saved to {output_file}")


if '__main__' == __name__:
    args = parse_args()
    get_credentials(args.client_secret, args.output_file)
