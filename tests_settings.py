# >>>> </> STANDARD IMPORTS </>
# >>>> ********************************************************************************
import os
import string
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
# --- FASTAPI TEST SETTINGS ---
PORT = 8000

if os.getenv("ENVIRONMENT") == "DEVELOPMENT":
    PORT = os.getenv("DEV_APP_PORT")

if os.getenv("ENVIRONMENT") == "STAGE":
    PORT = os.getenv("STAGE_APP_PORT")

if os.getenv("ENVIRONMENT") == "PRODUCTION":
    PORT = os.getenv("PROD_APP_PORT")

PREFIX = "/v1/svg-parsing"
BASE_URL = f"http://localhost:{PORT}{PREFIX}"


# ________________________________________________________________________________
# --- PAYLOAD ---

TEST_DIRS = dict(
    extract_all_shapes=dict(
        pdf_dir="svg_parsing_service/test_extract_all_shapes/pdf_dir/",
        out_dir="svg_parsing_service/test_extract_all_shapes/out_dir/")
)

BUCKET_NAME = "drawer-ai-dev-services-testing-files"


TEST_EXTRACT_ALL_SHAPES_S3 = dict(
    link='/extract-all-shapes-s3/',
    json_data=dict(
        files=dict(
            pdf_file=dict(
                file_key=TEST_DIRS["extract_all_shapes"]["pdf_dir"]+"small-sample.pdf")
        ),
        s3_bucket_name=BUCKET_NAME,
        out_files=dict(
            lines=TEST_DIRS["extract_all_shapes"]["out_dir"]+"lines.json",
            cubic_lines=TEST_DIRS["extract_all_shapes"]["out_dir"]+"cubic_lines.json",
            quads=TEST_DIRS["extract_all_shapes"]["out_dir"]+"quads.json",
            circles=TEST_DIRS["extract_all_shapes"]["out_dir"]+"circles.json",
            rectangles=TEST_DIRS["extract_all_shapes"]["out_dir"]+"rectangles.json"
        ),
        page_num=0,
        return_svg_size=True,
        return_attributes=True
    )
)

TEST_EXTRACT_ALL_SHAPES_JSON = dict(
    link='/extract-all-shapes/',
    s3_bucket_name=BUCKET_NAME,
    file_keys=dict(
        pdf_file=TEST_DIRS["extract_all_shapes"]["pdf_dir"]+"small-sample.pdf"),
    json_data=dict(
        page_num=0,
        return_svg_size=True,
        return_attributes=True),
    )
