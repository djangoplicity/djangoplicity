from typing import TypedDict, List, Optional


ArchiveResource = TypedDict('ArchiveResource', {
    "ResourceType": str, 
    "MediaType": str, 
    "URL": str, 
    "FileSize": Optional[int],
    "Dimensions": Optional[List[int]],
    "ProjectionType": Optional[str],
})
