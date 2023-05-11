FROM ubuntu:22.04
ENV DEBIAN_FRONTEND noninteractive

LABEL org.opencontainers.image.title = "document converter"
LABEL org.opencontainers.image.licenses = MIT
LABEL org.opencontainers.image.source = https://github.com/jayvyanl/convert-document

RUN apt-get -qq -y update \
    && apt-get install -y -qq ca-certificates \
    && echo '''deb https://mirrors.ustc.edu.cn/ubuntu/ jammy main restricted universe multiverse\n\
# deb-src https://mirrors.ustc.edu.cn/ubuntu/ jammy main restricted universe multiverse\n\
deb https://mirrors.ustc.edu.cn/ubuntu/ jammy-security main restricted universe multiverse\n\
# deb-src https://mirrors.ustc.edu.cn/ubuntu/ jammy-security main restricted universe multiverse\n\
deb https://mirrors.ustc.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse\n\
# deb-src https://mirrors.ustc.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse\n\
deb https://mirrors.ustc.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse\n\
''' > /etc/apt/sources.list \
    && apt-get -qq -y update \
    && apt-get install -y -qq --no-install-recommends libreoffice \
    && apt-get install -y -qq default-jre libreoffice-java-common \
    curl python3-pip python3-uno \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && groupadd -g 1000 -r app \
    && useradd -m -u 1000 -d /tmp -s /bin/false -g app app \
    && mkdir -p /convert

COPY requirements.txt /convert
RUN pip3 install --no-cache-dir -q -r /convert/requirements.txt -i https://mirrors.ustc.edu.cn/pypi/web/simple
COPY DENG.TTF /usr/share/fonts
COPY convert /convert/convert
USER app
WORKDIR /convert

HEALTHCHECK --interval=10s --timeout=10s --retries=100 \
    CMD curl -f http://localhost:3000/healthy || exit 1

# Default API port.
EXPOSE 3000
CMD ["gunicorn", \
    "-w", "4", \
    "--bind", "0.0.0.0:3000", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--timeout", "84600", \
    "convert.app:app"]
