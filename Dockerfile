FROM python:3-alpine

WORKDIR /usr/src/app

COPY . .
RUN pip install --no-cache-dir -r deploy-requirements.txt

ENV PATH /bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:/usr/src/app/bin
ENV PYTHONPATH /usr/src/app
CMD ["nat-conntracker"]
