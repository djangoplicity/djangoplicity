from enum import Enum

class AccessTagControl(str, Enum):
    PRIVATE = 'Private'
    PUBLIC = 'Public'

ZOOMABLE_PRIVATE_ZOOM_LEVELS = [0, 1, 2, 3]