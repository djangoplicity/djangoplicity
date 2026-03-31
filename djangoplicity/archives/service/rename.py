import os
import inspect

from django.apps import apps
from django.conf import settings
from django.db import connection, transaction
from django.contrib.contenttypes.models import ContentType


class FileRenameTracker:
    def __init__(self):
        self.renamed_files = []
    
    def add(self, old_path, new_path):
        self.renamed_files.append((old_path, new_path))
    
    def rollback(self):
        for old_path, new_path in self.renamed_files:
            if os.path.exists(new_path):
                try:
                    os.rename(new_path, old_path)
                except Exception as e:
                    print(f"Failed to rollback {new_path} to {old_path}: {e}")


class ArchiveRenameService:
    def rename(self, instance, new_pk, _internal=False):
        from djangoplicity.archives.base import cache_handler, post_rename

        tracker = FileRenameTracker()
 
        try:
            with transaction.atomic():
                old_pk = instance.pk
                self.validate(instance, new_pk)

                pk_info = self.get_pk(instance)
                fk_relations = self.get_fk_relations(instance)

                cache_handler(instance.__class__, created=False, instance=instance)

                self.rename_related_resources(instance, old_pk, new_pk)

                self.rename_translations(instance, old_pk, new_pk)

                self.rename_resources_safe(instance, new_pk, tracker)

                self.update_primary_key(pk_info, old_pk, new_pk)

                self.update_foreign_keys(fk_relations, old_pk, new_pk)

                self.update_admin_log(instance, old_pk, new_pk)

                # Get the new instance and update embargo/release tasks
                new_instance = instance.__class__.objects.get(pk=new_pk)

                new_instance.set_embargo_date_task()
                new_instance.set_release_date_task()
                new_instance.save()

                post_rename.send(
                    sender=instance.__class__,
                    old_pk=old_pk,
                    new_pk=new_pk,
                )

                return new_instance

        except Exception as e:
            tracker.rollback()
            raise ValueError(f"Error renaming instance: {e}")

    
    def validate(self, instance, new_pk):
        if instance.__class__.objects.filter(pk=new_pk).exists():
            raise ValueError("PK already exists")
        
        if instance.pk == new_pk:
            raise ValueError("Same PK")
    
    def get_pk(self, instance):
        if getattr(instance.Archive.Meta, 'auto_detect_pk_fks', False):
            db_table_name = instance._meta.db_table
            pk_name = instance._meta.pk.name
            return db_table_name, pk_name
        
        return instance.Archive.Meta.rename_pk

    def get_fk_relations(self, instance):
        if getattr(instance.Archive.Meta, 'auto_detect_pk_fks', False):
            relations = set()

            for model in apps.get_models():
                for field in model._meta.get_fields():
                    if (
                        field.is_relation and
                        field.many_to_one and
                        field.related_model == instance.__class__ and
                        hasattr(field, 'attname')
                    ):
                        table_name = model._meta.db_table
                        column_name = field.attname

                        relations.add((table_name, column_name))

            return list(relations)

        return instance.Archive.Meta.rename_fks
    
    # Get list of related resources and rename them, this has to be done
    # before we update the keys in the DB
    def rename_related_resources(self, instance, old_pk, new_pk):
        from djangoplicity.archives.base import ArchiveModel

        def get_related(x):
            return x.startswith('related_') or x in ('image', 'video', 'comparison')
        
        for related_resource in filter(get_related, dir(instance)):
            related_resource = getattr(instance, related_resource)
            
            if not related_resource:
                continue
            
            #  Check if the attribute is an ArchiveModel (like for POTW)
            #  or a ManytoMany (PR, Ann, etc.)
            if isinstance(related_resource, ArchiveModel):
                related_resources = [related_resource]
            else:
                related_resources = related_resource.all()
            
            for resource in related_resources:
                if not resource.pk.startswith(old_pk):
                    continue
                
                # Generate destination pk:
                destpk = resource.pk.replace(old_pk, new_pk, 1)
                
                # Make sure that the destination pk doesn't already exist:
                if resource.__class__.objects.filter(pk=destpk).exists():
                    raise ValueError(f"Related object PK already exists: {destpk}")
                
                self.rename(resource, destpk, _internal=True)
        
    def rename_translations(self, instance, old_pk, new_pk):
        if ( settings.USE_I18N and hasattr(instance, 'Translation') and instance.is_source() ):
            
            translations = instance.get_translations(filter_kwargs={})['translations']

            for _lang, translation in translations.items():
                if not translation.pk.startswith(old_pk):
                    continue
                
                destpk = translation.pk.replace(old_pk, new_pk, 1)
                
                # Make sure that the destination pk doesn't already exist:
                if translation.__class__.objects.filter(pk=destpk).exists():
                    raise ValueError(f"Related object PK already exists: {destpk}")
                
                module = inspect.getmodule(translation)
                proxymodel_name = '%sProxy' % translation.__class__.__name__
                
                if not hasattr(module, proxymodel_name):
                    continue
                
                proxymodel = getattr(module, proxymodel_name)
                
                # Rename translation
                proxymodel = getattr(module, proxymodel_name)
                proxytranslation = proxymodel.objects.get(pk=translation.pk)

                # Recursive
                self.rename(proxytranslation, destpk, _internal=True)
    
    def rename_resources_safe(self, instance, new_pk, tracker):
        resource_names = [
            name for name, type_ in vars(instance.Archive).items()
            if hasattr(type_, 'get_resource_for_instance')
        ]

        for rname in resource_names:
            try:
                self._rename_resource_safe(instance, rname, new_pk, tracker)
            except Exception:
                continue
    
    def _rename_resource_safe(self, instance, resoruce_name, new_pk, tracker):
        if ( settings.USE_I18N and hasattr( instance, 'Translation') and instance.is_translation() ):
            return
        
        resource = getattr(instance, "resource_%s" % resoruce_name)

        if not resource:
            return
        
        old_path = getattr(resource, "path", None)

        # Check if the path exists
        if not old_path or not os.path.exists(old_path):
            return
        
        dirname = os.path.dirname(old_path)
        _, ext = os.path.splitext(old_path)
        new_path = os.path.join(dirname, f"{new_pk}{ext}")

        try:
            os.rename(old_path, new_path)
            tracker.add(old_path, new_path)
        except Exception as e:
            print(f"[WARN] Resource rename failed: {e}")
            pass
    
    
    def update_content_server_resources(self, instance, old_pk, new_pk):
        from djangoplicity.contentserver.models import ContentServerResource
        
        resources = ContentServerResource.objects.filter(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=old_pk
        )
        
        for resource in resources:
            resource.object_id = new_pk
            resource.save()

    # ------ SQL Operations ------ #
    def update_primary_key(self, pk_info, old_pk, new_pk):
        table, key = pk_info
        
        sql = f'UPDATE "{table}" SET "{key}"=%s WHERE "{key}"=%s'
        if connection.vendor == 'mysql':
            sql = f'UPDATE `{table}` SET `{key}`=%s WHERE `{key}`=%s'

        with connection.cursor() as cursor:
            cursor.execute(sql, [new_pk, old_pk])
    
    def update_foreign_keys(self, fk_relations, old_pk, new_pk):
        tables = connection.introspection.table_names()

        with connection.cursor() as cursor:
            for table, key in fk_relations:
                if table not in tables:
                    continue

                sql = f'UPDATE "{table}" SET "{key}"=%s WHERE "{key}"=%s'
                if connection.vendor == 'mysql':
                    sql = f'UPDATE `{table}` SET `{key}`=%s WHERE `{key}`=%s'

                cursor.execute(sql, [new_pk, old_pk])
    
    def update_admin_log(self, instance, old_pk, new_pk):
        content_type = ContentType.objects.get_for_model(instance)

        sql = """
            UPDATE django_admin_log
            SET object_id=%s
            WHERE object_id=%s AND content_type_id=%s
        """

        if connection.vendor == 'mysql':
            sql = """
                UPDATE django_admin_log
                SET object_id=%s
                WHERE object_id=%s AND content_type_id=%s
            """

        with connection.cursor() as cursor:
            cursor.execute(sql, [new_pk, old_pk, content_type.pk])

