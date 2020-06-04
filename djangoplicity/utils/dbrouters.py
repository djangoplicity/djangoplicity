import random

class DualDBRouter:
    '''
    Router that supports two databases: one master is read/write, and one
    slave is read only. Writes are always done on the master, and reads
    are done randomly on either
	'''
    def db_for_read(self, model, **hints):
        '''
        Pick a random database to read from
        '''
        return random.choice(['default', 'readonly'])

    def db_for_write(self, model, **hints):
        '''
        Writes always go to primary.
        '''
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default'
