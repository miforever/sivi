from apps.vacancies.scraper.platforms.argos_uz import ArgosUzParser
from apps.vacancies.scraper.platforms.base import BasePlatformParser
from apps.vacancies.scraper.platforms.hh_uz import HhUzParser
from apps.vacancies.scraper.platforms.ish_uz import IshUzParser
from apps.vacancies.scraper.platforms.ishkop_uz import IshkopUzParser
from apps.vacancies.scraper.platforms.ishplus_uz import IshplusUzParser
from apps.vacancies.scraper.platforms.olx_uz import OlxUzParser
from apps.vacancies.scraper.platforms.osonish_uz import OsonishUzParser
from apps.vacancies.scraper.platforms.uzairways import UzairwaysParser
from apps.vacancies.scraper.platforms.vacandi_uz import VacandiUzParser

PLATFORM_REGISTRY: dict[str, type[BasePlatformParser]] = {
    "argos_uz": ArgosUzParser,
    "hh_uz": HhUzParser,
    "ish_uz": IshUzParser,
    "ishkop_uz": IshkopUzParser,
    "ishplus_uz": IshplusUzParser,
    "olx_uz": OlxUzParser,
    "osonish_uz": OsonishUzParser,
    "uzairways": UzairwaysParser,
    "vacandi_uz": VacandiUzParser,
}


def get_platform_parser(platform_name: str) -> BasePlatformParser:
    parser_cls = PLATFORM_REGISTRY.get(platform_name)
    if not parser_cls:
        raise ValueError(f"No parser registered for platform: {platform_name}")
    return parser_cls()
