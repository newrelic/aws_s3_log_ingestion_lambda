build:
	sam build --use-container

run: check-run-env
	sam local invoke "NewRelicLogIngestionFunction" -e $(TEST_FILE)

package: check-package-env
	sam package --output-template-file packaged.yml --s3-bucket $(BUCKET) --region $(REGION) 

deploy: check-deploy-env
	sam deploy --template-file packaged.yml --stack-name $(STACK_NAME) --region $(REGION) 

publish: check-publish-env
	sam publish --template packaged.yml --region $(REGION)

check-run-env:
ifndef LICENSE_KEY
	$(error LICENSE_KEY is undefined)
endif
ifndef TEST_FILE
	$(error TEST_FILE is undefined)
endif

check-package-env:
ifndef REGION
	$(error REGION is undefined)
endif
ifndef BUCKET
	$(error BUCKET is undefined)
endif

check-deploy-env:
ifndef REGION
	$(error REGION is undefined)
endif
ifndef STACK_NAME
	$(error STACK_NAME is undefined)
endif

check-publish-env:
ifndef REGION
	$(error REGION is undefined)
endif
