from apps.vacancies.scraper.base import ParsedVacancy as ParsedVacancy
from apps.vacancies.scraper.channels.base import BaseChannelParser
from apps.vacancies.scraper.channels.click_jobs import ClickJobsParser
from apps.vacancies.scraper.channels.clozjobs import ClozJobsParser
from apps.vacancies.scraper.channels.data_ish import DataIshParser
from apps.vacancies.scraper.channels.doda_jobs import DodaJobsParser
from apps.vacancies.scraper.channels.edu_vakansiya import EduVakansiyaParser
from apps.vacancies.scraper.channels.example_uz import ExampleUzParser
from apps.vacancies.scraper.channels.hrjob_uz import HrjobUzParser
from apps.vacancies.scraper.channels.ishmi_ish import IshmiIshParser
from apps.vacancies.scraper.channels.itjobs_uzbekistan import ITjobsUzbekistanParser
from apps.vacancies.scraper.channels.itpark_uz import ItparkUzParser
from apps.vacancies.scraper.channels.linkedin_jobs_uz import LinkedInJobsUzParser
from apps.vacancies.scraper.channels.python_djangojobs import PythonDjangoJobsParser
from apps.vacancies.scraper.channels.ustoz_shogird import UstozShogirdParser
from apps.vacancies.scraper.channels.uzbekistan_ishbor import UzbekistanIshborParser
from apps.vacancies.scraper.channels.uzdev_jobs import UzdevJobsParser
from apps.vacancies.scraper.channels.uzjobs_uz import UzjobsUzParser
from apps.vacancies.scraper.channels.vacancy_uz_airports import VacancyUzAirportsParser

PARSER_REGISTRY: dict[str, type[BaseChannelParser]] = {
    "clozjobs": ClozJobsParser,
    "uzdev_jobs": UzdevJobsParser,
    "UstozShogird": UstozShogirdParser,
    "python_djangojobs": PythonDjangoJobsParser,
    "data_ish": DataIshParser,
    "UzjobsUz": UzjobsUzParser,
    "edu_vakansiya": EduVakansiyaParser,
    "click_jobs": ClickJobsParser,
    "Exampleuz": ExampleUzParser,
    "uzbekistanishborwork": UzbekistanIshborParser,
    "doda_jobs": DodaJobsParser,
    "itpark_uz": ItparkUzParser,
    "ITjobs_Uzbekistan": ITjobsUzbekistanParser,
    "hrjobuz": HrjobUzParser,
    "vacancyuzairports": VacancyUzAirportsParser,
    "linkedinjobsuzbekistan": LinkedInJobsUzParser,
    "ishmi_ish": IshmiIshParser,
}


def get_parser(channel_username: str) -> BaseChannelParser:
    parser_cls = PARSER_REGISTRY.get(channel_username)
    if not parser_cls:
        raise ValueError(f"No parser registered for channel: {channel_username}")
    return parser_cls()
