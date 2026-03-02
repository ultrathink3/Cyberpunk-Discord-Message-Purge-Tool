"""Profile management for multiple Discord accounts."""

from __future__ import annotations

import logging
from datetime import datetime

from .database import Database
from .discord_client import DiscordClient
from .exceptions import ProfileError
from .models import Profile
from .rate_limiter import RateLimiter
from .token_vault import TokenVault

logger = logging.getLogger("neurowipe.profile_manager")


class ProfileManager:
    """Manages Discord account profiles with token storage."""

    def __init__(self, database: Database, token_vault: TokenVault):
        self.database = database
        self.token_vault = token_vault
        self._active_client: DiscordClient | None = None
        self._active_profile: Profile | None = None

    @property
    def active_profile(self) -> Profile | None:
        return self._active_profile

    @property
    def active_client(self) -> DiscordClient | None:
        return self._active_client

    async def load_profiles(self) -> list[Profile]:
        """Load all profiles from database."""
        return await self.database.get_profiles()

    async def create_profile(
        self, name: str, token: str, rate_limiter: RateLimiter | None = None
    ) -> Profile:
        """Create a new profile by validating token and saving."""
        client = DiscordClient(token, rate_limiter or RateLimiter())
        try:
            user_info = await client.validate_token()
        except Exception as e:
            await client.close()
            raise ProfileError(f"Token validation failed: {e}") from e

        profile = Profile(
            name=name or user_info.display_name,
            user_id=user_info.id,
            username=user_info.username,
            discriminator=user_info.discriminator,
            avatar=user_info.avatar,
            is_active=False,
            created_at=datetime.now(),
        )

        profile.id = await self.database.create_profile(profile)
        self.token_vault.store_token(str(profile.id), token)
        await client.close()

        logger.info(f"Profile created: {profile.name} ({profile.user_id})")
        return profile

    async def update_profile(self, profile: Profile, new_token: str | None = None) -> None:
        """Update an existing profile."""
        if new_token:
            client = DiscordClient(new_token)
            try:
                user_info = await client.validate_token()
                profile.user_id = user_info.id
                profile.username = user_info.username
                profile.discriminator = user_info.discriminator
                profile.avatar = user_info.avatar
            except Exception as e:
                await client.close()
                raise ProfileError(f"Token validation failed: {e}") from e
            finally:
                await client.close()

            self.token_vault.store_token(str(profile.id), new_token)

        await self.database.update_profile(profile)
        logger.info(f"Profile updated: {profile.name}")

    async def delete_profile(self, profile_id: int) -> None:
        """Delete a profile and its token."""
        if self._active_profile and self._active_profile.id == profile_id:
            await self.disconnect()
        self.token_vault.delete_token(str(profile_id))
        await self.database.delete_profile(profile_id)
        logger.info(f"Profile deleted: {profile_id}")

    async def connect(
        self, profile_id: int, rate_limiter: RateLimiter | None = None
    ) -> DiscordClient:
        """Connect with a profile's token."""
        token = self.token_vault.get_token(str(profile_id))
        if not token:
            raise ProfileError(f"No token found for profile {profile_id}")

        if self._active_client:
            await self._active_client.close()

        client = DiscordClient(token, rate_limiter or RateLimiter())
        user_info = await client.validate_token()

        await self.database.set_active_profile(profile_id)
        profiles = await self.database.get_profiles()
        self._active_profile = next(
            (p for p in profiles if p.id == profile_id), None
        )
        if self._active_profile:
            self._active_profile.last_used = datetime.now()
            await self.database.update_profile(self._active_profile)

        self._active_client = client
        logger.info(f"Connected as {user_info.display_name}")
        return client

    async def connect_with_token(
        self, token: str, rate_limiter: RateLimiter | None = None
    ) -> DiscordClient:
        """Connect directly with a token (without saving as profile)."""
        if self._active_client:
            await self._active_client.close()

        client = DiscordClient(token, rate_limiter or RateLimiter())
        await client.validate_token()
        self._active_client = client
        return client

    async def disconnect(self) -> None:
        """Disconnect current session."""
        if self._active_client:
            await self._active_client.close()
            self._active_client = None
        self._active_profile = None
        logger.info("Disconnected")
