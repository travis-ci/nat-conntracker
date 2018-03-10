FROM python:3-alpine

WORKDIR /usr/src/app

COPY . .
RUN pip install --no-cache-dir -r deploy-requirements.txt

ENV PYTHONPATH /usr/src/app
CMD ["python", "-m", "nat_conntracker", "-"]
