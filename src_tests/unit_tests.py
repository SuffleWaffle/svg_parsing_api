# >>>> </> STANDARD IMPORTS </>
# >>>> ********************************************************************************
import asyncio
import logging
# TEMPORARY
import os
import io
# >>>> ********************************************************************************

# >>>> </> EXTERNAL IMPORTS </>
# >>>> ********************************************************************************
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
import httpx
import pytest
import json
# import requests
# from requests.auth import HTTPBasicAuth
from pydantic import BaseModel, Field
from typing import List
# from unittest.mock import patch
# import mock
# >>>> ********************************************************************************

# >>>> </> LOCAL IMPORTS </>
# >>>> ********************************************************************************
from main import app
from src_logging import log_config
from src_utils.aws_utils import S3FileOps
import tests_settings
# >>>> ********************************************************************************

dev_username = "drawer"
dev_password = "Y4AuMasf"
base_url = tests_settings.BASE_URL

# ________________________________________________________________________________
# --- INIT CONFIG - LOGGER SETUP ---
logger = log_config.setup_logger(logger_name=__name__, logging_level=logging.DEBUG)

client = TestClient(app)


# ________________________________________________________________________________
# >>>> </> TEST - EXTRACT ALL SHAPES DATA - S3 - FILE NOT FOUND </>
def test_s3_file_not_found():
    test_data = tests_settings.TEST_EXTRACT_ALL_SHAPES_S3
    link = base_url + test_data["link"]

    json_data = test_data["json_data"]
    json_data["files"]["pdf_file"]["file_key"] = "wrong_file.pdf"
    json_payload = json.dumps(json_data)

    response = client.post(url=link,
                           content=json_payload)

    # ________________________________________________________________________________
    # --- CHECK RESPONSE STATUS CODE ---
    assertion_s3(response,
                 status_code=503)


# ________________________________________________________________________________
# >>>> </> TEST - EXTRACT ALL SHAPES DATA - JSON </
def test_extract_all_shapes_post():
    test_data = tests_settings.TEST_EXTRACT_ALL_SHAPES_JSON
    link = base_url + test_data["link"]

    pdf_data = download_file_s3(test_data["file_keys"]["pdf_file"], test_data["s3_bucket_name"])
    files = {"pdf_file": (pdf_data.name, pdf_data, "application/pdf")}
    json_data = test_data["json_data"]

    response = client.post(url=link,
                           files=files,
                           data=json_data)

    # ________________________________________________________________________________
    # --- CHECK RESPONSE STATUS CODE + CONTENT TYPE ---
    assertion_json(response,
                   status_code=200)

    # ________________________________________________________________________________
    # --- CHECK JSON CONTENT ---
    response_data = response.json()

    # Data validation
    assert ExtractAllShapesOutJSON(**response_data)
    logger.info(f"- RESPONSE JSON IS OK -")


def assertion_json(response,
                   status_code: int):
    # ________________________________________________________________________________
    # --- CHECK RESPONSE STATUS CODE ---
    assert response.status_code == status_code
    logger.info(f"- RESPONSE STATUS CODE - {response.status_code}")

    # ________________________________________________________________________________
    # --- CHECK RESPONSE CONTENT TYPE ---
    assert response.headers["content-type"] == "application/json"
    content_type = response.headers["content-type"]
    logger.info(f"- RESPONSE CONTENT TYPE - {content_type}")


def assertion_s3(response,
                 status_code: int):
    # ________________________________________________________________________________
    # --- CHECK RESPONSE STATUS CODE ---
    assert response.status_code == status_code
    logger.info(f"- RESPONSE STATUS CODE - {response.status_code}")


# ________________________________________________________________________________
# >>>> </> TEST - EXTRACT ALL SHAPES JSON MODEL </>
class ExtractAllShapesOutJSON(BaseModel):
    lines: dict
    cubic_lines: dict
    circles: dict
    quads: dict
    circles: dict
    rectangles: dict


def download_n_save_file_s3(file_key, s3_bucket_name):
    # _____________________________________________________________________________
    # --- INIT S3FileOps INSTANCE ---
    logger.info("- CONNECTING TO AWS S3 BUCKET -")
    s3 = S3FileOps(s3_bucket_name=s3_bucket_name)

    # --- DOWNLOAD FILE FROM S3 ---
    file_data = s3.download_file_obj(s3_bucket_name, file_key)

    # --- SAVING FILE ---
    logger.info("- 2 - SAVING FILE -")
    filename = file_key.split('/')[-1]

    with open(filename, "wb") as f:
        f.write(file_data.getvalue())


def download_file_s3(file_key, s3_bucket_name):
    # _____________________________________________________________________________
    # --- INIT S3FileOps INSTANCE ---
    logger.info("- CONNECTING TO AWS S3 BUCKET -")
    s3 = S3FileOps(s3_bucket_name=s3_bucket_name)

    # --- DOWNLOAD FILE FROM S3 ---
    file_data = s3.download_file_obj(s3_bucket_name, file_key)
    file_data.name = file_key.split('/')[-1]

    return file_data
