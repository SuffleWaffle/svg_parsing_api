# >>>> </> STANDARD IMPORTS </>
# >>>> ********************************************************************************
import os
import sys
import logging
import asyncio
from pathlib import Path
# >>>> ********************************************************************************

# >>>> </> EXTERNAL IMPORTS </>
# >>>> ********************************************************************************
from fastapi import FastAPI, Response, status
from fastapi.responses import UJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ujson as json
# >>>> ********************************************************************************

# >>>> </> LOCAL IMPORTS </>
# >>>> ********************************************************************************
# ---- CONFIG ----
# import settings
from src_logging import log_config
from src_env import env_config
# ---- FastAPI ROUTERS ----
from src_routers.rtr_extract_lines import svg_lines_router
from src_routers.rtr_extract_circles import svg_circles_router
from src_routers.rtr_extract_rectangles import svg_rectangles_router
from src_routers.rtr_extract_cub_bezier import svg_cub_bezier_lines_router
from src_routers.rtr_extract_quad_bezier import svg_quad_bezier_lines_router
from src_routers.rtr_extract_all_shapes import svg_all_router
# >>>> ********************************************************************************


# ________________________________________________________________________________
# --- INIT CONFIG - LOGGER SETUP ---
logger = log_config.setup_logger(logger_name=__name__, logging_level=logging.INFO)

# ________________________________________________________________________________
# --- INIT CONFIG - ENVIRONMENT LOADING ---
# env_general_file_path = Path(".env")
# env_dev_file_path = Path("src_env/dev/.env")
# env_prod_file_path = Path("src_env/prod/.env")
# env_stage_file_path = Path("src_env/stage/.env")

# ________________________________________________________________________________
# --- INIT CONFIG - EVENT LOOP POLICY SETUP ---
if sys.platform == "linux":
    # --- PROD - uvloop (for Linux) EVENT LOOP POLICY SETUP ---
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    logging.info(">>>> EVENT LOOP POLICY SETUP - PROD - | uvloop.EventLoopPolicy | IS ACTIVE <<<<")

elif sys.platform == "win32":
    # --- DEV - win32 (for Windows) EVENT LOOP POLICY SETUP ---
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logging.info(">>>> EVENT LOOP POLICY SETUP - DEV - | WindowsSelectorEventLoopPolicy | IS ACTIVE <<<<")


# ________________________________________________________________________________
# >>>> </> FastAPI APP CONFIG </>
description = """
**SVG Parsing API - API Service for SVG files parsing and geometry extractions.**

## Healthcheck:

- **Healthcheck allows to monitor operational status of the API -> Returns status <HTTP_200_OK> if service instance is running**).

## SVG Parsing:

### Extract ALL SHAPES 
- **/extract-all-shapes-data             > Extract all shapes from SVG to JSON                  > JSON with all shapes data**


### Extract LINES 
- **/extract-lines-data             > Extract lines from SVG to JSON                  > JSON with lines data**

### Extract CIRCLES
- **/extract-circles-data           > Extract circles from SVG to JSON                > JSON with circles data**

### Extract RECTANGLES
- **/extract-rectangles-data        > Extract rectangles from SVG to JSON             > JSON with rectangles data**

### Extract CUBIC BEZIER CURVES
- **/extract-cub-bezier-lines-data  > Extract cubic Bezier lines from SVG to JSON     > JSON with cubic Bezier lines**

### Extract QUADRATIC BEZIER CURVES
- **/extract-quad-bezier-lines-data > Extract quadratic Bezier lines from SVG to JSON > JSON with quadratic Bezier lines**

"""

app = FastAPI(
    title="Drawer AI - SVG Parsing API",
    description=description,
    version="0.1.0")

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=json.loads(os.getenv("APP_CORS_ORIGINS")),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router=svg_lines_router)
app.include_router(router=svg_circles_router)
app.include_router(router=svg_rectangles_router)
app.include_router(router=svg_cub_bezier_lines_router)
app.include_router(router=svg_quad_bezier_lines_router)
app.include_router(router=svg_all_router)


# ________________________________________________________________________________
# >>>> </> APP - STARTUP </>
@app.on_event(event_type="startup")
async def startup_event():
    logger.info(">>> SVG Parsing API - SERVICE STARTUP COMPLETE <<<")


# ________________________________________________________________________________
# >>>> </> APP - SHUTDOWN </>
@app.on_event(event_type="shutdown")
async def shutdown_event():
    logger.info(">>> SVG Parsing API - SERVICE SHUTDOWN <<<")


# ________________________________________________________________________________
# >>>> </> APP - HEALTHCHECK </>
class HealthcheckResponse(BaseModel):
    healthcheck: str = "API Status 200"


@app.get(path="/healthcheck/",
         status_code=status.HTTP_200_OK,
         response_model=HealthcheckResponse,
         tags=["HEALTHCHECK"],
         summary="Healthcheck endpoint for API service.")
async def healthcheck() -> Response:
    logger.info("--- HEALTHCHECK Endpoint - Status 200 ---")
    return UJSONResponse(content={"healthcheck": "API Status 200"},
                         status_code=status.HTTP_200_OK)


# ________________________________________________________________________________
# >>>> </> APP - DEV RUN CONFIG </>
# if __name__ == "main":
#     import uvicorn

    # ________________________________________________________________________________
    # >>>> RUN CMD for | Gunicorn with UvicornWorker |
    # ---- web: gunicorn app_main:app --workers 4 -k uvicorn.test_workers.UvicornWorker -b 0.0.0.0:8026
    # ________________________________________________________________________________
    # uvicorn.run(app=app, host=APP_HOST, port=APP_PORT, workers=APP_WORKERS, log_level="debug")
    # ________________________________________________________________________________
    # uvicorn.run("main:app", host="0.0.0.0", port=8027, reload=True, log_level="info")
