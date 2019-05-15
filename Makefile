init:
	pipenv install --dev

test:
	coverage run setup.py test