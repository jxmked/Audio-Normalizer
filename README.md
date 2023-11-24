# Audio-Normalizer

Handling Batch Audio Files

- Remove Silence from both end of an audio file
- Extract Metadata
- Extract Lyrics and create *.lrc file if possible
- Extract Album Cover (If possible)
- Increase or Decrease volume automatically to normalize it
- mp3 (libmp3lame) output
- Re-encoding audio file
- Also converts video into mp3 


### Usage

Place your audio file(s) into "Input" folder

Execute `python script.py` then wait until its done

You will see the processed audio file(s) in output folder 
with its metadata, album art, lyric file in their designated folder

Adjust your minimum silence to your needs and make sure
bit rate to your likings. 


### Note:
 > Make sure you had an FFMPEG installed into your machine
 > and an eyed3 

### Requires

- ffmpeg
- eyed3

## Socials

- [Github](https://github.com/jxmked)
- [Facebook](https://www.facebook.com/deguia25)
