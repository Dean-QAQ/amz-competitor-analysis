"""Amazon product reviews crawler — CLI + integrable Python API."""

__version__ = "0.2.0"

from .api import ReviewsService, RunOutcome
from .fetch import FetchResult, fetch_reviews
from .sites import SITES, SiteConfig, get_site
from .tasks import ReviewTask, TaskStore

__all__ = [
    "FetchResult",
    "ReviewTask",
    "ReviewsService",
    "RunOutcome",
    "SITES",
    "SiteConfig",
    "TaskStore",
    "fetch_reviews",
    "get_site",
    "__version__",
]
