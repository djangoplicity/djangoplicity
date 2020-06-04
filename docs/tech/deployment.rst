Deployment
==========

Following is an overview and guide to deployment of djangoplicity websites.

Anatomy of Deployment
---------------------
All djangoplicity websites have the same deployment structure, which is setup automatically by a deployment script. Following overview of the structure lists the most important directories of a deployment.

**Deployment Structure**
::

	docs/
	  static/
	    ...
	    djangoplicity/
	docs_maintenace/
	logs/
	projects/
	  djangoplicity/
	    <website>/
	      ...
	      conf/
	        crontab.txt
	        settings-integration.ini
	        settings-production.ini
	      fabfile.py
	      pavement.py
	      sql/
	virutalenv/
	  apache/
	    django.wsgi
	  bin/
	    ...
	    python
	    virtual_djangohandler.py
	    start_shell.sh
	  lib/
	    python2.5/
	      site-packages/
	        ...
	tmp/


Test
 * ``docs/static`` all static files for the project.
 * ``docs_maintenance`` is a the document root for a simple static website that can be enabled in case of maintenance work on the website.
 * ``logs`` and ``tmp`` are directories for logs files and temporary files respectively. Web server user must have write permission to these directories
 * ```virtual `
test

**pavement.py**

**fabfile.py**

Integration Deployment
----------------------

Database?

Run Fabric::

	source ~/Workspaces/sites/<site>/bin/start_shell.py
	fab integration_stop
	fab integration_stop_cron
	# Do DB upgrades here,
	fab integration
	# or here 
	fab integraton_start_cron
	fab integration_start
	
	
Production Deployment
---------------------

Database Deployment
-------------------
No good solution

- UTF8 (tables and fields!!!)
- permissions data for new applications.

To get production database onto integration database run::

	source ~/Workspaces/sites/pttu/bin/start_shell.py
	fab integration_db_replace


Integration/Production Environment Setup
----------------------------------------

**Server**

Directories

/home/web/pttu symbolic link to the right place.

**Setup**

Run Fabric::
	
	source ~/Workspaces/sites/pttu/bin/start_shell.py
	fab integration_setup


Apache Configuration
--------------------

apachectl
config/httpd.conf
config/extra/...

Static vs. dynamic

Apache slots:
	dynamic start all at once - keep alive off
	static does as normal
	
Proxy request to static to allow test of individual server

Load balancer (SSL termination,)

**Memcache**

Reinstalling a Python package
-----------------------------
ssh to aweb8
/home/web/<server-env>/virtualenv/bin/pip install --no-index -E /home/web/<server-env>/virtualenv/ -f http://www.djangoplicity.org/repository/packages/ -I <package>==<version>
The "<package>==<version>" part should be copied from the requirements.txt file.

The -I flag ensure that previous version of the package is ignore.

Troubleshooting package installation 
------------------------------------
The most common problem for a package to fail installation is because of an included library that needs to be compiled and which depends on
already installed libraries. Since most libraries are installed in /home/web/lib some packages fail to respect LD_LIBRARY_FLAGS and other
standard measures to tell where include and library directories are. In those cases, usually the setup.py file have to be edited and 
the package have to be repackaged. 


Clean Installation on Running Production Servers
------------------------------------------------
Following is a step-by-step guide to make a fresh production deployment without setting the production website in maintenance mode. This is for instance useful when doing a larger upgrades of Python packages or Django itself. It however requires that the the old and the new installation can run off the same database without any problems - thus any database upgrades cannot break the old installation.

The method shutdowns one production server and uses it for the installation and upgrade. Once the server has been updated, it's set back in production, while the other server is taken out of service and upgrade.

IMPORTANT: Check configuration, log and temporary files that should also be transferred to the new deployment. E.g. for spacetelescope virtualenv/etc/coposweb.ini and logs/orderid.txt must be transferred as well.

Example variables::
		<projectname> : spacetelescope
		<env> : integration|production
		<server-env> : hubble|hubblei
		<server1> : hubble1|hubble1i
		<server2> : hubble2|hubble2i
		<servername> : hubble
		<import-env> : import|importi

1. Start develop shell and stop cron job (local)::

		source ~/Workspaces/sites/<projectname>/virtualenv/bin/start_shell.sh
		fab <env>_stop_cron

 2. Create directory for old deploy (local)::

		cd /Volumes/webdocs/
		mkdir <server-env>_old

 3. Stop server 1 and make it point to old deployment (remote)::

		ssh web@<server1>
		sudo /etc/init.d/http.<servername>.main stop
		sudo /etc/init.d/http.<servername>.static stop
		cd /home/web/
		rm -f <servername>
		ln -s A/<server-env>_old <servername>

 4. Move old deployment into separate directory, and symlink back so server 2 still can run (remote)::

		ssh lchriste@<server1>
		cd /home/web/A/<server-env>
		mv docs ../<server-env>_old/; ln -s ../<server-env>_old/docs docs
		
		# Test if <server2> is still running (just in case something is not right)
		
		mv docs_maintenance ../<server-env>_old/; ln -s ../<server-env>_old/docs_maintenance docs_maintenance
		mv projects ../<server-env>_old/; ln -s ../<server-env>_old/projects projects
		mv virtualenv ../<server-env>_old/; ln -s ../<server-env>_old/virtualenv virtualenv
		mv logs ../<server-env>_old/; ln -s ../<server-env>_old/logs logs
		mv tmp ../<server-env>_old/; ln -s ../<server-env>_old/tmp tmp
		mv import ../<server-env>_old/; ln -s /home/web/A/<import-env> import

 5. Start server 1 again using old deployment (remote)::

		ssh web@<server1>
		sudo /etc/init.d/http.<servername>.main start
		sudo /etc/init.d/http.<servername>.static start
		
		# Test if <server1> is running

 6. Shutdown server 2 (remote)::

		ssh web@<server2>
		sudo /etc/init.d/http.<servername>.main stop
		sudo /etc/init.d/http.<servername>.static stop
		
		# Test if www.<domain> is running

 7. Prepare server 2 for new deployment (remote)::

		ssh lchriste@<server2>
		cd /home/web/<server-env>/
		rm docs
		rm docs_maintenance
		rm import
		rm projects
		rm virtualenv
		rm logs
		rm tmp

 8. Deploy on server 2 (local)::

		source ~/Workspaces/sites/<projectname>/virtualenv/bin/start_shell.sh
		fab <env>_setup
		fab <env>_relocate_virtualenv

 9. Manually edit ``/Volumes/webdocs/<server-env>/virtualenv/apache/django.wsgi`` (replace settings-<host>.ini with settings-production.ini)

 10. Merge old and new static files (remote)::

		ssh lchriste@<server2>
		cd /home/web/A/<server-env>
		mv docs docs_new
		cd /home/web/A/<server-env>_old
		mv docs ../<server-env>/;ln -s ../<server-env>/docs docs
		cd /home/web/<server-env>/
		rsync -av docs_new/ docs/

 11. Fix permission on directories to ensure they are writable (local)::

		source ~/Workspaces/sites/<projectname>/virtualenv/bin/start_shell.sh
		fab <env>_fix_perms

 12. Start server 2 (remote)::

		ssh web@<server2>
		sudo /etc/init.d/http.<servername>.static start
		sudo /etc/init.d/http.<servername>.main start
		exit
		
 13. Apply SQL 

 12. Stop server 1, point it to new deployment and start it again  (remote)::

		ssh web@<server1>
		sudo /etc/init.d/http.<servername>.main stop
		sudo /etc/init.d/http.<servername>.static stop
		cd /home/web/
		rm -f <servername>
		ln -s A/<server-env> <servername>
		sudo /etc/init.d/http.<servername>.static start
		sudo /etc/init.d/http.<servername>.main start
		
 13. Start cron job (local)::

		source ~/Workspaces/sites/<projectname>/virtualenv/bin/start_shell.sh
		fab <env>_start_cron

 14. Remove temporary directories and old deployment (remote)::

		ssh lchriste@<server1>
		cd /home/web/<server-env>/
		rm -Rf docs_new
		cd /home/web/A/<server-env>_old/
		rm docs
		rm import
		rm -Rf *

 15. Remove old deployment directory (local)::

		cd /Volumes/webdocs/
		rmdir  <server-env>_old
		
		
		
		
		
===================
Troubleshooting

Cannot stop/start server:

E.g:
$ fab production_stop
[pttu2] Executing task 'production_stop'
[pttu2] sudo: /etc/init.d/http.pttu.main stop
Password for web@pttu2: 
[pttu2] out: 20265: No such process
[pttu2] out: Null message body; hope that's ok
[pttu2] out: http.pttu.main : /home/web/server/apache/http.pttu.main/stop failed on aweb24
[pttu2] out: portaltotheuniverse.org Web Server daemon killed !
[pttu1] Executing task 'production_stop'
[pttu1] sudo: /etc/init.d/http.pttu.main stop
[pttu1] out: 14598: No such process
[pttu1] out: Null message body; hope that's ok
[pttu1] out: http.pttu.main : /home/web/server/apache/http.pttu.main/stop failed on aweb23
[pttu1] out: portaltotheuniverse.org Web Server daemon killed !


Memcache pid is not correct in log file - go to each server and do:

ssh web@pttu1
cd /home/web/server/apache/http.pttu.main/logs/; rm -f memdpid; echo `ps axf | grep memcache | grep pttu | awk '{print $1}'` > memdpid