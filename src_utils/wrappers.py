# >>>> </> STANDARD IMPORTS </>
# >>>> ********************************************************************************
import logging
from typing import Callable
# >>>> ********************************************************************************

# >>>> </> EXTERNAL IMPORTS </>
# >>>> ********************************************************************************
# import ray
from pathos.helpers import mp as pathos_mp
from pathos.multiprocessing import ProcessPool
# >>>> ********************************************************************************

# >>>> </> LOCAL IMPORTS </>
# >>>> ********************************************************************************
import settings
from src_logging import log_config
# >>>> ********************************************************************************

# ________________________________________________________________________________
# --- INIT CONFIG - LOGGER SETUP ---
logger = log_config.setup_logger(logger_name=__name__, logging_level=logging.DEBUG)


# --- PRODUCTION READY ---
def parallel_task_with_timeout(func_obj: Callable,
                               proc_timeout: int = settings.PARALLEL_PROC_TIMEOUT,
                               **kwargs):
    """ --- PRODUCTION READY ---\n
        - A decorator function that wraps a parameter function in a separate parallel process.
        - Parallel process runs with timeout (user-defined or default settings.PARALLEL_PROC_TIMEOUT value).

        Args:
            func_obj(Callable): Function to be processed in parallel.
            proc_timeout(int): Number of seconds to wait before the process is terminated.
            **kwargs: Keyword arguments to be passed to the function

        Returns:
            Function execution result or None if the process timed out.
    """

    pool = ProcessPool(nodes=1)
    result = pool.apipe(func_obj, **kwargs)

    try:
        return result.get(timeout=proc_timeout)

    except pathos_mp.TimeoutError:
        logger.error(f">>> PROCESS TIMEOUT ERROR\n"
                     f">>> Process - PID: {result.pool[0].pid}\n"
                     f">>> Timed out after {proc_timeout} seconds.")
        pool.terminate()
        return None
