import os
import sys
import re
from fontTools import ttLib
from guessit import guessit

reponse_positive = ["oui", "yep", "ui", "yes", "y"]
reponse_negative = ["non", "no", "nop", "na", "iee"]
SUBLANGUAGE = "fre"
SUBDEFAULT = "yes"


class Mux:
    def __init__(self):
        self.files = os.listdir()
        self.font = False

    def get_mkv_list(self):
        self.mkv_list = []
        for file in self.files:
            if (
                file[(len(file) - 4) :].lower() == ".mkv"
                or file[(len(file) - 4) :].lower() == ".mp4"
            ):
                item = self.guess(file)
                self.mkv_list.append(item)

        print(f"•{len(self.mkv_list)} raw found•")

    def get_font_list(self):
        self.font_list = []
        for file in self.files:
            if (
                file[(len(file) - 4) :].lower() == ".ttf"
                or (file[(len(file) - 4) :]).lower() == ".otf"
                or (file[(len(file) - 4) :]).lower() == ".ttc"
            ):
                # Check real name
                try:
                    for font in ttLib.TTFont(file)["name"].names:
                        if font.nameID != 1:
                            continue
                        if font.platformID != 1:
                            continue
                        # if name/platform ID == 1 it's the real name
                        font = font.string.decode()
                        break
                except:
                    font = " "
                # font = ttLib.TTFont(file)['name'].names[]
                self.font_list.append({"name": font, "file": file})
                self.font = True
        print(f"•{len(self.font_list)} font found•")

    def sub_font_parser(self, sub_file):
        # If the font exist, let's associate them to sub
        valid_font = []
        command_font = ""
        if self.font == True:
            sub = open(sub_file, "r").read()
            for font in self.font_list:
                # Simple check
                try:
                    if font["name"].lower() in re.findall(
                        r"style:.*?,(.*?),", sub.lower()
                    ):
                        valid_font.append(
                            {
                                "name": font["name"],
                                "file": font["file"],
                            }
                        )
                        command_font = (
                            command_font
                            + f'--attach-file "{font["file"]}" '
                        )
                except:
                    valid_font.append(
                        {"name": font["name"], "file": font["file"]}
                    )
                    command_font = (
                        command_font
                        + f'--attach-file "{font["file"]}" '
                    )
            return valid_font, command_font
        return valid_font, command_font

    def get_sub_list(self):
        self.sub_list = []
        for file in self.files:
            if (
                file[(len(file) - 4) :].lower() == ".ass"
                or (file[(len(file) - 4) :]).lower() == ".srt"
            ):
                # Check if font needed for this sub
                font, command_font = self.sub_font_parser(file)
                # Check episode of sub
                item = self.guess(file)
                self.sub_list.append(
                    {
                        "file": file,
                        "font": font,
                        "episode": item["episode"],
                        "ext": item["ext"],
                        "command_font": command_font,
                    }
                )
                print(f"{len(font)} font found for {file} subtitle")
        print(f"•{len(self.sub_list)} subtitle found•")

    def info_user(self):
        while True:
            print("[Tag] Show name S01E01 [Release info].mkv")
            print("Tag of release ? (without [])")
            self.tag = input()
            print("Show name ? (One Piece, Toradora...)")
            self.name = input()
            while True:
                try:
                    print("Season number ? (00, 01, 02...)")
                    self.season = input()
                    int(self.season)
                    break
                except:
                    print("Must be number... (00, 01, 02...)")
            print(
                "Release info ? (VOSTFR BD x264 1080p FLAC, VOSTFR BD x264 720p FLAC...)"
            )
            self.info = input()
            print("Source of sub ? (Crunchyroll, netflix...)")
            self.source_sub = input()
            print("• The name file example below is correct ? •")
            print(
                f"[{self.tag}] {self.name} S{self.season}E01 [{self.info}].mkv"
            )
            self.good = input()
            if self.good.lower() in reponse_positive:
                break
            print("Try again...")

    def guess(self, item):
        # Use Guessit for getting infos
        guess = guessit(item)
        ext = item[(len(item) - 4) :].lower()
        item = {"episode": guess["episode"], "file": item, "ext": ext}
        return item

    def check_combo(self):
        for raw in self.mkv_list:
            for sub in self.sub_list:
                if raw["episode"] == sub["episode"]:
                    print(
                        "\n",
                        raw["file"],
                        "Raw\n will be mux with\n",
                        sub["file"],
                        f"Subtitle ({len(sub['font'])} font)",
                    )
        print("\n")
        print(
            "Perfect, now confirm me if the parse above is correct (Y/N) (!!!please check it, don't be monkey!!!)"
        )
        perfect = input()
        if perfect.lower() in reponse_positive:
            return
        else:
            print(
                "Please try to renames your files (01.mkv, 01.ass...) for better result, press enter for exit"
            )
            input()
            sys.exit()

    def mkvmerge_command(self):
        self.command_list = []
        for raw in self.mkv_list:
            command = 'mkvmerge -o "Output Muxing/'
            for sub in self.sub_list:
                if raw["episode"] == sub["episode"]:
                    # If it's True, let's make the command
                    # Name of file
                    name_file = (
                        f"[{self.tag}] {self.name} "
                        f"S{self.season.zfill(2)}E{str(raw['episode']).zfill(2)} "
                        f"[{self.info}].mkv"
                    )
                    command = command + f'{name_file}" '
                    # Raw file
                    command = command + f'"{raw["file"]}" '
                    # Language / track name (source) / default track
                    command = (
                        command
                        + f"--language 0:{SUBLANGUAGE} "
                        + f'--track-name 0:"{self.source_sub}" '
                        + f"--default-track 0:{SUBDEFAULT} "
                    )
                    # Subtitle
                    command = command + f'"{sub["file"]}" '

                    # Add font to the command
                    command = command + sub["command_font"]

                    # Title of video
                    command = (
                        command + f'--title "[{self.tag}] {self.name}"'
                    )

                    self.command_list.append(
                        {
                            "raw": raw["file"],
                            "sub": sub["file"],
                            "font_number": len(sub["font"]),
                            "command": command,
                            "name_file": name_file,
                        }
                    )

    def mkvmerge_merge(self):
        print("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬")
        for command in self.command_list:
            print(
                "Start mux of \n"
                f"{command['raw']} Raw with\n"
                f"{command['sub']} Subtitle \nOutput :\n"
                + command["name_file"]
            )
            os.system(command["command"])
            print("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬")


if __name__ == "__main__":
    mux = Mux()
    print("••••••••••••••••••••••••••")
    print("Contact Taiga#9999 for any problem")
    print("••••••••••••••••••••••••••")
    print("Search raws")
    mux.get_mkv_list()
    print("Search font...")
    mux.get_font_list()
    print("Search sub...")
    mux.get_sub_list()
    print("Give me some info now please")
    mux.info_user()
    mux.check_combo()
    mux.mkvmerge_command()
    print(
        f"Press enter for start the mux of {len(mux.command_list)} item"
    )
    input()
    mux.mkvmerge_merge()
    print("Mux end press enter for closing script")
    input()
