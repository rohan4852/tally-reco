from pydantic import BaseModel
from typing import List

class FileParseInfo(BaseModel):
    file_type: str
    file_path: str
    sheet_name: str
    row_count: int
    column_count: int
    columns_found: List[str]
    missing_required_columns: List[str]
    warnings: List[str]

class ParseResponse(BaseModel):
    session_id: str
    message: str
    gst_file: FileParseInfo
    tally_file: FileParseInfo

class DataPreviewResponse(BaseModel):
    session_id: str
    file_type: str
    sheet_name: str
    row_count: int
    columns: List[str]
    preview_rows: List[dict]