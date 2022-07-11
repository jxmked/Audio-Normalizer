#!/usr/bin/env python3

import os

import eyed3
import re
from sys import argv as params

params.pop(0)

# change directory. 
# Directory must be existing
paths = {
    "input" : "Input",
    "output" : "Output",
    "metadata" : "Metadata",
    "lyrics" : "Lyrics",
    "albumArt" : "Album Cover"
}

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
        "silenceremove=start_periods=%s:start_silence=%s:start_threshold=%s" % (1 ,0.1, "-50dB"),
        "areverse"
    )
    
    return pat

def getLyrics(file):
    
    audiofile = eyed3.load(file)
    
    try:
        return audiofile.tag.lyrics[0].text
    except IndexError:
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
    print("")
    print("-+" * 8, end="-\n")
    print(" ".join(arr))
    print("-+" * 8, end="-\n")
    return os.system(" ".join(arr)) == 0
    
def getNormalize(num):
    return -abs(num) if num > 0 else abs(num)
    

# If error file is not empty.
# Copy those text here and rerun
s = """
.mp3
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
    b = os.path.join(paths["output"], file)
    
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
    res = execute([
        "ffmpeg -y",
        "-nostdin -hide_banner",
        "-i \"%s\"" % a,
        "-an -vcodec copy",
        "\"%s\"" % albumArt
    ])
    
    if not res:
        exit(1)
    
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
    
    # Insert Metadata and Convert to MP3
    res = execute([
        "ffmpeg -y", # Overwrite Existing File
        "-nostdin -hide_banner", # Disable Inputs abd Hide Banner
        "-i \"%s.wav\"" % sample, # Import Audio File
        "-i \"%s\"" % metadata, # Import Metadata
        "-i \"%s\"" % albumArt, # Import Album Art
        "-map 0:0 -map 2:0", # Mapping Audio File and Album Art
        "-id3v2_version 3", # Force ID3 version
        "-metadata:s:v title=\"Album cover\"", # Inserting Title to Album Art
        "-metadata:s:v comment=\"Cover (front)\"", # Setting up Album Art
        "-c:a libmp3lame", # MP3 Lossy Codec
        "-b:a 192k", # Medium Bitrate
        "-map_metadata 1", # Inserting Metadata
        "\"%s\"" % b
    ])
    
    
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
    
    setLyrics(b, lyric, lrcFile)
    

print("Decibels Adjustment")
for con in suc:
    print("  File: %s" % con["title"])
    print("  Decibels: %s" % con["decibels"])
    print()

fopen = open("errors.txt", "w")

fopen.write("\n".join(err))

fopen.close()

# Written By Jovan De Guia
# Github: jxmked