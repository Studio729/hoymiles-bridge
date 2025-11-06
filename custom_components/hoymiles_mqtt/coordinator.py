"""Data update coordinator for Hoymiles MQTT Bridge."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, ENDPOINT_HEALTH, ENDPOINT_STATS

_LOGGER = logging.getLogger(__name__)


class HoymilesMqttCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data fetching from Hoymiles MQTT health API."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._session: aiohttp.ClientSession | None = None
        self._consecutive_failures = 0
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=15)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=aiohttp.TCPConnector(
                    limit=10,
                    ttl_dns_cache=300,
                    force_close=False,
                ),
            )
            _LOGGER.debug("Created new aiohttp session for %s:%s", self.host, self.port)
        return self._session

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        import time
        start_time = time.time()
        
        _LOGGER.debug(
            "[API Call Start] Fetching data from %s:%s (session_active=%s, consecutive_failures=%d)",
            self.host, self.port,
            self._session is not None and not self._session.closed,
            self._consecutive_failures
        )
        
        try:
            session = await self._get_session()
            
            # Use a longer timeout - 20 seconds total
            async with async_timeout.timeout(20):
                # Fetch health data with retry
                _LOGGER.debug("[API Call] Fetching %s from %s:%s", ENDPOINT_HEALTH, self.host, self.port)
                health_data = await self._fetch_endpoint_with_retry(session, ENDPOINT_HEALTH)
                _LOGGER.debug("[API Call] Received health data: healthy=%s, uptime=%s",
                             health_data.get("healthy"), health_data.get("uptime_seconds"))
                
                # Fetch stats data with retry
                _LOGGER.debug("[API Call] Fetching %s from %s:%s", ENDPOINT_STATS, self.host, self.port)
                stats_data = await self._fetch_endpoint_with_retry(session, ENDPOINT_STATS)
                _LOGGER.debug("[API Call] Received stats data: records=%s", 
                             stats_data.get("total_records"))
                
                # Reset failure counter on success
                if self._consecutive_failures > 0:
                    _LOGGER.info(
                        "Successfully reconnected to %s:%s after %d failures",
                        self.host, self.port, self._consecutive_failures
                    )
                self._consecutive_failures = 0
                
                elapsed = time.time() - start_time
                _LOGGER.debug(
                    "[API Call Complete] Success in %.2fs from %s:%s",
                    elapsed, self.host, self.port
                )
                
                # Combine data
                return {
                    "health": health_data,
                    "stats": stats_data,
                    "available": True,
                }
        except asyncio.TimeoutError as err:
            import time
            elapsed = time.time() - start_time
            self._consecutive_failures += 1
            _LOGGER.warning(
                "[API Call Failed] Timeout after %.2fs from %s:%s (failure %d): %s",
                elapsed, self.host, self.port, self._consecutive_failures, err
            )
            _LOGGER.debug(
                "[API Call Failed] Session state: active=%s, closed=%s",
                self._session is not None,
                self._session.closed if self._session else "N/A"
            )
            # Close session on timeout to force fresh connection next time
            if self._session and not self._session.closed:
                _LOGGER.debug("[Session] Closing session due to timeout")
                await self._session.close()
                self._session = None
            raise UpdateFailed(f"Timeout communicating with API: {err}") from err
        except aiohttp.ClientError as err:
            import time
            elapsed = time.time() - start_time
            self._consecutive_failures += 1
            _LOGGER.warning(
                "[API Call Failed] Client error after %.2fs from %s:%s (failure %d): %s",
                elapsed, self.host, self.port, self._consecutive_failures, err
            )
            _LOGGER.debug(
                "[API Call Failed] Error type: %s, Session: %s",
                type(err).__name__,
                "active" if (self._session and not self._session.closed) else "closed/none"
            )
            # Close session on client error
            if self._session and not self._session.closed:
                _LOGGER.debug("[Session] Closing session due to client error")
                await self._session.close()
                self._session = None
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            import time
            elapsed = time.time() - start_time
            self._consecutive_failures += 1
            _LOGGER.error(
                "[API Call Failed] Unexpected error after %.2fs from %s:%s (failure %d): %s",
                elapsed, self.host, self.port, self._consecutive_failures, err,
                exc_info=True
            )
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def _fetch_endpoint_with_retry(
        self, session: aiohttp.ClientSession, endpoint: str, max_retries: int = 2
    ) -> dict[str, Any]:
        """Fetch data from a specific endpoint with retry logic."""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self._fetch_endpoint(session, endpoint)
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                last_error = err
                if attempt < max_retries - 1:
                    wait_time = 0.5 * (attempt + 1)  # 0.5s, 1s
                    _LOGGER.debug(
                        "Retry %d/%d for %s after %s, waiting %.1fs",
                        attempt + 1, max_retries, endpoint, err, wait_time
                    )
                    await asyncio.sleep(wait_time)
                else:
                    _LOGGER.warning(
                        "All %d retries failed for %s: %s",
                        max_retries, endpoint, err
                    )
        
        # All retries failed
        raise last_error

    async def _fetch_endpoint(
        self, session: aiohttp.ClientSession, endpoint: str
    ) -> dict[str, Any]:
        """Fetch data from a specific endpoint."""
        import time
        url = f"{self.base_url}{endpoint}"
        fetch_start = time.time()
        
        _LOGGER.debug("[HTTP] GET %s", url)
        
        try:
            async with session.get(url) as response:
                status = response.status
                fetch_time = time.time() - fetch_start
                
                _LOGGER.debug(
                    "[HTTP] Response %d from %s in %.3fs",
                    status, endpoint, fetch_time
                )
                
                response.raise_for_status()
                data = await response.json()
                
                _LOGGER.debug(
                    "[HTTP] Successfully parsed JSON from %s (%d bytes)",
                    endpoint, len(str(data))
                )
                
                return data
        except aiohttp.ClientResponseError as err:
            _LOGGER.error(
                "[HTTP] Response error %d from %s: %s",
                err.status, endpoint, err.message
            )
            raise
        except asyncio.TimeoutError:
            _LOGGER.error("[HTTP] Timeout for %s", endpoint)
            raise
        except Exception as err:
            _LOGGER.error(
                "[HTTP] Unexpected error for %s: %s",
                endpoint, err, exc_info=True
            )
            raise

    def get_health_data(self) -> dict[str, Any] | None:
        """Get health data from coordinator."""
        if self.data and "health" in self.data:
            return self.data["health"]
        return None

    def get_stats_data(self) -> dict[str, Any] | None:
        """Get stats data from coordinator."""
        if self.data and "stats" in self.data:
            return self.data["stats"]
        return None

    def get_dtu_data(self, dtu_name: str = "DTU") -> dict[str, Any] | None:
        """Get DTU-specific data."""
        health = self.get_health_data()
        if health and "dtus" in health and dtu_name in health["dtus"]:
            return health["dtus"][dtu_name]
        return None

    def is_available(self) -> bool:
        """Check if the API is available."""
        return self.data is not None and self.data.get("available", False)

    async def async_shutdown(self) -> None:
        """Shutdown coordinator and cleanup resources."""
        if self._session and not self._session.closed:
            _LOGGER.debug("Closing aiohttp session for %s:%s", self.host, self.port)
            await self._session.close()
            self._session = None

