"""
Audio component for R2D2 sound playback.
"""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from r2d2.components.base import Component
from r2d2.protocol.constants import DeviceId, IOCommand, AnimatronicCommand, AudioPlaybackMode

if TYPE_CHECKING:
    from r2d2.robot import R2D2


class AudioComponent(Component):
    """Controls R2D2 audio playback."""

    async def play_sound(
        self,
        sound_id: int,
        mode: AudioPlaybackMode = AudioPlaybackMode.PLAY_IMMEDIATELY,
    ) -> None:
        """Play a pre-recorded sound.

        Args:
            sound_id: Sound ID (0-500+)
            mode: Playback mode

        Example:
            >>> await r2.audio.play_sound(1862)  # R2D2 chatty sound
        """
        data = struct.pack(">HB", sound_id, mode)
        await self._send_command(
            DeviceId.IO,
            IOCommand.PLAY_AUDIO_FILE,
            data,
        )

    async def stop(self) -> None:
        """Stop all audio playback."""
        await self._send_command(
            DeviceId.IO,
            IOCommand.STOP_ALL_AUDIO,
        )

    async def set_volume(self, volume: int) -> None:
        """Set audio volume.

        Args:
            volume: Volume level (0-255)
        """
        volume = max(0, min(255, volume))
        await self._send_command(
            DeviceId.IO,
            IOCommand.SET_AUDIO_VOLUME,
            bytes([volume]),
        )

    async def get_volume(self) -> int:
        """Get current audio volume.

        Returns:
            Volume level (0-255)
        """
        response = await self._send_command(
            DeviceId.IO,
            IOCommand.GET_AUDIO_VOLUME,
        )
        return response[0]

    async def play_animation(self, animation_id: int) -> None:
        """Play a pre-defined animation (sound + movement).

        Args:
            animation_id: Animation ID (0-50)
        """
        data = struct.pack(">H", animation_id)
        await self._send_command(
            DeviceId.ANIMATRONIC,
            AnimatronicCommand.PLAY_ANIMATION,
            data,
        )

    async def stop_animation(self) -> None:
        """Stop current animation."""
        await self._send_command(
            DeviceId.ANIMATRONIC,
            AnimatronicCommand.STOP_ANIMATION,
        )

    # Convenience methods for common sounds

    async def happy(self) -> None:
        """Play a happy sound."""
        await self.play_sound(1890)  # R2D2 positive

    async def sad(self) -> None:
        """Play a sad sound."""
        await self.play_sound(1913)  # R2D2 sad

    async def excited(self) -> None:
        """Play an excited sound."""
        await self.play_sound(1821)  # R2D2 excited

    async def alarm(self) -> None:
        """Play an alarm sound."""
        await self.play_sound(1708)  # R2D2 alarm

    async def scream(self) -> None:
        """Play a scream sound."""
        await self.play_sound(1938)  # R2D2 scream
