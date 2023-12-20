# >>>> </> STANDARD IMPORTS </>
# >>>> ********************************************************************************
import os
import logging
from pathlib import Path
# >>>> ********************************************************************************

# >>>> </> EXTERNAL IMPORTS </>
# >>>> ********************************************************************************
from dotenv import load_dotenv
# >>>> ********************************************************************************

# >>>> </> LOCAL IMPORTS </>
# >>>> ********************************************************************************
from src_logging import log_config
# >>>> ********************************************************************************


# ________________________________________________________________________________
# --- INIT CONFIG - LOGGER SETUP ---
logger = log_config.setup_logger(logger_name=__name__, logging_level=logging.INFO)


class EnvSetupFailedError(Exception):
    """Custom error that is raised when Environment setup fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def load_env_file(env_file_path: Path):
    if os.path.exists(env_file_path):
        load_dotenv(dotenv_path=env_file_path)
    else:
        raise EnvSetupFailedError(message=f"ERROR: Environment setup failed -> .env file '{env_file_path}' not found.")
        # raise FileNotFoundError


def load_multiple_env_files(env_files_paths: list):
    # env_file_path = Path(settings.env_file_path)
    # env_dev_file_path = Path(settings.env_dev_file_path)
    # env_prod_file_path = Path(settings.env_prod_file_path)
    # env_files_paths: list = [env_file_path, env_dev_file_path, env_prod_file_path]

    for env_file_path in env_files_paths:
        if os.path.exists(env_file_path):
            load_dotenv(dotenv_path=env_file_path)
        else:
            raise EnvSetupFailedError(message=f"ERROR: Environment setup failed -> .env file '{env_file_path}' not found.")
            # raise FileNotFoundError


# ________________________________________________________________________________
# --- INIT CONFIG - ENVIRONMENT LOADING ---
# def setup_env(env_general_file_path:    Path = Path(".env"),
#               env_dev_file_path:        Path = Path("src_env/dev/.env"),
#               env_prod_file_path:       Path = Path("src_env/prod/.env"),
#               env_stage_file_path:      Path = Path("src_env/stage/.env")) -> None:

env_general_file_path: Path = Path(".env")
env_dev_file_path: Path = Path("src_env/dev/.env")
env_prod_file_path: Path = Path("src_env/prod/.env")
env_stage_file_path: Path = Path("src_env/stage/.env")

logger.info(">>> SETUP OF THE GENERAL .env FILE <<<")
load_env_file(env_file_path=env_general_file_path)

if os.getenv("ENVIRONMENT") is None:
    logger.error(">>> ENV VAR | ENVIRONMENT | IS NOT SET - SETTING TO DEFAULT: 'DEVELOPMENT' <<<")
    os.environ["ENVIRONMENT"] = "DEVELOPMENT"

if os.getenv("ENVIRONMENT") == "PRODUCTION":
    logger.info(">>> ENV VAR | ENVIRONMENT | IS SET TO: 'PRODUCTION' <<<")
    load_env_file(env_file_path=env_prod_file_path)

elif os.getenv("ENVIRONMENT") == "DEVELOPMENT":
    logger.info(">>> ENV VAR | ENVIRONMENT | IS SET TO: 'DEVELOPMENT' <<<")
    load_env_file(env_file_path=env_dev_file_path)

elif os.getenv("ENVIRONMENT") == "STAGE":
    logger.info(">>> ENV VAR | ENVIRONMENT | IS SET TO: 'STAGE' <<<")
    load_env_file(env_file_path=env_stage_file_path)
