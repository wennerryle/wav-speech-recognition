import asyncio
from typing import Any, Dict, List, TypedDict
import websockets
import sys
import wave
import json

from websockets import ClientConnection

from modules.AudioFileValidator import AudioFileValidator
# from modules.myitertools import some

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
        config = { # type: ignore
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
        
        if self.last_partial != "" and (partial == "" or partial == None):
          write_to_file(self.output_path, self.last_partial + "\n")
          self.last_partial = ""
        
        if partial != None:
          self.last_partial = partial
        
        # alternatives = result.get("alternatives")
        # if alternatives == None:
        #   return
        
        # alts = [alt["text"] for alt in alternatives]
        # if some(alts, lambda text: text != ""):
        #     write_to_file(self.output_path, 
        #                 json.dumps(alts, ensure_ascii=False) + "\n")

    async def run(self) -> None:
        """Run the speech recognition process."""
        try:
            async with websockets.connect(self.uri, ping_timeout=None) as websocket:
                with wave.open(self.audio_path, "rb") as wav_file:
                    AudioFileValidator.validate(wav_file)
                    sample_rate = wav_file.getframerate()
                    self.buffer_size = max(self.buffer_size, int(sample_rate * 0.2))
                    
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
                    
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <audio_file> <output_file> [server_url]", 
              file=sys.stderr)
        sys.exit(1)
    
    audio_file = sys.argv[1]
    output_file = sys.argv[2]
    server_url = sys.argv[3] if len(sys.argv) > 3 else "ws://localhost:2700"
    
    client = SpeechRecognitionClient(server_url, audio_file, output_file)
    asyncio.run(client.run())


if __name__ == "__main__":
    main()