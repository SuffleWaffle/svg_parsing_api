# >>>> </> STANDARD IMPORTS </>
# >>>> ********************************************************************************
import logging
import io
# >>>> ********************************************************************************

# >>>> </> EXTERNAL IMPORTS </>
# >>>> ********************************************************************************
from fastapi import APIRouter
from fastapi import Response,  File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse, UJSONResponse
import ujson as json
# >>>> ********************************************************************************

# >>>> </> LOCAL IMPORTS </>
# >>>> ********************************************************************************
import settings
from src_logging import log_config
from src_processes.proc_svg_parsing import SVGParser
from src_utils.wrappers import parallel_task_with_timeout
from src_utils.aws_utils import S3FileOps
# from src_utils.loading_utils import load_pdf
# ---- REQUEST MODELS ----
from .request_models import ExtractAllShapesFilesDataS3
# >>>> ********************************************************************************


# ________________________________________________________________________________
# --- INIT CONFIG - LOGGER SETUP ---
logger = log_config.setup_logger(logger_name=__name__, logging_level=logging.DEBUG)

# ________________________________________________________________________________
# --- FastAPI ROUTER ---
svg_all_router = APIRouter(prefix="/v1/svg-parsing")


# ________________________________________________________________________________
# --- EXTRACT ALL SHAPES DATA ---
@svg_all_router.post(path="/extract-all-shapes/",
                     responses={200: {}, 500: {}, 503: {}},
                     status_code=status.HTTP_200_OK,
                     response_class=UJSONResponse,
                     tags=["SVG Parsing - Extract all shapes as JSON data"],
                     summary="Extract shapes in JSON format.")
async def extract_all_shapes_data_json(pdf_file: UploadFile = File(...),
                                       return_svg_size: bool = True,
                                       return_attributes: bool = False,
                                       page_num: int = 0) -> Response:
    # --- CHECK IF FILE IS PDF ---
    if not pdf_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail="ERROR -> '/extract-circles-data': File type not supported")

    # --- EXTRACT circles DATA ---
    all_svg = SVGParser.extract_all_svg(pdf_file_obj=pdf_file, config=settings.SVG_ELEMENTS_EXTRACTION, page_num=page_num,
                                        round_threshold=settings.ROUND_THRESHOLD)
    if not return_svg_size:
        for k, v in all_svg.items():
            del v['svg_width']
            del v['svg_height']

    if not return_attributes:
        for k, v in all_svg.items():
            if 'attributes' in v:
                del v['attributes']
            else:
                del v['lines_attributes']

    # ________________________________________________________________________________
    # --- RETURN RESPONSE -> JSON WITH circles DATA ---
    return UJSONResponse(content=all_svg,
                         status_code=status.HTTP_200_OK,
                         media_type="application/json")


# ________________________________________________________________________________
# --- EXTRACT ALL SHAPES DATA - S3 ---
@svg_all_router.post(path="/extract-all-shapes-s3/",
                     responses={200: {}, 500: {}, 503: {}},
                     status_code=status.HTTP_200_OK,
                     response_class=Response,
                     tags=["SVG Parsing - Extract all shapes as JSON data", "S3"],
                     summary="Extract shapes in JSON format.")
async def extract_all_shapes_data_json_s3(files_data: ExtractAllShapesFilesDataS3) -> Response:
    # ________________________________________________________________________________
    # --- INIT S3FileOps INSTANCE ---
    s3 = S3FileOps(s3_bucket_name=files_data.s3_bucket_name)

    # --- DOWNLOAD PDF FILE BYTES FROM AWS S3 ---
    pdf_file_bytes = s3.get_pdf_file_obj_bytes(s3_file_key=files_data.files.pdf_file.file_key)
    logger.info("- 1 - DOWNLOADED PDF FILE FROM AWS S3 -")

    # ________________________________________________________________________________
    # --- EXTRACT ALL SHAPES DATA ---
    all_svg = SVGParser.extract_all_svg(pdf_file_obj=pdf_file_bytes,
                                        config=settings.SVG_ELEMENTS_EXTRACTION,
                                        page_num=files_data.page_num,
                                        round_threshold=settings.ROUND_THRESHOLD,
                                        s3_origin=True)
    logger.info("- 2 - EXTRACTED ALL SHAPES FROM PDF FILE -")

    # --- DELETE SVG SIZE FROM JSON (OPTIONAL) ---
    if not files_data.return_svg_size:
        for key, value in all_svg.items():
            del value["svg_width"]
            del value["svg_height"]
        logger.info("- 3.1 - REMOVED SVG SIZE FROM JSON -")

    # --- DELETE ATTRIBUTES FROM JSON (OPTIONAL) ---
    if not files_data.return_attributes:
        for key, value in all_svg.items():
            if 'attributes' in value:
                del value["attributes"]
            else:
                del value['lines_attributes']
        logger.info("- 3.2 - REMOVED ATTRIBUTES FROM JSON -")

    # ________________________________________________________________________________
    # --- UPLOAD FILE TO AWS S3 BUCKET ---
    try:
        logger.info("- 4.1 - UPLOADING JSON FILES WITH ALL SHAPES DATA TO AWS S3 -")
        for shape_name, json_file_key in files_data.out_files.dict().items():
            shape_dict = all_svg[shape_name]
            s3.upload_json_file_to_bucket(s3_file_key=json_file_key,
                                          json_data=shape_dict)

        return Response(status_code=status.HTTP_200_OK)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"ERROR -> Raised EXCEPTION during failed upload of the file to S3.")
