TAG=7

build:
	docker build -t convert-document:$(TAG) .
	docker tag convert-document:$(TAG) convert-document:latest

#push:
#	docker push alephdata/convert-document:$(TAG)
#	docker push alephdata/convert-document:latest

shell: build
	docker run --name document -ti -v $(PWD):/convert convert-document bash

run: build
	docker run --name document -p 3000:3000 --tmpfs /tmp --rm -ti convert-document
