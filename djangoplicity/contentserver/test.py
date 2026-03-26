import os
import tempfile
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from unittest.mock import patch, MagicMock
from djangoplicity.contentserver.models import ContentServerResource
from djangoplicity.contentserver.base import S3ContentServer
from djangoplicity.contentserver.tasks import cleanup_old_local_resources


class ContentServerCleanupTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_content_type = ContentType.objects.get_for_model(ContentServerResource)
        
        # Create test files with different timestamps
        self.old_date = timezone.now() - timedelta(weeks=5) 
        self.recent_date = timezone.now() - timedelta(weeks=2)  
        
        self.s3_server = 'AWS_S3'

        self.old_resource = ContentServerResource.objects.create(
            content_type=self.test_content_type,
            object_id='test123',
            format='original',
            extension='tif',
            resource_size=1024,
            content_server=self.s3_server,
            content_server_path=os.path.join(self.temp_dir, 'models3d', 'original', 'imagen123.tif'),
            is_directory=False,
            created_at=self.old_date,
            updated_at=self.old_date
        )
        
        self.recent_resource = ContentServerResource.objects.create(
            content_type=self.test_content_type,
            object_id='test456',
            format='screen',
            extension='jpg',
            resource_size=512,
            content_server=self.s3_server,
            content_server_path=os.path.join(self.temp_dir, 'images', 'screen', 'imagen456.jpg'),
            is_directory=False,
            created_at=self.recent_date,
            updated_at=self.recent_date
        )

        ContentServerResource.objects.filter(id=self.old_resource.id).update(
            created_at=self.old_date,
            updated_at=self.old_date
        )
        self.old_resource.refresh_from_db()

        ContentServerResource.objects.filter(id=self.recent_resource.id).update(
            created_at=self.recent_date,
            updated_at=self.recent_date
        )
        self.recent_resource.refresh_from_db()

        os.makedirs(os.path.dirname(self.old_resource.content_server_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.recent_resource.content_server_path), exist_ok=True)
        
        with open(self.old_resource.content_server_path, 'w') as f:
            f.write('test old content')
        
        with open(self.recent_resource.content_server_path, 'w') as f:
            f.write('test recent content')
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cleanup_old_resources_deletes_files(self):
        """Test that old resources are deleted from disk"""
        self.assertTrue(os.path.exists(self.old_resource.content_server_path))
        self.assertTrue(os.path.exists(self.recent_resource.content_server_path))

        deleted_count = cleanup_old_local_resources(weeks=4)
        
        self.assertFalse(os.path.exists(self.old_resource.content_server_path))
        self.old_resource.refresh_from_db()
        
        self.assertTrue(os.path.exists(self.recent_resource.content_server_path))
        self.recent_resource.refresh_from_db()
        
        self.assertEqual(deleted_count, 1)
    
    def test_cleanup_with_non_s3_server_skips_resource(self):
        """Test that resources with non-S3 servers are skipped"""
        old_resource_non_s3 = ContentServerResource.objects.create(
            content_type=self.test_content_type,
            object_id='test789',
            format='original',
            extension='png',
            resource_size=256,
            content_server='non_s3_server',
            content_server_path=os.path.join(self.temp_dir, 'video', 'original', 'imagen789.png'),
            is_directory=False,
            created_at=self.old_date,
            updated_at=self.old_date
        )
        
        # Create file
        os.makedirs(os.path.dirname(old_resource_non_s3.content_server_path), exist_ok=True)
        with open(old_resource_non_s3.content_server_path, 'w') as f:
            f.write('test content')
        
        deleted_count = cleanup_old_local_resources(weeks=4)
        
        self.assertTrue(os.path.exists(old_resource_non_s3.content_server_path))
        old_resource_non_s3.refresh_from_db()
        self.assertTrue(old_resource_non_s3.is_active)
        
        self.assertEqual(deleted_count, 1)
    
    def test_cleanup_with_missing_file(self):
        """Test cleanup when file doesn't exist on disk"""
        os.remove(self.old_resource.content_server_path)
        
        deleted_count = cleanup_old_local_resources(weeks=4)
        
        self.old_resource.refresh_from_db()
        self.assertTrue(self.old_resource.is_active)
        
        self.assertEqual(deleted_count, 0)
    
    def test_cleanup_with_no_old_resources(self):
        """Test cleanup when there are no old resources"""
        # Update old resource to be recent
        self.old_resource.updated_at = timezone.now() - timedelta(weeks=2)
        self.old_resource.save()
        
        # Run cleanup
        deleted_count = cleanup_old_local_resources(weeks=4)
        
        # No files should be deleted
        self.assertEqual(deleted_count, 0)
        
        # Both resources should remain active
        self.old_resource.refresh_from_db()
        self.recent_resource.refresh_from_db()
        self.assertTrue(self.old_resource.is_active)
        self.assertTrue(self.recent_resource.is_active)
    
    def test_cleanup_different_archive_types(self):
        """Test cleanup works with different archive types (models3d, images, video, etc.)"""
        archive_types = ['pressrelease', 'video', 'news']
        resources = []
        
        for archive_type in archive_types:
            resource = ContentServerResource.objects.create(
                content_type=self.test_content_type,
                object_id=f'test_{archive_type}',
                format='thumbnail',
                extension='jpg',
                resource_size=128,
                content_server=self.s3_server,
                content_server_path=os.path.join(self.temp_dir, archive_type, 'thumbnail', f'test_{archive_type}.jpg'),
                is_directory=False,
            )
            ContentServerResource.objects.filter(id=resource.id).update(
                created_at=self.old_date,
                updated_at=self.old_date
            )
            resource.refresh_from_db()
            resources.append(resource)
            
            os.makedirs(os.path.dirname(resource.content_server_path), exist_ok=True)
            with open(resource.content_server_path, 'w') as f:
                f.write(f'test content for {archive_type}')
        
        deleted_count = cleanup_old_local_resources(weeks=4)
        
        for resource in resources:
            self.assertFalse(os.path.exists(resource.content_server_path))
        
        # Should delete 3 additional files plus the original old_resource
        self.assertEqual(deleted_count, 4)
