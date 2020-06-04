Development Environment
=======================

Getting a complete development environment setup for any djangoplicity website involves:

 * Installing MySQL
 * Installing Python 2.7
 * Preparing Eclipse workspace area
 * Installing Eclipse 3.6
 * Setting up a virtual Python environment
 * Loading website database
 * Starting development server

Once you have setup the general website environment, you may need to perform some additional tasks specific for the website (please referrer to the documentation for the specific website).

Prerequisites
-------------
Before you start the installation, you need the following:

 * Mercurial SCM installed: http://mercurial.selenic.com/
 * Apple Developer Tools - i.e. XCode 4.2
 * a valid Mantis username and password.
 * long and short name for website you wanna work with (e.g portaltotheuniverse.org/pttu or astronomy2009.org/iya2009)

Installing MySQL (OS X)
-----------------------
All production/integration database servers are running MySQL 5.0.x, so the newest release of MySQL 5.0 should be used for development servers.
	
The easiest way to install MySQL is to grab an installation package from http://www.mysql.com. If you are installing the default installation package on OS X, you also need to add ``/usr/local/mysql/bin`` to your ``PATH`` environment variable (this is needed later to install the MySQL Python package). 

Note, that to install `MySQL-python` on OS X, the setup program needs to be able find ``mysql_config`` on your path (e.g. try to run ``which mysql_config`` to see if the program can be found, otherwise MySQL might not have been installed, or you need to add the MySQL ``bin/`` directory to your `PATH` environment variable). 

If you installed MySQL using the default OS X installation, you can start/stop MySQL using the following command::

  sudo /usr/local/mysql/support-files/mysql.server start
  sudo /usr/local/mysql/support-files/mysql.server stop

Note, it is recommended you don't set any root password for your local MySQL development server, but just ensure that the server only replies to requests on localhost. Some development scripts will not work unless you do this, since they assume there is no root password.

.. warning::
   If your Python installation is 32-bit, then you must use the 32-bit version of MySQL (e.g. Leopard). If you Python installation is 64-bit, then you must use the 64-bit version of MySQL (e.g. on Snow Leopard), otherwise the Python MySQL package will not compile.

Installing Python 2.7 (OS X)
----------------------------
The default installation image for Python on OS X is Universal Binary. This however can create a lot of problems installing Python modules, since not all libraries that the modules link with are Universal Binaries. You hence need to compile Python from source.

 1. Remove any previous Python installation in ``/Library/Frameworks/Python.framework``
 2. Download the latest source code - currently http://www.python.org/ftp/python/2.7/Python-2.7.tgz
 3. Unpack and go into the directory.
 4. Run::

	./configure --enable-framework=/Library/Frameworks/ --enable-ipv6
	make
	sudo make install
	
 5. Ensure that ``/Library/Frameworks/Python.framework/Versions/Current/bin`` is in you path.
	- Check it by ``which python``
	- If not, then add ``export PATH=/Library/Frameworks/Python.framework/Versions/Current/bin:$PATH`` to ``~/.profile``
 6. Install distribute (http://pypi.python.org/pypi/distribute)
	- Run:: 

		curl -O http://python-distribute.org/distribute_setup.py
		sudo python distribute_setup.py

	- Now you should have ``easy_install`` in the same location as in (4) - check with ``which easy_install``.
 7. Install pip 
 	- Run::
 		easy_install pip
 8. Run::
	  sudo pip install virtualenv==1.7
	  sudo pip install readline
	
 9. Install GNU GMP:
 	- Download and unarchive ftp://ftp.gmplib.org/pub/gmp-5.0.2/gmp-5.0.2.tar.bz2
 	- Run ./configure; make; sudo make install

Installing djangoplicity-paver
------------------------------
`Paver` is a Python-based build/distribution/deployment scripting tool along the lines of Make or Rake. What makes Paver unique is its integration with commonly used Python libraries. Common tasks that were easy before remain easy. 

`djangoplicity-paver` adds extra tasks to paver that allow easy automated setup of both development and production environments. To install it, you need the latest checkout from the Subversion repository.

 1. Checkout `djangoplicity-paver` from the Subversion repository::

	svn co --username=<username> http://svnhq30.hq.eso.org/p30/trunk/djangoplicity-paver djangoplicity-paver
	
 2. Go into directory and run install::

	cd djangoplicity-paver
	sudo python setup.py install
	
	This will install djangoplicity-paver into the standard Python site-packages.


Preparing Eclipse workspace area
--------------------------------
To ensure minimise the possibilities for errors it is important to ensure that both development, integration and production environments are as similar as possible. As a result, everybody should be using the same directory structure and location for workspaces etc.

 1. Create directory for Eclipse workspaces in ``~/Workspaces`` and ``~/Workspaces/pttu``.
 2. Create deployment directory in ``~/Workspaces/sites``.
 3. Create project specific Eclipse workspace and deployment directory in ``~/Workspaces/pttu`` and ``~/Workspaces/sites/pttu``.
		
Installing Eclipse 3.5
----------------------
In case you are on ESO, the easiest way to get Eclipse is using the prepackaged version in T:/ToolsTech/Software/Eclipse/. This distribution includes all plugins so you can skip down to step 4, and only perform the configuration part.

 1. Download and install Eclipse 3.5 JaveEE edition.
 2. Install the following standard plug-ins if not already installed:
      * Mylyn Task
      * Mylyn Focused UI
      * Web Developer Tools
      * Web Page Editor
      * JavaScript Developer Tools
 3. Install the following non-standard plug-ins:
      * PyDev for Eclipse 
          - Using update site http://pydev.sourceforge.net/updates/.
      * Subversive SVN Team Provider (Incubation), Subversive SVN Team Provider Localization (Incubation), Subversive SVN Integration for the Mylyn Project
          - Using update site http://download.eclipse.org/technology/subversive/0.7/update-site/, and
      * Subversive SVN Connectors, SVNKit 1.1.7, SVNKit 1.2.0, Native JavaHL 1.4 Implementation, Native JavaHL 1.5 Implementation
          - Using update site http://www.polarion.org/projects/subversive/download/eclipse/2.0/update-site/  
      * Mylyn Connector: Mantis
          - Using update site http://mylyn-mantis.sourceforge.net/eclipse/update/site.xml
 4. Setting up Mylyn Mantis connector:
	  * Go to Planning perspective.
	  * Add new task (through the new wizard)
		 - Press Add task repository.
		 - Use the following values:
		   - *Server:*  http://www.spacetelescope.org/bugs/api/soap/mantisconnect.php
           - *User ID/Password:* Use your Mantis username and password
		- Press validate settings
		- Press Cancel
      * Add new query.
		- Give it a name (e.g. ESO Mantis Bugtracker)
		- Select project (e.g. portaltotheiunverise.org)
  		- Select Filter: Myself, by prio.
		- Press Ok
	  * Go to Preferences > Team > SVN > Comment Templates, and change the commit comment template to::
	     
	     MANTIS ${connector.task.prefix}${task.key} (${task.status}): ${task.description}
	
 5. Setting up Subversion repository:
      * Add new SVN > Repository Location:
          - Use repository location ``svn://<username>@svnsrv.hq.eso.org/p30/`` where ``<username>`` is replaced with your Subversion username and password.
 6. Checkout projects from version control:
     * Checkout the following projects from repository above.
		- ``trunk/djangoplicity``
		- ``trunk/<website>`` where ``<website>``is the website you wanna work with.

Setting up a virtual Python environment
---------------------------------------
`Virtualenv` allows to create a virtual Python environment for the website, so that packages from one website doesn't conflict or interfere with packages from other websites. It is a very nice and easy way to isolate the code for the website.


 1. Make dir ``~/Workspaces/sites/<short website name>`` e.g. ``~/Workspaces/sites/pttu``
 1. Go to ``~/Workspaces/pttu/<website>``
 2. Run::

 	paver deploy_develop --prefix=/Users/<username>/Workspaces/sites/<short website name>

The normal command to start the virtual environment is::

	source ~/Workspaces/sites/<short website name>/virtualenv/bin/start_shell.sh
	
This script ensures that the virtual environment is activated and that all needed environment variables are exported. Also, an AppleScript can be made to allow fast starting of a shell::

	on run
		tell application "Terminal"
			activate
			tell application "System Events" to tell process "Terminal" to keystroke "t" using command down
			do script with command "source ~/Workspaces/sites/<short website name>/virtualenv/bin/start_shell.sh" in window 1
		end tell
	end run

Starting development server
---------------------------
Both development, integration and production servers must be able to locate their ``settings.ini`` file, otherwise they will not start. This is controlled by a number of factors:

 * The name of the ini-file:
    - If ``DJANGO_SETTINGS_INI`` environment variable is set, its value will be used as the ini-filename.
    - Otherwise, both ``settings-<hostname>.ini`` and ``settings.ini`` will be used in the order given. 
 * The path to search for the ini-file:
    - The main ``__init__.py`` (in ``src/<short website name>``) contains a dictionary ``PROJECT_BASES``. Each key is a hostname is associated with a list of paths. If your hostname exists in the dictionary, it will search each path in the list for the ini-filename. Otherwise it will search the list of paths for the key ``_default``.

Hence, you need to edit a couple of files before you can run.

 1. Edit settings:
	 - ``settings-<hostname>.ini`` (if it doesn't exists, then create it by copying from another development settings).
	 - ``<short website name>.__init__.PROJECT_BASES`` (add your hostname, and path to search)
	
	Note settings you might want to update include:
	 - [djangoplicity] All settings
	 - [database] All settings
	 - [gis] All settings
	 - [admins] All settings
	
	Also you may want to add a new user to ``fixtures/initial_data.json``
 2. Launch virtual environment as described above (using the ``start_shell.sh`` script).
 3. Ensure that the database server is running.
 4. Run::
      
      python src/pttu/manage.py validate

 5. If everything is fine, then run::
      
		python src/pttu/manage.py syncdb --noinput
		python src/pttu/manage.py runserver
		
		
Test mail server
----------------
In Python you can run a test mail server that will print all received mails to the standard output instead of sending them to the actually receiver. This is very handy way to test and validate mail sending.

To start the test mail server run the following command::

  python -m smtpd -n -c DebuggingServer localhost:1025

