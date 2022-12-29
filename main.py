import time
from pytube import YouTube
from pytube import Playlist
import os
import moviepy.editor as mp
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import multiprocessing
from multiprocessing import current_process
from rich import print
from rich.console import Console
from rich.table import Table
from rich import progress
from concurrent.futures import ProcessPoolExecutor
import sys



def download(url, drive, progress, task_id):

    def on_complete(stream, file_path):
        progress[task_id] = {"progress": 2, "total": 4, "status": "Converting..."}
        ytfile = file_path
        mp4_path = ytfile
        mp3_path = ytfile.split('.mp4')[0]+'.mp3'
        title = os.path.basename(mp3_path)
        new_file = mp.AudioFileClip(mp4_path)
        new_file.write_audiofile(mp3_path, verbose=False, logger=None)
        os.remove(mp4_path)
        progress[task_id] = {"progress": 3, "total": 4, "status": "Uploading..."}
        gfile = drive.CreateFile({'parents': [{'id': '1IrESQhwTstwkiZuCNQusAXoAeTHVpTLp'}], 'title': title})
        gfile.SetContentFile(mp3_path)
        gfile.Upload()
        progress[task_id] = {"progress": 4, "total": 4, "status": "Complete!"}

    try: 
        progress[task_id] = {"progress": 1, "total": 4, "status": "Downloading..."}
        YouTube(url,on_complete_callback=on_complete).streams.filter(file_extension='mp4').first().download()
    except:
        progress[task_id] = {"progress": 1, "total": 4, "status": "Downloading Again..."}
        YouTube(url,on_complete_callback=on_complete).streams.filter(file_extension='mp4').first().download()



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


    playlist = Playlist("https://www.youtube.com/playlist?list=PLOWDZJe5wh3j2HkdsxNe7yDeZrow5XRsD")

    print('Trashing Old Songs From Drive', flush=True)
    gfiles = drive.ListFile({'q': "'1IrESQhwTstwkiZuCNQusAXoAeTHVpTLp' in parents and trashed=false"}).GetList()
    for file in gfiles:
        file.Trash()
    print('Trashing Complete', flush=True)



    print('Starting Downloads...\n', flush=True)

    songs = 14

    with progress.Progress(
            progress.SpinnerColumn(),
            "[progress.description]{task.description}",
            "[bold yellow]{task.fields[status]}",
            progress.BarColumn(),
            progress.MofNCompleteColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            progress.TimeElapsedColumn(),
            refresh_per_second=20,  # bit slower updates
        ) as progress:
            futures = []  # keep track of the jobs
            with multiprocessing.Manager() as manager:
                # this is the key - we share some state between our 
                # main process and our worker functions
                _progress = manager.dict()
                overall_progress_task = progress.add_task("[green]All jobs progress:", status="Working...", extend=True)

                with ProcessPoolExecutor() as executor:
                    for url in playlist[:songs]:  # iterate over the jobs we need to run
                        # set visible false so we don't have a lot of bars all at once:
                        task_id = progress.add_task(f"{YouTube(url).title}", status='Loading...', visible=True)
                        futures.append(executor.submit(download, url, drive, _progress, task_id))

                    # monitor the progress:
                    while (n_finished := sum([future.done() for future in futures])) < len(
                        futures
                    ):
                        progress.update(
                            overall_progress_task, completed=n_finished, total=len(futures)
                        )
                        sys.stderr.write(f'Total complete: {int(n_finished/len(futures)*100)}%\n')
                        sys.stderr.flush()
                        for task_id, update_data in _progress.items():
                            latest = update_data["progress"]
                            total = update_data["total"]
                            status = update_data["status"]
                            # update the progress bar for this task:
                            progress.update(
                                task_id,
                                status=status,
                                completed=latest,
                                total=total,
                                visible=latest <= total,
                            )
                    progress.update(
                            overall_progress_task, completed=n_finished, total=len(futures), status="Complete!"
                        )
                    time.sleep(.5)
                    sys.stderr.write(f'Total complete: {int(n_finished/len(futures)*100)}%')
                    sys.stderr.flush()
                    time.sleep(.5)
                    # raise any errors:
                    for future in futures:
                        future.result()