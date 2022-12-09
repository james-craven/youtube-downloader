from pytube import YouTube
from pytube import Playlist
import os
import moviepy.editor as mp
import re
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
gauth = GoogleAuth()

# Try to load saved client credentials
gauth.LoadCredentialsFile("mycreds.txt")

if gauth.credentials is None:
    # Authenticate if they're not there

    # This is what solved the issues:
    gauth.GetFlow()
    gauth.flow.params.update({'access_type': 'offline'})
    gauth.flow.params.update({'approval_prompt': 'force'})

    gauth.LocalWebserverAuth()

elif gauth.access_token_expired:

    # Refresh them if expired

    gauth.Refresh()
else:

    # Initialize the saved creds

    gauth.Authorize()

# Save the current credentials to a file
gauth.SaveCredentialsFile("mycreds.txt")  

drive = GoogleDrive(gauth)


playlist = Playlist("https://www.youtube.com/playlist?list=PLrxcNWZXdQ2kDOkW-S86MyRJkZiwxhL6c")

for url in playlist[:20]:
    print(f'Downloading: {YouTube(url).title}')
    YouTube(url).streams.filter(file_extension='mp4').first().download()
    folder = os.getcwd()
    for file in os.listdir(folder):
        if re.search('mp4', file):
            mp4_path = os.path.join(folder,file)
            mp3_path = os.path.join(folder,os.path.splitext(file)[0]+'.mp3')
            title = os.path.splitext(file)[0]+'.mp3'
            new_file = mp.AudioFileClip(mp4_path)
            new_file.write_audiofile(mp3_path)
            os.remove(mp4_path)
            print(f'Completed: {YouTube(url).title}')
            print(f'Uploading: {YouTube(url).title}')
            gfile = drive.CreateFile({'parents': [{'id': '1IrESQhwTstwkiZuCNQusAXoAeTHVpTLp'}], 'title': title})
            gfile.SetContentFile(mp3_path)
            gfile.Upload()
            print('Drive Upload Completed')