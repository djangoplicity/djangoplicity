from pipeline.storage import PipelineMixin

from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class PipelineManifestStorage(PipelineMixin, ManifestStaticFilesStorage):
    '''
    pipeline.storage.PipelineCachedStorage causes problem as it fetches
    the hashes from the shared cache, meaning it can have different values
    if two servers with different static files are running at the same time
    (which can happen during deployment).
    To prevent that we provide this storage based on ManifestStaticFilesStorage
    '''
    manifest_strict = False
