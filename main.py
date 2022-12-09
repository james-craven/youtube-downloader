from pytube import YouTube
from pytube import Playlist
import os
import moviepy.editor as mp
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import multiprocessing
from pytube.cli import on_progress

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

global drive 
drive = GoogleDrive(gauth)

def download(url, drive):

    try: 
        YouTube(url,on_progress_callback=on_progress, on_complete_callback=on_complete).streams.filter(file_extension='mp4').first().download()
    except:
        YouTube(url,on_progress_callback=on_progress, on_complete_callback=on_complete).streams.filter(file_extension='mp4').first().download()
    print("(:") 

def on_complete(stream, file_path):
    ytfile = file_path
    mp4_path = ytfile
    mp3_path = ytfile.split('.mp4')[0]+'.mp3'
    title = os.path.basename(mp3_path)
    new_file = mp.AudioFileClip(mp4_path)
    new_file.write_audiofile(mp3_path, verbose=False)
    os.remove(mp4_path)
    print(f'Completed: {title}')
    print(f'Uploading: {title}')
    gfile = drive.CreateFile({'parents': [{'id': '1IrESQhwTstwkiZuCNQusAXoAeTHVpTLp'}], 'title': title})
    gfile.SetContentFile(mp3_path)
    gfile.Upload()
    print(f'Drive Upload Completed For {title}')

if __name__ == '__main__':

        

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

    print('Trashing Old Songs From Drive')
    gfiles = drive.ListFile({'q': "'1IrESQhwTstwkiZuCNQusAXoAeTHVpTLp' in parents and trashed=false"}).GetList()
    for file in gfiles:
        file.Trash()
    print('Trashing Complete')

    threads = []

    print('Starting Downloads...\n')
    for url in playlist[:5]:
        t = multiprocessing.Process(target=download, args=[url, drive])
        t.start()
        threads.append(t)

    for thread in threads:
        thread.join()
