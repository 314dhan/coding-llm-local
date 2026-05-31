import os
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from PyQt6.QtCore import QThread, pyqtSignal

SAMPLE_RATE = 16000
_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
_LANG_ENV = os.getenv("WHISPER_LANGUAGE", "auto")

_model_cache: dict[str, WhisperModel] = {}


def _load_model(size: str) -> WhisperModel:
    if size not in _model_cache:
        _model_cache[size] = WhisperModel(size, device="cpu", compute_type="int8")
    return _model_cache[size]


class VoiceWorker(QThread):
    """Records mic audio then transcribes via local Whisper model.

    Signals:
        state_changed(str): "loading" | "recording" | "transcribing" | "idle"
        transcription_ready(str): transcribed text
        error_occurred(str): error message
    """

    state_changed = pyqtSignal(str)
    transcription_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._active = False
        self._language: str | None = None if _LANG_ENV == "auto" else _LANG_ENV

    def start_recording(self) -> None:
        if self.isRunning():
            return
        self._active = True
        self.start()

    def stop_recording(self) -> None:
        self._active = False

    def run(self) -> None:
        try:
            self.state_changed.emit("loading")
            model = _load_model(_MODEL_SIZE)

            frames: list = []
            self.state_changed.emit("recording")

            def _cb(indata, n_frames, time_info, status):
                if self._active:
                    frames.append(indata.copy())

            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                callback=_cb,
            ):
                while self._active:
                    self.msleep(50)

            self.state_changed.emit("transcribing")
            if frames:
                audio = np.concatenate(frames, axis=0).flatten()
                segments, _ = model.transcribe(
                    audio,
                    beam_size=5,
                    language=self._language,
                )
                text = " ".join(seg.text for seg in segments).strip()
                if text:
                    self.transcription_ready.emit(text)

            self.state_changed.emit("idle")
        except Exception as exc:
            self.error_occurred.emit(str(exc))
            self.state_changed.emit("idle")
