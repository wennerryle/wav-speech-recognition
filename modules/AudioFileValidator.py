import wave

class AudioFileValidator:
    """Validates audio file format requirements."""

    @staticmethod
    def validate(wave_file: wave.Wave_read) -> None:
        """Check if audio file meets requirements."""
        if wave_file.getnchannels() != 1:
            raise ValueError("Only mono audio supported. Current channels: "
                           f"{wave_file.getnchannels()}")
        if wave_file.getsampwidth() != 2:
            raise ValueError("Only 16-bit PCM supported")