"""Scrapers package.

Importing this package registers every implemented scraper with the ScraperFactory
(registration happens as a side effect of importing each module).
"""

from ingestion.scrapers import devbg as _devbg  # noqa: F401
from ingestion.scrapers import ndk as _ndk  # noqa: F401
from ingestion.scrapers import sofia_opera as _sofia_opera  # noqa: F401
from ingestion.scrapers import ticketmaster as _ticketmaster  # noqa: F401
from ingestion.scrapers import visitsofia as _visitsofia  # noqa: F401

# Live-verified: devbg, ndk, sofia_opera, visitsofia, ticketmaster (TM has no BG inventory yet).
# Deferred: bandsintown (optional — API needs an approved app_id, awaiting key).
