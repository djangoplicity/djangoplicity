bash:
	docker exec -it djangoplicity bash

createsuperuser:
	docker exec -it djangoplicity ./manage.py createsuperuser

test:
	docker exec -it djangoplicity coverage run --source='.' manage.py test
	docker exec -it djangoplicity coverage html
	open ./htmlcov/index.html

coverage-html:
	docker exec -it djangoplicity coverage html
	open ./htmlcov/index.html

test-python27:
	tox -e py27-django111
