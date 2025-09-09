"""Convert utils module"""

import subprocess
import os


class FileAlreadyExistException(Exception):
    def __init__(self, message):
        super().__init__(message)


def quiet_run(args: list[str], debug=False) -> bool:
    """Runs command quietly. Return False if command not found.
    Throws an error if program failed."""
    if debug:
        subprocess.run(
            args,
            check=True
        )
    else:
        subprocess.run(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

    return True


class FileConverter:
    """Class that convert file to wav file using ffmpeg"""

    @staticmethod
    def is_convertable() -> bool:
        """Checks if ffmpeg available"""

        try:
            quiet_run(['command', 'ffmpeg'])
        except subprocess.CalledProcessError as e:
            return e.returncode == 1

        return False

    @staticmethod
    def convert(convert_from: str, convert_to: str) -> bool:
        """Convert a file from any format to wav"""

        if os.path.exists(convert_to):
            print("File " + convert_to +
                  " is already exist. Please delete it before next run.")
            return False

        return quiet_run([
            'ffmpeg', '-i',
            convert_from,
            '-acodec', 'pcm_s16le', '-ac', '1',
            convert_to
        ])
