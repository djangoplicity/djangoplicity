from typing import TypedDict, Optional
from djangoplicity.media.models import Image, Video
from djangoplicity.archives.resources import ResourceManager


allImageFormatsTuplesList = []
for image_format in dir(Image.Archive):
    if not isinstance(getattr(Image.Archive, image_format), ResourceManager):
        continue
    allImageFormatsTuplesList.append((image_format, Optional[str]))

allVideoFormatsTuplesList = []
for video_format in dir(Video.Archive):
    if not isinstance(getattr(Video.Archive, video_format), ResourceManager):
        continue
    allVideoFormatsTuplesList.append((video_format, Optional[str]))


ImageFormatsURLs = TypedDict('ImageFormatsURLs', dict(allImageFormatsTuplesList))
VideoFormatsURLs = TypedDict('VideoFormatsURLs', dict(allVideoFormatsTuplesList))
