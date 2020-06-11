testCoverage:
	docker exec -it djangoplicity-web pytest tests --cov=djangoplicity

testPython27:
	tox -e py27-django111
