bash:
	docker exec -it djangoplicity bash

test:
	docker exec -it djangoplicity coverage run --source='.' manage.py test

coverage-html:
	docker exec -it djangoplicity coverage html
	open ./htmlcov/index.html

futurize-stage1:
	docker exec -it djangoplicity futurize --stage1 -w -n .

futurize-stage2:
	docker exec -it djangoplicity futurize --stage2 -w -n .

test-python27:
	tox -e py27-django111
