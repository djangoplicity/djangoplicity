bash:
	docker exec -it djangoplicity bash

test:
	docker exec -it djangoplicity coverage run --source='.' manage.py test

coverage-html:
	docker exec -it djangoplicity pytest tests --cov=djangoplicity

test-python27:
	tox -e py27-django111
