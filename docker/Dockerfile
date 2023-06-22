# DBMail Dockerfile
# Copyright (c) 2020-2023 Alan Hicks, Persistent Objects Ltd support@p-o.co.uk
# LICENSE GPL2+

FROM ubuntu:jammy AS build_base
LABEL org.opencontainers.image.authors="ahicks@p-o.co.uk" \
      org.opencontainers.image.url="https://dbmail.org/docs/docker-images/" \
      org.opencontainers.image.source="https://github.com/dbmail/dbmail/tree/master/docker" \
      org.opencontainers.image.licenses="GPL-2.0+" \
      org.opencontainers.image.title="DBMail-build-environment" \
      org.opencontainers.image.description="This image contains everything to build dbmail"

RUN apt update && \
    apt install -y build-essential \
                    libgmime-3.0-dev \
                    libzdb-dev \
                    libldap2-dev \
                    libmhash-dev \
                    libevent-dev \
                    libssl-dev \
                    libsieve2-dev

FROM build_base AS build
LABEL org.opencontainers.image.authors="ahicks@p-o.co.uk" \
      org.opencontainers.image.url="https://dbmail.org/docs/docker-images/" \
      org.opencontainers.image.source="https://github.com/dbmail/dbmail/tree/master/docker" \
      org.opencontainers.image.licenses="GPL-2.0+" \
      org.opencontainers.image.title="DBMail-build" \
      org.opencontainers.image.description="This image builds dbmail"

COPY . /dbmail

WORKDIR /dbmail

RUN ./configure \
      --with-ldap=/usr \
      --with-sieve=/usr
RUN make
RUN make install

FROM ubuntu:jammy
LABEL org.opencontainers.image.authors="ahicks@p-o.co.uk" \
      org.opencontainers.image.url="https://dbmail.org/docs/docker-images/" \
      org.opencontainers.image.source="https://github.com/dbmail/dbmail/tree/master/docker" \
      org.opencontainers.image.licenses="GPL-2.0+" \
      org.opencontainers.image.title="DBMail" \
      org.opencontainers.image.description="This image runs dbmail"

WORKDIR /

RUN apt update && \
    apt install -y libgmime-3.0-0 \
                    libzdb11 \
                    libldap-common \
                    libmhash2 libevent-2.1-7 \
                    libevent-pthreads-2.1-7 \
                    libssl3 \
                    libsieve2-1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/local/sbin/* /usr/local/sbin/
COPY --from=build /usr/local/lib/dbmail/* /usr/local/lib/dbmail/

COPY dbmail.conf /usr/local/etc/

COPY --chown=nobody:nogroup docker/logs/dbmail-imapd.log /var/log/dbmail/
COPY --chown=nobody:nogroup docker/logs/dbmail-imapd.err /var/log/dbmail/
COPY --chown=nobody:nogroup docker/run/dbmail-imapd.pid /var/run/dbmail/

COPY docker/docker-entry.sh /usr/local/sbin/docker-entry.sh

# dbmail-imapd
EXPOSE 143/tcp
EXPOSE 993/tcp

# dbmail-timsieved
EXPOSE 2000/tcp

# dbmail-pop3d
EXPOSE 110/tcp

# dbmail-lmtpd
EXPOSE 24/tcp

CMD ["/usr/local/sbin/docker-entry.sh"]
