FROM python:3-alpine

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r deploy-requirements.txt

ENV PATH /bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:/app/bin
ENV PYTHONPATH /app
CMD ["nat-conntracker"]
