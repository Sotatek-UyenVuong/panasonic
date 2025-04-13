# File: error_codes.py

from enum import Enum

class ErrorCode(Enum):
    AUDIO_PROCESS_ERR = 460
    YT_PROCESS_ERR = 461
    INV_YT_URL = 462
    YT_CREDIT_ERR = 463
    YT_CREDIT_USE_ERR = 464
    INV_WEB_URL = 462
    WEB_CREDIT_ERR = 463
    INV_AUDIO = 465
    AUDIO_LENGTH_ERR = 466
    NO_RECORDING_CREDIT = 467
    NO_AUDIO_CREDIT = 468
    NO_UPLOAD_CREDIT = 468
    FILE_SIZE_ERR = 469
    NO_INPUT = 470
    SERVER_ERROR = 500
    DB_ERR = 471
    NOTE_404 = 472
    NO_SUMMARY = 473
    NO_TRANSCRIPT = 474
    TASK_CREATE_ERR = 475
    SERVER_ERR = 476  # Added
    UPDATE_FAILED = 477  # Added
    YT_LENGTH_ERR = 478 # Added
    TIME_OUT = 408
    # Thêm các mã lỗi mới cho quá trình tải lên
    UPLOAD_NOT_FOUND = 480
    CHUNK_ALREADY_UPLOADED = 481
    INCOMPLETE_UPLOAD = 482
    INTERNAL_SERVER_ERROR = 500
    # Thêm mã lỗi cho referral
    REFERRAL_NOT_FOUND = 490
    REFERRAL_SELF_USE = 491 
    REFERRAL_ALREADY_USED = 492
    REFERRAL_TIME_EXPIRED = 493
    REFERRAL_CREDIT_ERR = 494
    REFERRAL_UPDATE_ERR = 495
    # Thêm mã lỗi cho user
    USER_NOT_FOUND = 404
    
    SHORTS_CREDIT_ERR = 496

def get_error_code(error_key: str) -> int:
    try:
        return ErrorCode[error_key].value
    except KeyError:
        return 400
