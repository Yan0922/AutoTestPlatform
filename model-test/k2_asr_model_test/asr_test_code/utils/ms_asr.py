# pip install azure-cognitiveservices-speech
# pip install pydub
# pip install miniaudio
# python3 ms_asr.py --lang zh-CN --listFile src/audio.list --srcFile result/zh.src --resFile result/zh.rst

import argparse
import os
import threading
import time
import wave

import azure.cognitiveservices.speech as speechsdk
import miniaudio


def _speech_config(language_code):
    subscription = os.environ.get("AZURE_SPEECH_KEY", "").strip()
    if not subscription:
        raise RuntimeError(
            "未设置 AZURE_SPEECH_KEY 环境变量，请在本地 export 后再运行 ms_asr.py"
        )

    region = os.environ.get("AZURE_SPEECH_REGION", "southeastasia").strip()
    endpoint_id = os.environ.get("AZURE_SPEECH_ENDPOINT_ID", "").strip()

    speech_config = speechsdk.SpeechConfig(subscription=subscription, region=region)
    speech_config.speech_recognition_language = language_code

    if endpoint_id:
        speechsdk.languageconfig.SourceLanguageConfig(language_code, endpoint_id)
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_EndpointId,
            endpoint_id,
        )

    return speech_config


def check_file(file_path):
    if not os.path.exists(file_path):
        print(f"File does not exist {file_path}")
        return 0

    if os.path.getsize(file_path) == 0:
        print("File is empty")
        return 0

    if file_path.lower().endswith(".wav"):
        return 1
    if file_path.lower().endswith(".mp3"):
        return 2
    if file_path.lower().endswith(".pcm"):
        return 3

    print("Unsupported file format")
    return 0


def save_pcm_as_wav(pcm_data, sample_rate, bit_depth, channels, output_file):
    with wave.open(output_file, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(bit_depth // 8)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)


def push_stream_writer(stream, weatherfilename):
    try:
        chunk_size = 640 * 2
        if check_file(weatherfilename) == 2:
            decoded_sound_file = miniaudio.mp3_read_file_s16(weatherfilename)
            pcm_data = decoded_sound_file.samples

            base_name = os.path.basename(weatherfilename)
            tmpfile = os.path.join("/tmp/", os.path.splitext(base_name)[0] + ".wav")
            save_pcm_as_wav(pcm_data, 16000, 16, 1, tmpfile)

            wav_fh = wave.open(tmpfile, "rb")
            while True:
                frames = wav_fh.readframes(chunk_size // 2)
                if not frames:
                    break
                stream.write(frames)
            wav_fh.close()
            try:
                os.remove(tmpfile)
            except OSError as exc:
                print(f"{exc}")

        elif check_file(weatherfilename) == 3:
            with open(weatherfilename, "rb") as pcm_file:
                while True:
                    frames = pcm_file.read(chunk_size)
                    if not frames:
                        break
                    stream.write(frames)
        else:
            total_size = 0
            wav_fh = wave.open(weatherfilename, "rb")
            while True:
                frames = wav_fh.readframes(chunk_size // 2)
                if not frames:
                    break
                total_size += len(frames)
                stream.write(frames)
                time.sleep(0.02)
            print(f"Total frames size: {total_size} bytes")
            wav_fh.close()
    finally:
        stream.close()


def from_stream(speech_config, file_path, language):
    try:
        myresult = []
        stream_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=16000,
            bits_per_sample=16,
            channels=1,
        )
        stream = speechsdk.audio.PushAudioInputStream(stream_format)
        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            language=language,
            audio_config=audio_config,
        )
        speech_recognizer.session_started.connect(
            lambda evt: print(f"SESSION ID: {evt.session_id}")
        )

        def recognized_cb(evt: speechsdk.SpeechRecognitionEventArgs):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                print(f"RECOGNIZED: {evt.result.text}")
                myresult.append(evt.result.text)
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                print(f"NOMATCH: {evt}")

        speech_recognizer.recognized.connect(recognized_cb)

        push_stream_writer_thread = threading.Thread(
            target=push_stream_writer,
            args=[stream, file_path],
        )
        push_stream_writer_thread.start()

        speech_recognizer.start_continuous_recognition_async().get()
        push_stream_writer_thread.join()

        print(f"return result: {myresult}")
        return " ".join(myresult)
    except FileNotFoundError:
        print(f"Error: File not found {file_path}")
        return None


def main(language_code, listFile, srcFile, resFile):
    speech_config = _speech_config(language_code)

    with open(listFile, "r", encoding="utf-8") as file, open(
        resFile, "a", encoding="utf-8"
    ) as frst:
        for line in file:
            try:
                if len(line.strip()) <= 2:
                    continue

                parts = line.strip().split(" ", 1)
                file_name = parts[0]
                wav_file_path = file_name.strip()
                if check_file(wav_file_path) == 0:
                    continue

                result = from_stream(speech_config, wav_file_path, language_code)
                if result:
                    output_line = wav_file_path + " " + result + "\n"
                    frst.write(output_line)
                    frst.flush()
                else:
                    print(f"{wav_file_path} No transcription results.")
            except FileNotFoundError:
                print(f"Error: File not found {wav_file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process audio files for speech recognition")
    parser.add_argument("--lang", type=str, default="es-ES", help="language code for audio")
    parser.add_argument(
        "--listFile",
        type=str,
        default=r"/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/outside_dataset/es_wav/es.txt",
        help="list for src list file",
    )
    parser.add_argument("--srcFile", type=str, default=None, help="list for src audio file")
    parser.add_argument(
        "--rstFile",
        type=str,
        default=r"/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/0916_ms_outside/es_rst.txt",
        help="list for result file",
    )
    args = parser.parse_args()

    main(args.lang, args.listFile, args.srcFile, args.rstFile)
