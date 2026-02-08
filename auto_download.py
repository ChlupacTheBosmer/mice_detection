#!/usr/bin/env python3
"""
Bulk downloader for camera‑trap mouse/rat videos and datasets.

This script automates two distinct tasks:

1. **Video downloads** – Given a list of web URLs, it attempts to fetch the
   underlying video streams using the `yt_dlp` library.  The URLs may point
   directly at YouTube, MSN, Talker News or other hosts that embed a video.
   `yt_dlp` automatically resolves embedded players and extracts the
   highest quality stream.  Each video is saved into a configurable
   destination directory using the title reported by the host site.

2. **Dataset downloads** – A set of direct archive URLs is provided for
   Zenodo and CaltechDATA datasets.  These archives can be very large
   (gigabytes), so downloads are performed using the standard `requests`
   library in streaming mode.  Progress feedback is printed to the
   terminal.  If a dataset already exists in the destination directory,
   it will not be downloaded again.

Usage:

```
python download_mice_videos_and_datasets.py
```

The script can be customised by editing the `VIDEO_URLS` and
`DATASET_URLS` lists at the bottom of the file.  Ensure that `yt_dlp`
is installed in your Python environment (`pip install yt‑dlp`) before
running the script; otherwise only dataset downloads will proceed.

Note:
* Newsflare videos often require a licence purchase.  If `yt_dlp`
  cannot extract a free preview stream, the script will print an error
  and continue.
* The large dataset downloads may take a long time and require
  sufficient disk space.  Interrupting a download will leave a
  partially downloaded file that you can resume by re‑running the
  script.
"""

import os
import sys
import errno
from urllib.parse import urlparse, unquote

import requests

def download_file(url: str, dest_folder: str) -> str:
    """Stream a file from `url` to `dest_folder`.

    Args:
        url: Direct download URL to a binary file (e.g. zip archive).
        dest_folder: Directory where the file will be stored.

    Returns:
        The path to the downloaded file on disk.

    Raises:
        requests.HTTPError: If the HTTP request fails.
    """
    os.makedirs(dest_folder, exist_ok=True)
    parsed = urlparse(url)
    filename = unquote(os.path.basename(parsed.path)) or "downloaded_file"
    dest_path = os.path.join(dest_folder, filename)

    if os.path.exists(dest_path):
        print(f"[INFO] {filename} already exists – skipping.")
        return dest_path

    print(f"[INFO] Downloading dataset archive from {url}")
    with requests.get(url, stream=True) as resp:
        resp.raise_for_status()
        total_size = int(resp.headers.get('Content-Length', 0))
        downloaded = 0
        with open(dest_path, 'wb') as file_handle:
            for chunk in resp.iter_content(chunk_size=8 * 1024):
                if not chunk:
                    continue
                file_handle.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = downloaded * 100.0 / total_size
                    sys.stdout.write(f"\r    {filename}: {percent:.2f}%")
                    sys.stdout.flush()
        if total_size:
            sys.stdout.write("\n")
    print(f"[INFO] Finished downloading {filename}")
    return dest_path

def download_videos(video_urls, dest_folder: str) -> None:
    """Download videos from arbitrary web pages using yt_dlp.

    Args:
        video_urls: Iterable of URLs to process.
        dest_folder: Directory where the videos will be saved.
    """
    try:
        import yt_dlp  # type: ignore
    except ImportError:
        print("[WARNING] yt_dlp is not installed.\n"
              "Install it with `pip install yt-dlp` to enable video downloads.")
        return

    os.makedirs(dest_folder, exist_ok=True)
    ydl_opts = {
        'outtmpl': os.path.join(dest_folder, '%(title)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'quiet': False,
        'ignoreerrors': True,
        'merge_output_format': 'mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in video_urls:
            try:
                print(f"[INFO] Downloading video from {url}")
                ydl.download([url])
            except Exception as exc:
                print(f"[ERROR] Failed to download {url}: {exc}")

def main() -> None:
    """Entry point for the downloader script."""
    VIDEO_URLS = [
        'https://www.youtube.com/watch?v=CIc-Eeh7IUY',
        'https://www.youtube.com/watch?v=MFMHu1YEYQo',
        # 'https://www.newsflare.com/video/806359/mouse-triggers-trail-camera-unexpected-wildlife-moment',
        'https://www.msn.com/en-us/video/animals/hidden-camera-captures-a-tiny-mouse-collecting-food/vi-AA1Sv1nx',
        'https://www.youtube.com/watch?v=NfX6bm9x1i4',
        'https://www.youtube.com/watch?v=pGJbyh7oE2U',
        'https://www.youtube.com/watch?v=cP-___7Pva4',
        'https://www.youtube.com/watch?v=yqfF9e9PHj4',
        'https://www.youtube.com/watch?v=n3gfYT5Bw_g',
        'https://www.youtube.com/watch?v=wHWCjBzk6zc',
        'https://www.youtube.com/watch?v=Rs0KxwonI7k',
    ]
    DATASET_URLS = [
        'https://zenodo.org/record/3636136/files/RGB_D_Rat_Behavioral_Dataset_AnnotatedSection.zip?download=1',
        'https://zenodo.org/record/3636136/files/RGB_D_Rat_Behavioral_Dataset_NonannotatedSection.zip?download=1',
        'https://zenodo.org/record/15112879/files/Dataset_128_16x9x10K_Color.zip?download=1',
        'https://data.caltech.edu/records/4emt5-b0t10/files/CRIM13_res.zip?download=1',
        'https://data.caltech.edu/records/4emt5-b0t10/files/CRIM13_test1.zip?download=1',
        'https://data.caltech.edu/records/4emt5-b0t10/files/CRIM13_test2.zip?download=1',
        'https://data.caltech.edu/records/4emt5-b0t10/files/CRIM13_train1.zip?download=1',
        'https://data.caltech.edu/records/4emt5-b0t10/files/CRIM13_train2.zip?download=1',
        'https://data.caltech.edu/records/4emt5-b0t10/files/CRIM13_validation.zip?download=1',
    ]
    download_videos(VIDEO_URLS, dest_folder='downloaded_videos')
    for dataset_url in DATASET_URLS:
        try:
            download_file(dataset_url, dest_folder='downloaded_datasets')
        except requests.HTTPError as err:
            print(f"[ERROR] Failed to download dataset from {dataset_url}: {err}")

if __name__ == '__main__':
    main()