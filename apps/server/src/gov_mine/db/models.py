from gov_mine.db.base import Base
from gov_mine.modules.classify import models as _classify_models  # noqa: F401
from gov_mine.modules.crawl import models as _crawl_models  # noqa: F401
from gov_mine.modules.ingest import models as _ingest_models  # noqa: F401
from gov_mine.modules.institutions import models as _institutions_models  # noqa: F401
from gov_mine.modules.ledger import models as _ledger_models  # noqa: F401

__all__ = ["Base"]
