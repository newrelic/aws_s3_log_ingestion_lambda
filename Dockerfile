FROM public.ecr.aws/lambda/python:3.8

COPY ./src/ ${LAMBDA_TASK_ROOT}
COPY ./requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip3 install -r ${LAMBDA_TASK_ROOT}/requirements.txt --target "${LAMBDA_TASK_ROOT}"

CMD [ "handler.lambda_handler" ]
