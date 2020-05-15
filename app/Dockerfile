FROM algo
ARG BUILD_PACKAGES="gcc libffi-dev linux-headers make musl-dev openssl-dev"
COPY requirements.txt /app/requirements.txt
RUN apk --no-cache add ${BUILD_PACKAGES} && \
    source .env/bin/activate && \
    python3 -m pip --no-cache-dir install -r app/requirements.txt && \
    apk del ${BUILD_PACKAGES}
COPY . app
RUN chmod 0755 /algo/app/run.sh
CMD [ "/algo/app/run.sh" ]
