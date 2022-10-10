import subprocess
import json
import sys
from os import walk, remove
import os
 
##stolen from the net
def search(list, platform):
    for i in range(len(list)):
        if list[i] == platform:
            return True
    return False
 
#first we load the settings
with open("c:\\script"+"\\"+"settings.json",  "r") as read_it:
     settings = json.load(read_it)
 
#the path to our executable
mkvMerge = settings["pathToMKVToolNix"] + "\\" + "mkvmerge.exe"
mkvExtract = settings["pathToMKVToolNix"] + "\\" + "mkvextract.exe"
ffmpeg = settings["pathToFFMPEG"] + "\\" + "ffmpeg.exe"
inputPath = settings["input"]
mkv = ".mkv"
filesWithErrors = []
 
#we get the mkv filenames for the directory
filteredFileNames = []
fileList = []
for path, subdirs, files in os.walk(inputPath):
    for name in files:
        fileList.append(os.path.join(path, name))
 
print(fileList)
 
for loopFileName in fileList:
    if mkv in loopFileName:
        filteredFileNames.append(loopFileName)
 
if len(filteredFileNames) == 0:
    print("There are no files to be processed in " + inputPath)
 
#here we start the filename looping
#we need to assign parameter the full path we got from settings and the filename we have
for loop in filteredFileNames:
    exploded = loop.split("\\")
    #print(exploded)
    fileNameWithExtension=exploded[-1]
    print("fileNameWithExtension: " + fileNameWithExtension)
    path = loop.replace("\\"+fileNameWithExtension, "")
    print("path: " + path)
    #parameter = "d:\downloads\[Tinosoft] Spy X Family - 11 [1080p x265 HEVC].mkv"
    parameter = path + "\\" + fileNameWithExtension
 
    #we're just getting the filename, withouth extension
    #y = fileNameWithExtension.split(".")
    fileName = fileNameWithExtension.replace(mkv,"")
    print("filename: " + fileName)
 
   
 
    #we execute the program and capture all the output
    return_code = subprocess.run([mkvMerge,  "-J", parameter],  stdout=subprocess.PIPE)
    if return_code.returncode != 0:
        print("there was a problem reading the subtitle values, exiting ")
        print(return_code.stdout)
        print(return_code.stderr)
        print(return_code.returncode)
        filesWithErrors.append("Problem reading subtitles: " + fileName)
        continue
        #sys.exit()
   
    print("parameter: " + parameter)
    #sys.exit()
 
    #we print convert it to a json
    jsonValue = json.loads(return_code.stdout)
 
    # Filter python objects with list comprehensions
    jsonTracks = jsonValue["tracks"]
    jsonValueOut = [x for x in jsonTracks if x['type'] == 'subtitles']
   
    #then we need to start making the values of the extract
    #it seems that getting the smalles order was totally useless
    # more on that after the break
    parameters = [] #we're using a set instead
    langList = []
    subtitleFormat = ""
    currentLanguage = ""
    for info in jsonValueOut:
        currentLanguage = info["properties"]["language"]
        if info["codec"]=="SubStationAlpha":
            subtitleFormat = "ssa"
        elif info["codec"]=="HDMV PGS":
            subtitleFormat = "pgs"
        elif info["codec"]=="SubRip/SRT":
            subtitleFormat = "srt"
        elif info["codec"] == "VobSub":
            subtitleFormat = "sub"
        else:
            print("non recognized subitltes found, printing the subtitle codec and filename")
            print(parameter)
            print("subtitle codec: " + info["codec"])
            sys.exit()
 
        if not search(langList, currentLanguage):
            #let's assume that if it's undefined, it's in english
            subLanguage = ""
            if info["properties"]["language"] == "und":
                subLanguage = "eng"
            else:
                subLanguage = info["properties"]["language"]
            parameters.append(str(info["id"]) + ":" + path + "\\" + fileName + "." +subLanguage+  "."+ subtitleFormat)
            langList.append(currentLanguage)
 
    #convert into a single line
    sub_params = " ".join(map(str,  parameters))
    #print(sub_params)
    #sys.exit()
    print(len(parameters))
    #now that we have everything  we jsut have to run the code
    #extract_program = subprocess.run([mkvExtract,"tracks", parameter, sub_params], stdout=subprocess.PIPE)
    #we need to check if the parameters are 0, so there would be no subtitles to extract
    if len(parameters)>0:
        extract_program = subprocess.run([mkvExtract,"tracks", parameter] + parameters, stdout=subprocess.PIPE)
        if extract_program.returncode != 0:
            print("there was a problem generating the subtitle files: ")
            print(extract_program.stdout)
            print(extract_program.stderr)
            print(extract_program.returncode)
            filesWithErrors.append("Problem generating the subtitle files: " + fileName)
            continue
            #sys.exit()
    else:
        print("file " + fileName + " has no subtitles to extract.")
 
    #now that the subs are done, we need to extract the video, so, here we go!
    #and for this we will use ffmpeg and the following params
    #    "-f mp4 -c:v copy -c:a copy -sn"
    ffmpegParams = "-f mp4 -c:v copy -c:a copy -sn"
    print(ffmpegParams)
    outputMp4 =  path + "\\" + fileName + "." + "mp4"
    print(outputMp4)
 
    generateMp4 = subprocess.run([ffmpeg,"-y" , "-i", parameter, "-f", "mp4", "-c:v", "copy", "-c:a", "copy", "-sn" ,outputMp4] , stdout=subprocess.PIPE)
    if generateMp4.returncode != 0:
        print("there was a problem generating the mp4 file: ")
        print(generateMp4.stdout)
        print(generateMp4.stderr)
        print(generateMp4.returncode)
        filesWithErrors.append("Problem generating the mp4: " + fileName)
        continue
        #sys.exit()
 
    #and because everything was successful, we delete the original file
    remove(parameter)
 
print("")
print("")
print("there were " + str(len(filesWithErrors)) + " files with errors.")
for a in filesWithErrors:
    print(a)
 
 
