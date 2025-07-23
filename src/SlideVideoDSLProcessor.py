from openai import OpenAI
import cv2
import hashlib
import os
from pydub import AudioSegment
import uuid
from dslProcessor import DSLProcessor, BasicDSLProcessor
from programs import ProgramOutput, ProgramDirectory
from typing import List, Any
import os
import time
import shutil
from dotenv import dotenv_values
class SlideVideoDSLProcessor(BasicDSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__(programDirectory)
        self.programDirectory = programDirectory
    
    def getVisualReturnTypes(self) -> List[str]:
        return ["mp4"]
    
    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str,config:dict) -> ProgramOutput:
        if preferredVisualReturnType not in self.getVisualReturnTypes():
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")
        result = super().process(code, input, outputNames, "md",config)
        if not result.succeeded():
            return dict(error="ERROR: program failed with message: " + result.errorMessage(),
                        succeeded=False)
        else:
            code =str(result.viz())
            
        model = "gpt-4o-mini-tts"
        if "model" in config:
            model = config["model"]
        instructions = "Speak in a cheerful and positive tone."
        if "instructions" in config:
            instructions = config["instructions"]
        voice = "coral"
        if "voice" in config:
            voice = config["voice"]

        print(f"model: {model}, instructions: {instructions}, voice: {voice}")
 
        client = None
        # if .env exists, load it
        if os.path.exists(".env"):
            env = dotenv_values(".env")
            client = OpenAI(api_key=env["OPENAI_API_KEY"])
        else:
            client = OpenAI()

        speech_cache = ".speech_cache"
        # create a speech_cache folder if it doesn't exist
        if not os.path.exists(speech_cache):
            os.makedirs(speech_cache)

        # create a random id for the temp directory
        tempdir = str(uuid.uuid4())
        # if the tempdir doesn't exist, create it
        if not os.path.exists(tempdir):
            os.makedirs(tempdir)

        prepend = "---\nmarp: true\ntheme: custom-default\n---\n"

        # save the code to a temporary file
        filename = f"{tempdir}/slides.itom"
        with open(filename, "w") as file:
            file.write(prepend + code)

        # run the marp command to crate the images
        os.system(f"marp --images png {filename} -o {tempdir}/temp");
        os.system(f"marp --notes {filename} -o {tempdir}/notes.md");

        slides = []
        # read the file
        with open(f"{tempdir}/notes.md", 'r') as file:
            # read each chunk (seperated by ---) and add to slides
            for chunk in file.read().split('---'):
                slides.append(chunk)

        images = []
        # look in the temp folder for all files that start with temp, sort lexicographically
        for file in sorted(os.listdir(f"{tempdir}")):
            if file.startswith("temp"):
                # if the file doesn't end with png, rename it to png
                if not file.endswith(".png"):
                    os.rename(f"{tempdir}/{file}", f"{tempdir}/{file}.png")
                    images.append(f"{tempdir}/{file}.png")
                else:
                    images.append(f"{tempdir}/{file}")

        speech_files = []
        for c in slides:
            # calculate the md5 of the string

            md5 = hashlib.md5(c.encode()).hexdigest()
            if (c.strip() != ""):
                tempc = c + instructions + voice + model
                md5 = hashlib.md5(tempc.encode()).hexdigest()
            speech_file_path = f"{speech_cache}/speech_{md5}.mp3"
            speech_files.append(speech_file_path)
            if (os.path.exists(speech_file_path)):
                continue
            # if c is empty (no text), create an mp3 file with 2 seconds of silence
            if (c.strip() == ""):
                print(f"Creating silent audio for {speech_file_path}")
                audio = AudioSegment.silent(duration=2000)
                audio.export(speech_file_path, format="mp3")
                continue
            with client.audio.speech.with_streaming_response.create(
                model=model,
                voice=voice,
                input=c,
                instructions=instructions,
            ) as response:
                response.stream_to_file(speech_file_path)


        files_and_duration = []

        # for each speech file, read the file and get the duration
        index = 0
        for speech_file in speech_files:
            audio = AudioSegment.from_mp3(speech_file)

            # determine length in milliseconds
            duration = len(audio)
            orig_duration = (duration / 1000)

            # round up duration to nearest second
            duration = int(duration / 1000) + 1

            print(f"{speech_file} duration: {duration}")
            
            # add the duration to the files_and_duration list
            files_and_duration.append((images[index], duration))
            
            # padding in milliseconds
            padding = (duration - orig_duration)
            print(f"Duration we want: {duration}, Duration we got: {orig_duration}, Padding: {padding}")
            
            padding_duration = padding * 1000
            audio += AudioSegment.silent(duration=padding_duration)
            # grab just the filename, ignore directory
            filename = os.path.basename(speech_file)
            audio.export(f"{tempdir}/padded_"+filename, format="mp3")
            speech_files[index] = f"{tempdir}/padded_"+filename
            index += 1

        # concatenate the audio files into a single file
        audio = AudioSegment.empty()
        for speech_file in speech_files:
            audio += AudioSegment.from_mp3(speech_file)
        audio.export(f"{tempdir}/output.mp3", format="mp3")

        # Each video has a frame per second which is number of frames in every second
        frame_per_second = 15

        w, h = None, None
        for file, duration in files_and_duration:
            frame = cv2.imread(file)

            if w is None:
                # Setting up the video writer
                h, w, _ = frame.shape
                fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
                writer = cv2.VideoWriter(f"{tempdir}/output.mp4", fourcc, frame_per_second, (w, h))

            # Repating the frame to fill the duration
            for repeat in range(duration * frame_per_second):
                writer.write(frame)

        writer.release()

        # combine the audio and video, overwrite the output file if it exists
        if (os.path.exists(f"{tempdir}/combined.mp4")):
            os.remove(f"{tempdir}/combined.mp4")
        os.system(f"ffmpeg -i {tempdir}/output.mp4 -i {tempdir}/output.mp3 -c:v copy -c:a aac -strict experimental {tempdir}/combined.mp4")

        outputData = {}

        # read the combined.mp4 file into a bytes object
        with open(f"{tempdir}/combined.mp4", "rb") as file:
            mp4_bytes = file.read()

        # remove the tempdir
        shutil.rmtree(tempdir)

        if preferredVisualReturnType == "mp4":
            return ProgramOutput(time.time(), "mp4", mp4_bytes, outputData)
        else:
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")
        




