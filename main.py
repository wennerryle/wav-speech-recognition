import os
import asyncio
import sys
import wave
import json
import signal

from typing import Any, Dict, List, TypedDict
import websockets
from websockets import ClientConnection

from modules.file_converter import FileConverter
from modules.audio_file_validator import AudioFileValidator


class Alternative(TypedDict):
    confidence: float
    text: str


class SpeechRecognitionWithAlts(TypedDict):
    alternatives: List[Alternative]


class SpeechRecognitionWithPartial(TypedDict):
    partial: str


type SpeechRecognitionResult = SpeechRecognitionWithAlts | SpeechRecognitionWithPartial


def write_to_file(file_path: str, content: str) -> None:
    """Write content to a file in append mode."""
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(content)


class SpeechRecognitionClient:
    """Client for speech recognition via WebSocket."""

    def __init__(self, uri: str, audio_path: str, output_path: str):
        self.uri = uri
        self.audio_path = audio_path
        self.output_path = output_path
        self.buffer_size: int = 3200

    async def _send_config(self, websocket: ClientConnection,
                           sample_rate: int) -> None:
        """Send recognition configuration to the server."""
        config = {  # type: ignore
            "config": {
                "sample_rate": sample_rate,
                "partial_results": True,
                "word_confidence": True,
                "max_alternatives": 3
            }
        }
        await websocket.send(json.dumps(config))

    def _has_meaningful_content(self, result: Dict[str, Any]) -> bool:
        """Check if the result contains meaningful speech content."""
        if "partial" in result and result["partial"] and result["partial"].strip():
            return True

        if "alternatives" in result:
            for alt in result["alternatives"]:
                if "text" in alt and alt["text"].strip():
                    return True
                if "result" in alt and alt["result"]:
                    return True
        return False

    last_partial = ""

    async def _process_server_response(self, response: str):
        """Process server response and write results to output file."""
        result: SpeechRecognitionResult = json.loads(response)

        print(result)

        partial = result.get("partial")

        if self.last_partial != "" and (partial == "" or partial is None):
            write_to_file(self.output_path, self.last_partial + "\n")
            self.last_partial = ""

        if partial is not None:
            self.last_partial = partial

    async def run(self) -> None:
        """Run the speech recognition process."""
        async with websockets.connect(self.uri, ping_timeout=None) as websocket:
            with wave.open(self.audio_path, "rb") as wav_file:
                AudioFileValidator.validate(wav_file)
                sample_rate = wav_file.getframerate()
                self.buffer_size = max(
                    self.buffer_size, int(sample_rate * 0.2))

                await self._send_config(websocket, sample_rate)

                while True:
                    audio_data = wav_file.readframes(self.buffer_size)
                    if not audio_data:
                        break

                    await websocket.send(audio_data)
                    response = await websocket.recv()
                    await self._process_server_response(str(response))

                write_to_file(self.output_path, self.last_partial + "\n")
                await websocket.send(json.dumps({"eof": 1}))
                await asyncio.sleep(1.0)


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <audio_file> <output_file> [server_url]",
              file=sys.stderr)
        sys.exit(1)

    audio_file = sys.argv[1]
    is_conveted = False

    if not audio_file.endswith("wav"):
        is_convertable = FileConverter.is_convertable()
        if not is_convertable:
            print(
                "Cannot find ffmpeg on this computer. Please check that ffmpeg is installed.")
            exit(1)

        success = FileConverter.convert(audio_file, audio_file + ".wav")

        if not success:
            print(
                f"Cannot convert {audio_file} to wav. Please check that ffmpeg is installed.")
            exit(1)

        audio_file += ".wav"
        is_conveted = True

    def dispose(_, __):
        if is_conveted:
            os.remove(audio_file)

        print("Done!")
        sys.exit(0)

    signal.signal(signal.SIGINT, dispose)

    output_file = sys.argv[2]
    server_url = sys.argv[3] if len(sys.argv) > 3 else "ws://localhost:2700"

    print(audio_file)

    client = SpeechRecognitionClient(server_url, audio_file, output_file)
    asyncio.run(client.run())
    dispose(0, 0)


if __name__ == "__main__":
    main()
