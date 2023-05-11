TAG=7

build:
	docker build -t convert-document:$(TAG) .
	docker tag convert-document:$(TAG) convert-document:latest

#push:
#	docker push alephdata/convert-document:$(TAG)
#	docker push alephdata/convert-document:latest

shell: build
	docker run -ti -v $(PWD):/convert -p 3000:3000 convert-document bash

run: build
	docker run -p 3000:3000 --tmpfs /tmp --rm -ti convert-document

test:
	rm out.pdf
	curl -o out.pdf -F format=pdf -F 'file=@fixtures/agreement.docx' http://localhost:3000/convert