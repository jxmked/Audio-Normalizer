#!/usr/bin/env python3

import os
import eyed3
import re

# change directory. 
# Directory must be existing
paths = {
    "input" : "Input",
    "output" : "Output",
    "metadata" : "Metadata",
    "lyrics" : "Lyrics",
    "albumArt" : "Album Cover"
}


MIN_SILENCE="-100dB"

BIT_RATE="128k"


def getFiles(dirIn, types):
    # From Time-Lapse v3.0 (Not yet finish)
    f = []
    
    if types == "*" or "*" in types:
        return os.listdir(dirIn)
    
    for file in os.listdir(dirIn):
        for ext in types:
            if file.endswith("%s" % ext):
                f.append(file)
    return f

def createSilenceRemoveFilter(cnt):
    # From Time-Lapse v3.0 (Not yet finish)
    pat = "{0},{1},{0},{1}".format(
        "silenceremove=start_periods=%s:start_silence=%s:start_threshold=%s" % (1 ,0.1, MIN_SILENCE),
        "areverse"
    )
    
    return pat

def getLyrics(file):
    
    audiofile = eyed3.load(file)
    
    try:
        return audiofile.tag.lyrics[0].text
    except (IndexError, AttributeError):
        return ""

def setLyrics(file, lyric, lrcOut):
    os.system(" ".join([
        "eyeD3",
        "--encoding utf8",
        "--add-lyrics \"%s\"" % lrcOut,
        "\"%s\"" % file
    ]))

def filename(path):
    # From Time-Lapse v3.0 (Not yet finish)
    return os.path.splitext(os.path.basename(path))[0]

def execute(arr, s=1):
    if not s:
        return
    print(flush=True)
    print("-+" * 8, end="-\n", flush=True)
    print(" ".join(arr), flush=True)
    print("-+" * 8, end="-\n", flush=True)
    return os.system(" ".join(arr)) == 0
    
def getNormalize(num):
    return -abs(num) if num > 0 else abs(num)
    

# If error file is not empty.
# Copy those text here and rerun
s = """
.mp3
.mp4
"""

# Remove empty value from array
s = [x for x in s.split("\n") if x]

err = []
suc = []

for file in getFiles(paths["input"], s):
    
    # Filename without Extension
    fn = filename(file)
    
    # Absolute Path to file without extension
    sample = os.path.join(paths["metadata"], fn)
    
    # Input folder
    a = os.path.join(paths["input"], file)
    
    # Output folder
    b = os.path.join(paths["output"], fn)
    
    # Output lrc File
    lrcFile = os.path.join(paths["lyrics"], "%s.lrc" % fn)
    
    # Output Metadata File
    metadata = "%s.txt" % sample
    
    albumArt = "%s.jpg" % os.path.join(paths["albumArt"], fn)
    
    # Lyric Text
    lyric = getLyrics(a)
    
    # Create Tmp text file contains Information about audio
    
  
    res = execute([
        "ffmpeg",
        "-nostdin -hide_banner",
        "-i \"%s\"" % a,
        "-af 'volumedetect'",
        "-vn -sn -dn",
        "-f null /dev/null",
        "&> ffmpeg_volumedetect.txt"
    ])
    
    if not res:
        exit(1)
    
    # Get Album Art
    hasAlbumCover = execute([
        "ffmpeg -y",
        "-nostdin -hide_banner",
        "-i \"%s\"" % a,
        "-an -vcodec copy",
        "\"%s\"" % albumArt
    ])
    
    if not hasAlbumCover:
      try:
          os.remove(albumArt) # Empty file
      except:
          pass
    
    f = open("ffmpeg_volumedetect.txt", "r")
    s = f.read()
    f.close()
    
    try:
        # Get max_volume decibels from raw txt file
        # My best regex for this. Hahaha
        found = re.search('(max_volume:\s)([\-0-9.]+)(\s*dB)', str(s)).group(2)
    except AttributeError:
        found = ''
    
    # Export Metadata from Original audio file
    res = execute([
        "ffmpeg -y",
        "-nostdin -hide_banner",
        "-i \"%s\"" % a,
        "-f ffmetadata \"%s\"" % metadata
    ])
    
    if not res:
        exit(1)
    
    # Create lrc file
    f = open(lrcFile, "w")
    f.write(lyric)
    f.close()
    
    # Increasing or Decreasing the defualt volume according to
    # its maximum decibels
    vlm = ",volume=%sdB" % getNormalize(float(found)) if found else ""
    
    # Convert And Trim Both end to Wav first
    res = execute([
        "ffmpeg -y",
        "-nostdin -hide_banner",
        
        "-i \"%s\"" % a,
        
        # Trim Both End
        "-af '%s%s'" % (createSilenceRemoveFilter(1), vlm),
        
        # Remove All Metadata
        "-write_xing 0 -id3v2_version 0",
        "-vn -sn",
        "\"%s.wav\"" % sample
    ])
    
    if not res:
        exit(1)
    
    
    toMp3Cmd = [
        "ffmpeg -y", # Overwrite Existing File
        "-nostdin -hide_banner", # Disable Inputs abd Hide Banner
        "-i \"%s.wav\"" % sample, # Import Audio File
        "-i \"%s\"" % metadata, # Import Metadata
        "-id3v2_version 3", # Force ID3 version
        "-c:a libmp3lame", # MP3 Lossy Codec
        "-f mp3",
        "-b:a %s" ^ BIT_RATE, # Medium Bitrate
        "-map_metadata 1", # Inserting Metadata
        "\"%s.mp3\"" % b
    ]
    if hasAlbumCover:
        toMp3Cmd.insert(4, " ".join([
            "-i \"%s\"" % albumArt, # Import Album Art
            "-map 0:0 -map 2:0", # Mapping Audio File and Album Art
            "-metadata:s:v title=\"Album cover\"", # Inserting Title to Album Art
            "-metadata:s:v comment=\"Cover (front)\"", # Setting up Album Art
        ]))
    
    # Insert Metadata and Convert to MP3
    res = execute(toMp3Cmd)
    
    
    os.remove("%s.wav" % sample)
    os.remove("ffmpeg_volumedetect.txt")
    
    if res:
        suc.append({
            "title" : file,
            "decibels" : found
        })
    else:
        err.append(file)
        continue
    
    setLyrics("%s.mp3" % b, lyric, lrcFile)
    

print("Decibels Adjustment", flush=True)
for con in suc:
    print("  File: %s" % con["title"],flush=True)
    print("  Decibels: %s" % con["decibels"],flush=True)
    print(flush=True)

fopen = open("errors.txt", "w")

fopen.write("\n".join(err))

fopen.close()

# Written By Jovan De Guia
# Github: jxmked