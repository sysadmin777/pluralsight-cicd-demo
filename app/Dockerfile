# Pinned base image by tag; for maximum rigor you can pin by digest too:
# FROM public.ecr.aws/lambda/python:3.12@sha256:<digest>
FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt -t ${LAMBDA_TASK_ROOT}

COPY app.py ${LAMBDA_TASK_ROOT}/

CMD ["app.handler"]
