import os
import json
import string

from pydub import AudioSegment
from PIL import Image
import shutil


class Info:
    def __init__(self, song, composer, creator, bpm, duration, song_file, pic_name, diff_list):
        self._version = "1"
        self._songName = song
        self._songSubName = ""
        self._songAuthorName = composer
        self._levelAuthorName = creator
        self._explicit = "false"
        self._beatsPerMinute = bpm
        self._shuffle = 0
        self._shufflePeriod = 0.5
        self._previewStartTime = 0
        self._previewDuration = 0
        self._songApproximativeDuration = duration
        self._songFilename = song_file
        self._coverImageFilename = pic_name
        self._environmentName = "Midgard"
        self._songTimeOffset = 0
        self._customData = CustomData().__dict__
        self._difficultyBeatmapSets = [{"_beatmapCharacteristicName": "Standard",
                                        "_difficultyBeatmaps": diff_list}]


class CustomData:
    def __init__(self):
        self._contributors = []
        self._editors = {"Edda": {"version": "1.0.3"}, "_lastEditedBy": "Edda"}


class DiffMaps:
    def __init__(self, diff, rank, file):
        self._difficulty = diff
        self._difficultyRank = rank
        self._beatmapFilename = file
        self._noteJumpMovementSpeed = 30.0
        self._noteJumpStartBeatOffset = 0
        self._customData = {"_editorOffset": 0,
                            "_editorOldOffset": 0,
                            "_editorGridSpacing": 2.0,
                            "_editorGridDivision": 4,
                            "_warnings": [],
                            "_information": [],
                            "_suggestions": [],
                            "_requirements": []}


class Note:
    def __init__(self, time, position):
        self._time = time
        self._lineIndex = position
        self._lineLayer = 1
        self._type = 0
        self._cutDirection = 1


class BpmChange:
    def __init__(self, bpm, time, bpb, met):
        self._BPM = bpm
        self._time = time
        self._beatsPerBar = bpb
        self._metronomeOffset = met


ranks = ["Easy", "Normal", "Hard"]  # don't change this
rank_levels = [1, 4, 7]


def convert(dir):
    files = os.listdir(dir)

    list_music_file = []
    list_pic_file = []
    list_osu_file = []
    for file in files:
        if ".osu" in file:
            list_osu_file.append(dir + "\\" + file)
        elif ".mp3" in file or ".ogg" in file:
            list_music_file.append(dir + "\\" + file)
        elif ".jpg" in file or "jpeg" in file or ".png" in file:
            list_pic_file.append(dir + "\\" + file)

    dict_music_file = {}
    dict_pic_file = {}
    dict_osu_file = {}

    for file in list_music_file:
        size = os.path.getsize(file)
        dict_music_file[file] = size

    for file in list_pic_file:
        size = os.path.getsize(file)
        dict_pic_file[file] = size

    for file in list_osu_file:
        size = os.path.getsize(file)
        dict_osu_file[file] = size

    osu_file = sorted(dict_osu_file.items(), key=lambda x: x[1])
    music_file = sorted(dict_music_file.items(), key=lambda x: x[1], reverse=True)[0][0]
    pic_file = sorted(dict_pic_file.items(), key=lambda x: x[1], reverse=True)[0][0]

    song_meta = []

    if len(osu_file) < 3:
        for i in range(len(osu_file)):
            song_meta.append(osu_file_convert(osu_file[i][0], ranks[i]))
    else:
        for i in range(3):
            song_meta.append(osu_file_convert(osu_file[i][0], ranks[i]))

    save_dir = song_meta[0][4]
    duration = 0
    if music_file.split(".")[-1] != "ogg":
        song = AudioSegment.from_mp3(music_file)
        duration = round(song.duration_seconds)
        song.export("outputs\\" + save_dir + r"\song.ogg")
    else:
        shutil.copy(music_file, "outputs\\" + save_dir)
        music_file_single = music_file.split("\\")[-1]
        os.rename("outputs\\" + save_dir + "\\" + music_file_single,
                  "outputs\\" + save_dir + "\\" + "song.ogg")

    if pic_file.split(".")[-1] != "jpg":
        image = Image.open(pic_file)
        image = image.convert('RGB')
        image.save("outputs\\" + save_dir + r"\image.jpg", quality=95)
    else:
        shutil.copy(pic_file, "outputs\\" + save_dir)
        pic_file_single = pic_file.split("\\")[-1]
        os.rename("outputs\\" + save_dir + "\\" + pic_file_single,
                  "outputs\\" + save_dir + "\\" + "image.jpg")

    diff_lists = []
    for i in range(len(song_meta)):
        diff_lists.append(DiffMaps(ranks[i], rank_levels[i], ranks[i]+".dat").__dict__)

    info = Info(song_meta[0][0], song_meta[0][1], song_meta[0][5], song_meta[0][3], duration, "song.ogg",
                "image.jpg", diff_lists)
    info_content = info.__dict__

    save = open("outputs\\" + save_dir + r"\info.dat", mode="w")
    s = json.dumps(info_content, sort_keys=False, indent=4, separators=(',', ': '))
    save.write(s)
    save.close()


def osu_file_convert(input, diffname):
    notes = []
    bgm_changers = []
    global_bpm = 0
    offset = 0

    f = open(input, mode="r", encoding="UTF-8")

    readnotes = False
    readbpm = False
    for line in f.readlines():
        if "[TimingPoints]" in line:
            readbpm = True
            continue

        if "[HitObjects]" in line:
            readnotes = True
            readbpm = False
            continue

        if "Title:" in line:
            title = line.split(":")[1].replace("\n", "")
        if "Artist:" in line:
            composer = line.split(":")[1].replace("\n", "")
        if "Creator:" in line:
            creator = line.split(":")[1].replace("\n", "")

        if readbpm:
            elements = line.split(",")
            if len(elements) > 1:
                if float(elements[1]) > 0:
                    if global_bpm == 0:
                        global_bpm = 60000 / float(elements[1])
                    bpm = 60000 / float(elements[1])

                    timing = (global_bpm / 60) * (float(elements[0]) / 1000)
                    bgm_changers.append(BpmChange(bpm, timing, 2, 2))
                else:
                    continue

        if readnotes:
            elements = line.split(",")
            # print(elements)
            timing = (global_bpm / 60) * (float(elements[2]) / 1000)
            if elements[0] == "64":
                notes.append(Note(timing, 0).__dict__)
            elif elements[0] == "192":
                notes.append(Note(timing, 1).__dict__)
            elif elements[0] == "320":
                notes.append(Note(timing, 2).__dict__)
            elif elements[0] == "448":
                notes.append(Note(timing, 3).__dict__)

    note_file = {"_version": "1",
                 "_customData": {
                     "_time": 0,
                     "_BPMChanges": [BpmChange(global_bpm, (global_bpm / 60) * (offset / 1000), 2, 2).__dict__],
                     "_bookmarks": []
                 },
                 "_events": [],
                 "_notes": notes,
                 "_obstacles": []}

    f.close()

    save_dir = composer.lower().capitalize() + title.lower().capitalize()
    punctuation_string = string.punctuation
    punctuation_string += " "
    for i in punctuation_string:
        save_dir = save_dir.replace(i, "")

    if not os.path.exists(fr"outputs\{save_dir}"):
        os.mkdir(fr"outputs\{save_dir}")

    save = open(fr"outputs\{save_dir}\{diffname}.dat", mode="w")
    s = json.dumps(note_file, sort_keys=False, indent=4, separators=(',', ': '))
    save.write(s)
    save.close()
    return [title, composer, diffname + ".dat", global_bpm, save_dir, creator]


if __name__ == '__main__':
    convert(r"E:\osu!\Songs\1793916 Leo_need x Hatsune Miku - HIBANA -Reloaded-")

