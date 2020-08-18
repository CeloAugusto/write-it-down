from wave import open as wav_open
from pulsectl import Pulse
from subprocess import Popen
from signal import SIGINT
from os import remove, listdir

AUDIOS_PATH = "./audios"


def default_config():
    with Pulse("default") as pulse:
        # Muda o volume da saida
        built_output = pulse.sink_list()[0]
        pulse.volume_set_all_chans(built_output, 0.5)

        # Muda o volume da entrada Monitor
        monitor_input = pulse.source_list()[0]
        pulse.volume_set_all_chans(monitor_input, 1)

        # Muda o volume da entrada
        built_input = pulse.source_list()[1]
        pulse.volume_set_all_chans(built_input, 0.35)

        # Muda a entrada e saida primaria
        pulse.default_set(built_output)
        pulse.default_set(built_input)

        # # Muda o volume de entrada e saida do WEBRTC (Discord)
        # play_sink = [x for x in pulse.sink_input_list() if x.name == "playStream"][0]
        # rec_source = [x for x in pulse.source_output_list() if x.name == "recStream"][0]
        # pulse.sink_input_volume_set(play_sink, 1)
        # pulse.volume_set_all_chans(rec_source, 1)


def list_audios():
    for a in sorted(listdir(AUDIOS_PATH)):
        print(a[:-4])


def rec_in_wav(audio_name):
    # with Pulse("rec-pulse") as pulse:
    # call_rep = [x for x in pulse.sink_input_list() if x.name == "playStream"][0]
    temp_file = "%s/temp.wav" % AUDIOS_PATH
    audio_file = "%s/%s.wav" % (AUDIOS_PATH, audio_name)
    try:
        rec_process = Popen(
            "parec " +
            "--device=alsa_output.pci-0000_00_1f.3.analog-stereo.monitor " +
            "--file-format=wav %s" % temp_file,
            shell=True,
        )
        print("Press CTRL+C to stop recording")
        rec_process.communicate()
    except KeyboardInterrupt:
        rec_process.send_signal(SIGINT)

    open(audio_file, "a").close()
    with wav_open(temp_file, "r") as r, wav_open(audio_file, "w") as w:
        w.setnchannels(r.getnchannels())
        w.setsampwidth(r.getsampwidth())
        w.setframerate(r.getframerate())
        for i in range(r.getnframes()):
            frame = r.readframes(1)
            for j in range(len(frame)):
                if frame[j] > 0:
                    w.writeframes(frame)
                    break
    remove(temp_file)


def play_in_sink(audio_name):
    with Pulse("play-pulse") as pulse:
        new_sink_id = pulse.module_load(
            "module-null-sink",
            "sink_name=WriteItDown " +
            "sink_properties=device.description=WriteItDown",
        )
        new_loopback_id = pulse.module_load(
            "module-loopback",
            "source=WriteItDown.monitor " +
            "sink=alsa_output.pci-0000_00_1f.3.analog-stereo",
        )

        new_sink = [x for x in pulse.sink_list() if x.name == "WriteItDown"][0]
        new_source = [
            x for x in pulse.source_list() if x.name == "WriteItDown.monitor"
        ][0]
        rec_source = [x for x in pulse.source_output_list() if x.name == "recStream"][0]

        pulse.volume_set_all_chans(new_sink, 1)
        pulse.volume_set_all_chans(new_source, 1)
        pulse.source_output_move(rec_source.index, new_source.index)

        try:
            play_process = Popen(
                "paplay --device=WriteItDown %s/%s.wav" % (AUDIOS_PATH, audio_name),
                shell=True
            )
            print("Press CTRL+C to stop playing")
            play_process.communicate()
        except KeyboardInterrupt:
            play_process.send_signal(SIGINT)

        pulse.module_unload(new_loopback_id)
        pulse.module_unload(new_sink_id)


if __name__ == "__main__":
    from sys import argv

    if len(argv) < 2:
        default_config()
    elif argv[1] == "play":
        play_in_sink(argv[2])
    elif argv[1] == "rec":
        rec_in_wav(argv[2])
    elif argv[1] == "-l":
        list_audios()
