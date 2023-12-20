# >>>> </> STANDARD IMPORTS </>
# >>>> ********************************************************************************
import logging
import io
# from typing import Optional
# >>>> ********************************************************************************

# >>>> </> EXTERNAL IMPORTS </>
# >>>> ********************************************************************************
from fastapi import APIRouter
from fastapi import Response, File, UploadFile, HTTPException, status
from fastapi.responses import UJSONResponse
# from pydantic import BaseModel
import ujson as json
# >>>> ********************************************************************************

# >>>> </> LOCAL IMPORTS </>
# >>>> ********************************************************************************
import settings
from src_logging import log_config
from src_processes.proc_svg_parsing import SVGParser
from src_utils.wrappers import parallel_task_with_timeout
from src_utils.aws_utils import S3Utils
# from src_utils.loading_utils import load_pdf
# from request_models import FileDetails
from .request_models import SVGParsingFilesDataS3
# >>>> ********************************************************************************


# ________________________________________________________________________________
# --- INIT CONFIG - LOGGER SETUP ---
logger = log_config.setup_logger(logger_name=__name__, logging_level=logging.DEBUG)

# ________________________________________________________________________________
# --- FastAPI ROUTER ---
svg_quad_bezier_lines_router = APIRouter(prefix="/v1/svg-parsing")


# ________________________________________________________________________________
# --- EXTRACT QUAD BEZIER LINES DATA ---
@svg_quad_bezier_lines_router.post(path="/extract-quad-bezier-lines-data/",
                                   responses={200: {}, 500: {}, 503: {}},
                                   status_code=status.HTTP_200_OK,
                                   response_class=UJSONResponse,
                                   tags=["SVG Parsing - Extract QUADRATIC BEZIER LINES as JSON data", "S3"],
                                   summary="Extract QUADRATIC BEZIER LINES data in JSON format.")
async def extract_quad_bezier_lines_data(return_svg_size: bool = True,
                                         return_attributes: bool = False,
                                         pdf_file: UploadFile = File(...),
                                         page_num: int = 0) -> Response:
    # --- CHECK IF FILE IS PDF ---
    if not pdf_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail="ERROR -> '/extract-quad-bezier-lines-data': File type not supported")

    # --- EXTRACT quad_bezier DATA ---
    quad_bezier_data, width, height, attributes = (SVGParser.
                                                   extract_svg_quad_bezier_lines(pdf_file_obj=pdf_file,
                                                                                 page_num=page_num,
                                                                                 round_threshold=settings.ROUND_THRESHOLD)
                                                   )
    # \
    #     parallel_task_with_timeout(func_obj=SVGParser.extract_svg_quad_bezier_lines,
    #                                pdf_file=pdf_file,
    #                                page_num=page_num)

    json_payload = {"quad_bezier_lines_data": quad_bezier_data}

    if return_svg_size:
        json_payload.update({"svg_width": width,
                             "svg_height": height})
    if return_attributes:
        json_payload["attributes"] = attributes

    # ________________________________________________________________________________
    # --- RETURN RESPONSE -> JSON WITH quad_bezier DATA ---
    return UJSONResponse(content=json_payload,
                         status_code=status.HTTP_200_OK,
                         media_type="application/json")


# ________________________________________________________________________________
# --- EXTRACT QUAD BEZIER LINES DATA - S3 ---
@svg_quad_bezier_lines_router.post(path="/extract-quad-bezier-lines-data-s3/",
                                   responses={200: {}, 500: {}, 503: {}},
                                   status_code=status.HTTP_200_OK,
                                   response_class=UJSONResponse,
                                   tags=["SVG Parsing - Extract QUADRATIC BEZIER LINES as JSON data"],
                                   summary="Extract QUADRATIC BEZIER LINES data in JSON format.")
async def extract_quad_bezier_lines_data(files_data: SVGParsingFilesDataS3) -> Response:
    # --- INIT S3 UTILS INSTANCE ---
    s3 = S3Utils()

    # --- DOWNLOAD FILE FROM AWS S3 ---
    pdf_file_bytes = s3.download_file_obj(s3_bucket_name=files_data.s3_bucket_name,
                                          s3_file_key=files_data.files.pdf_file.file_key)

    # ________________________________________________________________________________
    # --- EXTRACT QUADRATIC BEZIER LINES DATA ---
    quad_bezier_data, width, height, attributes = (SVGParser.
                                                   extract_svg_quad_bezier_lines(pdf_file_obj=pdf_file_bytes,
                                                                                 page_num=files_data.page_num,
                                                                                 round_threshold=settings.ROUND_THRESHOLD,
                                                                                 s3_origin=True)
                                                   )

    json_payload = {"quad_bezier_lines_data": quad_bezier_data}

    if files_data.return_svg_size:
        json_payload.update({"svg_width": width,
                             "svg_height": height})
    if files_data.return_attributes:
        json_payload["attributes"] = attributes

    # ________________________________________________________________________________
    # --- CONVERT JSON TO BYTES STREAM ---
    json_payload = json.dumps(json_payload)
    json_byte_stream = io.BytesIO(json_payload.encode("utf-8"))

    # --- UPLOAD RESULT TO AWS S3 BUCKET ---
    try:
        s3_upload_status = s3.upload_file_obj(s3_bucket_name=files_data.s3_bucket_name,
                                              s3_file_key=files_data.out_s3_file_key,
                                              file_byte_stream=json_byte_stream)
        if not s3_upload_status:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"ERROR -> S3 upload status: {s3_upload_status}")
        return Response(status_code=status.HTTP_200_OK)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"ERROR -> Failed to upload file to S3. Error: {e}")
