bash:
	docker exec -it djangoplicity bash

shell:
	docker exec -it djangoplicity ./manage.py shell

createsuperuser:
	docker exec -it djangoplicity ./manage.py createsuperuser

test:
	docker exec -it djangoplicity coverage run --source='.' manage.py test

coverage-html:
	docker exec -it djangoplicity coverage html
	open ./htmlcov/index.html

futurize-stage1:
	docker exec -it djangoplicity futurize --stage1 -w -n .

futurize-stage2:
	docker exec -it djangoplicity futurize --stage2 --nofix=newstyle -w -n .

test-python27:
	tox -e py27-django111

test-python37:
	tox -e py37-django111

test-python38:
	tox -e py38-django111
