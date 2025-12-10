import praw
import requests
import openai
import random
import pyttsx3
import os
import json
import string
import textwrap
import whisper_timestamped as whisper
from PIL import ImageFont
from openai import OpenAI
from dotenv import load_dotenv
from moviepy import VideoFileClip, ImageClip, TextClip, CompositeAudioClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips, vfx, concatenate_audioclips

import logging
logging.getLogger().setLevel(level=logging.WARNING)

#DEFAULT TOGGLER
useDefault = True

useGPT_TTS = False
subredditOption = ""
backgroundOption = ""

subreddits = ["confessions", "nosleep", "amitheasshole", "amioverreacting", "scarystories", "wholesomestories"]
if(useDefault):
    subredditOption = subreddits[random.randint(0,len(subreddits)-1)]
else:
    promptText = "-------------------\n"
    for i in range(0,len(subreddits)):
        promptText += f"{subreddits[i]}: {i}\n"
    promptText += "-------------------\nChoose a subreddit: "
    subredditOption = subreddits[int(input(promptText))]

if(useDefault):
    useGPT_TTS = True
else:
    if(input("Use ChatGPT 4o Mini TTS? (y/n): ").lower() == "y"):
        useGPT_TTS = True

bgVideoFiles = ["videos/parkour.mp4", "videos/satisfying.mp4", "videos/games.mp4", "videos/clashroyale.mp4"]
if(useDefault):
    backgroundOption = bgVideoFiles[2]
else:
    promptText = "-------------------\n"
    for i in range(0,len(bgVideoFiles)):
        promptText += f"{bgVideoFiles[i]}: {i}\n"
    promptText += "-------------------\nChoose a background video: "
    backgroundOption = bgVideoFiles[int(input(promptText))]

# Load enviroment variables
print("Loading enviroment variables...", end="\r")
load_dotenv()
print("Loading enviroment variables... DONE")
# Create session to bypass SSL
session = requests.Session()
session.verify = False

# Set openAI keys
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Create clients
print("Creating clients...", end="\r")
client_Pyttsx3 =  pyttsx3.init()
client_OpenAI = OpenAI()
client_Whisper =  whisper.load_model("small", "cpu")
print("Creating clients... DONE")

# Create summary of top story that doesn't have a picture in subreddit
print("Getting reddit post...")
# Reddit API credentials
import urllib3
urllib3.disable_warnings()

reddit = praw.Reddit(
    client_id="E0iglhUXcBkNve-q94t0zA",
    client_secret="L5aMpdQwQLYCD4Oj6H73Jgli7fFh8Q",
    user_agent="AttentionSeeker v1.0 by /u/OkChemical6335",
    requestor_kwargs={'session': session},
)

subreddit_name = subredditOption
subreddit = reddit.subreddit(subreddit_name)
usedPosts = []
with open("data/used_stories.txt", "r") as file:
    usedPosts = file.read().splitlines()
post = None
title = ""
summary = ""
numPosts = 1
validPost = False

while(not validPost):
    subredditPosts = subreddit.top(limit=numPosts,time_filter="week")
    for submission in subredditPosts:
        if(submission.is_self and not (submission.url in usedPosts) and not submission.over_18):
            validPost = True
            with open("data/used_stories.txt", "a") as file:
                file.write(submission.url + "\n")
            post = submission
            title = submission.title
            prompt = f"Summarize this Reddit story into a ~300-word YouTube Shorts-style narration script from the view of the poster. Start immediately with a shocking or emotional hook — no intro or explanation. Keep the pacing fast, the language casual and vivid. Highlight key twists, drama, and suspense, and end with an ironic or satisfying resolution. Make sure the summary fits the context and tone of the Reddit post title: {title}. Focus on retention — skip fluff, keep only the juiciest parts. Here’s the story:\n"+submission.selftext
            summary = submission.selftext
            response = client_OpenAI.responses.create(
                model="gpt-4.1-nano",
                input=prompt
            )
            summary = response.output_text
    numPosts += 1

videoTitle = client_OpenAI.responses.create(
                model="gpt-4.1-nano",
                input="Based on this Reddit story, generate a clickable YouTube Shorts title (under 60 characters). Make the title eye-catching, emotionally charged, and relevant to the Reddit post title. Include 3-5 relevant hashtags like #RedditStories, #Shorts, #Storytime, etc. Here's the story: "+summary
            ).output_text
videoDescription = client_OpenAI.responses.create(
                model="gpt-4.1-nano",
                input="Based on this Reddit story, create a short YouTube description (1-2 punchy teaser sentences). Don't give away the twist. Here's the story:"+summary
            ).output_text
print("Getting reddit post... DONE: "+submission.url)

# Generate title card
print("Creating title card...", end="\r")
normFont = "fonts\Verdana.ttf"
boldFont = "fonts\Verdana-Bold.ttf"

titleBgImage = ImageClip("images/title.png")

imageWidth, imageHeight = titleBgImage.size

subredditTextClip = TextClip(font=boldFont, text=f"r/{submission.subreddit.display_name}", font_size=28, color="gray")
subredditTextClip = subredditTextClip.with_position([imageWidth*0.14,imageHeight*0.06])
userTextClip = TextClip(font=normFont, text=f"u/{submission.author.name}", font_size=28, color=(15, 0, 184))
userTextClip = userTextClip.with_position([imageWidth*0.14,imageHeight*0.15])

def soft_wrap_text(
    text: str, 
    fontsize: int, 
    letter_spacing: int, 
    font_family: str, 
    max_width: int,
):
    # Note that font_family has to be an absolute path to your .ttf/.otf
    image_font = ImageFont.truetype(font_family, fontsize) 

    # I am not sure my letter spacing calculation is accurate
    text_width = image_font.getlength(text) + (len(text)-1) * letter_spacing 
    letter_width = text_width / len(text)

    if text_width < max_width:
        return text

    max_chars = max_width / letter_width
    wrapped_text = textwrap.fill(text, width=max_chars)
    return wrapped_text

titleText =  soft_wrap_text(title, 32, 0, r"C:\Users\Ashtoons\OneDrive\Documents\Projects\Python Programming\AttentionSeeker\AttentionSeeker\fonts\Verdana-Bold.ttf", imageWidth*0.9)
titleTextClip = TextClip(font=boldFont, text=f"{titleText}", font_size=32, color="black")
titleTextClip = titleTextClip.with_position([imageWidth*0.04, imageHeight*0.3])

scoreTextClip = TextClip(font=normFont, text=f"{submission.score}", font_size=28, color="black")
scoreTextClip = scoreTextClip.with_position([imageWidth*0.13, imageHeight*0.83])

commentNumTextClip = TextClip(font=normFont, text=f"{submission.num_comments}", font_size=28, color="black")
commentNumTextClip = commentNumTextClip.with_position([imageWidth*0.44, imageHeight*0.83])

titleBgImage =  CompositeVideoClip([titleBgImage, subredditTextClip, userTextClip, titleTextClip, scoreTextClip, commentNumTextClip])
titleBgImage.save_frame("output/resultTitleImg.png",  0)
print("Creating title card... DONE")

# Read summary in AI voice
print("Creating voiceover...", end="\r")
client_Pyttsx3.save_to_file(title+" "+summary, "output/resultAudio.mp3")
client_Pyttsx3.runAndWait()
if(useGPT_TTS):
    with client_OpenAI.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="ash",
        input=title+" "+summary,
        instructions="Tell the story in a casual, fast-paced, TikTok storytime voice — like it’s playing over Minecraft parkour. Make it sound dramatic and engaging, like you’re trying to keep someone from scrolling. Use pauses before big twists, and sound like a teenager telling gossip.",
    ) as response:
        response.stream_to_file("output/resultAudio.mp3")
audio = AudioFileClip("output/resultAudio.mp3")
print("Creating voiceover... DONE")

# Transcribe and save transcription as JSON
print("Transcribing audio...")
whisperAudio = whisper.load_audio("output/resultAudio.mp3")
transcription = whisper.transcribe(client_Whisper, whisperAudio)

with open('output/resultTranscription.json', 'w') as fp:
    json.dump(transcription, fp)
print("Transcribing audio... DONE")

# Create background video
print("Getting background video...", end="\r")

video = VideoFileClip(backgroundOption)
start = random.randint(0,int(video.duration-audio.duration))

video = video.subclipped(start, start+audio.duration)
print("Getting background video... DONE")

# Create subtitles
print("Adding subtitles...", end="\r")
textClipList = []
textOutlineClipList = []

subtitleFont = "fonts\LuckiestGuy-Regular.ttf"
subtitleFontSize = 56
subtitleStrokeWidth = 3

for s in range(len(transcription["segments"])):
    segment = transcription["segments"][s]
    for i in range(len(segment['words'])):
        word = segment['words'][i]
        text = word['text'].translate(str.maketrans('', '', string.punctuation))
        textClip = TextClip(font=subtitleFont, text=text, font_size=subtitleFontSize, color='white', text_align="center")
        textOutlineClip = TextClip(font=subtitleFont, text=text, font_size=subtitleFontSize, color='black', text_align="center", stroke_width=subtitleStrokeWidth, size=video.size)
        if(i < len(segment['words'])-1) :
            nextWord = segment['words'][i+1]
            textClip.duration = nextWord['start']-word['start']
        elif(s < len(transcription["segments"])-1):
            textClip.duration = transcription["segments"][s+1]['words'][0]['start']-word['start']
        else:
            textClip.duration = 1
        textOutlineClip.duration = textClip.duration
        textClipList.append(textClip)
        textOutlineClipList.append(textOutlineClip)

subtitleClip = concatenate_videoclips(textClipList)
subtitleClip = subtitleClip.with_position('center','center')
subtitleOutlineClip = concatenate_videoclips(textOutlineClipList)
subtitleOutlineClip = subtitleOutlineClip.with_position('center','center')

subtitleClip = CompositeVideoClip([subtitleOutlineClip, subtitleClip])
subtitleClip = subtitleClip.with_position("center", "center")
print("Adding subtitles... DONE")

# Stich video together and output
print("Compiling video...")
videoWidth, videoHeight = video.size

titleImgClip = ImageClip("output/resultTitleImg.png", duration=transcription['segments'][1]['words'][0]['start'])
titleWidth, titleHeight = titleImgClip.size
scale = videoHeight/640

titleImgClip = titleImgClip.resized([titleWidth*scale*0.3, titleWidth*scale*0.3*0.4])
titleImgClip  = titleImgClip.with_position("center", "center")
video = CompositeVideoClip([video, subtitleClip, titleImgClip], use_bgclip=True)
audio = CompositeAudioClip([audio])
video.audio = audio
video = video.cropped(videoWidth/2-videoHeight*(9/16)/2, 0, width=videoHeight*(9/16))
video = video.with_effects([vfx.MultiplySpeed(factor=1.25)])
if(video.duration > 90):
    video = video.with_effects([vfx.MultiplySpeed(final_duration=90)])
if(video.duration < 61):
    video =  video.with_effects([vfx.MultiplySpeed(final_duration=61)])
video.write_videofile(f"output/{subreddit_name}/result-{submission.id}.mp4", fps=24, preset="ultrafast")
with open(f"output/{subreddit_name}/result-{submission.id}.txt", "x", encoding="utf-8") as f:
  f.write(f"Title:{videoTitle}\nDescription:{videoDescription}")
print("Compiling video... DONE")