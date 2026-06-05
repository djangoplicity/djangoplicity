from enum import Enum

class AccessTagControl(str, Enum):
    PRIVATE = 'Private'
    PUBLIC = 'Public'

ZOOMABLE_PRIVATE_TILE_GROUPS = ['TileGroup0', 'TileGroup1', 'TileGroup2', 'TileGroup3']
