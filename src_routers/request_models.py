# >>>> </> STANDARD IMPORTS </>
# >>>> ********************************************************************************
from typing import Optional
# >>>> ********************************************************************************

# >>>> </> EXTERNAL IMPORTS </>
# >>>> ********************************************************************************
from pydantic import BaseModel
# >>>> ********************************************************************************


# ________________________________________________________________________________
class PDFFileAttrs(BaseModel):
    file_key: str


class JSONFileAttrs(BaseModel):
    file_key: str


# ________________________________________________________________________________
class SVGParsingFiles(BaseModel):
    pdf_file: PDFFileAttrs


class SVGParsingFilesDataS3(BaseModel):
    """
    - Data model for the request body of the SVG parsing endpoints that are integrated with AWS S3 file storage.
    """
    files: SVGParsingFiles
    s3_bucket_name: str = "drawer-ai-services-test-files"
    out_s3_file_key: str = "sample/file/path.json"

    page_num: Optional[int] = 0
    return_svg_size: bool = True
    return_attributes: bool = False

    class Config:
        schema_extra = {
            "files": {
                "pdf_file": {
                    "file_key": "sample/file/path.pdf"
                }
            },
            "s3_bucket_name": "drawer-ai-services-test-files",
            "out_s3_file_key": "sample/file/path.json",

            "page_num": 0,
            "return_svg_size": True,
            "return_attributes": False
        }


# ________________________________________________________________________________
class ExtractAllShapesFiles(BaseModel):
    pdf_file: PDFFileAttrs


class ExtractAllShapesOutFiles(BaseModel):
    lines:          str = "sample/file/path.json"
    cubic_lines:    str = "sample/file/path.json"
    quads:          str = "sample/file/path.json"
    circles:        str = "sample/file/path.json"
    rectangles:     str = "sample/file/path.json"


class ExtractAllShapesFilesDataS3(BaseModel):
    """
    - Data model for the request body of the SVG parsing endpoints that are integrated with AWS S3 file storage.
    """
    files: ExtractAllShapesFiles
    s3_bucket_name: str = "drawer-ai-services-test-files"
    out_files: ExtractAllShapesOutFiles

    page_num: Optional[int] = 0
    return_svg_size: bool = True
    return_attributes: bool = False

    class Config:
        schema_extra = {
            "files": {
                "pdf_file": {
                    "file_key": "sample/file/path.pdf"
                }
            },
            "s3_bucket_name": "drawer-ai-services-test-files",
            "out_s3_file_key": {
                "lines": "sample/file/path.json",
            },

            "page_num": 0,
            "return_svg_size": True,
            "return_attributes": False
        }
