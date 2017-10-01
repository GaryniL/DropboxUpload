"""
Backs up a directory to Dropbox.
Example app for API v2.
"""

import os,sys

import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError

import six, unicodedata
import time,datetime


# Add OAuth2 access token here.
# You can generate one for yourself in the App Console.
# See <https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/>

TOKEN = ''
DIRECTORY_PATH = '/backupFolder/'
# It will backup beneath your dropbox application folder
# ex. /Dropbox/Application/YOURAPPNAME/DROPBOX_FOLDER_NAME/
DROPBOX_FOLDER_NAME = '/backupFolderOnDropbox/'

# config
showFileDescription = False


def searchDirectory(dbx):
    local_path = os.getcwd()+DIRECTORY_PATH

    for dn, dirs, files in os.walk(local_path):
        # print dn, dirs, files

        subfolder = dn[len(local_path):].strip(os.path.sep)
        print '[File] Descending into ', subfolder

        for name in files:
            fullname = os.path.join(dn, name)
            if not isinstance(name, six.text_type):
                name = name.decode('utf-8')
            nname = unicodedata.normalize('NFC', name)
            if name.startswith('.'):
                if showFileDescription == True:
                    print '[File] Skipping dot file:', name
            elif name.startswith('@') or name.endswith('~'):
                if showFileDescription == True:
                    print '[File] Skipping temporary file:', name
            elif name.endswith('.pyc') or name.endswith('.pyo'):
                if showFileDescription == True:
                    print '[File] Skipping generated file:', name
            else:
                uploadFile(dbx, fullname, DROPBOX_FOLDER_NAME, subfolder, name)


def uploadFile(dbx, fullname, folder, subfolder, name, overwrite=False):
    """Upload a file.
    Return the request response, or None in case of error.
    """
    path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    while '//' in path:
        path = path.replace('//', '/')
    mode = (dropbox.files.WriteMode.overwrite
            if overwrite
            else dropbox.files.WriteMode.add)
    mtime = os.path.getmtime(fullname)

    print '[Dropbox] Start upload ', path
    with open(fullname, 'rb') as f:
        data = f.read()
    try:
        res = dbx.files_upload(
            data, path,
            client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
            mute=True,
            mode=WriteMode('overwrite'))
    except dropbox.exceptions.ApiError as err:
        print '[Dropbox] *** API error', err
        return None
        # This checks for the specific error where a user doesn't have
        # enough Dropbox space quota to upload this file
        if (err.error.is_path() and
                err.error.get_path().error.is_insufficient_space()):
            sys.exit("[Dropbox] ERROR: Cannot back up; insufficient space.")
        elif err.user_message_text:
            print '[Dropbox]' ,err.user_message_text
            sys.exit()
        else:
            print '[Dropbox]' ,err
            sys.exit()

    print '[Dropbox] Uploaded ', res.name.encode('utf8'), ' done.'
    return

if __name__ == '__main__':
    # Check for an access token
    if (len(TOKEN) == 0):
        sys.exit("[Dropbox] ERROR: Looks like you didn't add your access token. "
            "Open up backup-and-restore-example.py in a text editor and "
            "paste in your token in line 14.")

    # Create an instance of a Dropbox class, which can make requests to the API.
    print("[Dropbox] Creating a Dropbox object...")
    dbx = dropbox.Dropbox(TOKEN)

    # Check that the access token is valid
    try:
        dbx.users_get_current_account()
    except AuthError as err:
        sys.exit("[Dropbox] ERROR: Invalid access token; try re-generating an "
            "access token from the app console on the web.")

    # Create a backup of the current settings file
    searchDirectory(dbx)

    print("[Sys] Upload all files!")