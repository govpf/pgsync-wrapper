FROM govpf/pgsync:2.1.2

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .
ENV PORT 5000
COPY docker/docker-entrypoint.sh /app/
ENTRYPOINT [ "/app/docker-entrypoint.sh" ]
