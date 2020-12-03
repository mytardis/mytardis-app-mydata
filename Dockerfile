# Used for CI testing in .github/workflows/docker-tests.yml
FROM ubuntu:18.04 AS build

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

# Create runtime user
RUN mkdir -p /app && \
    groupadd -r -g 10001 app && \
    useradd -r -u 10001 -g 10001 -d /app app && \
    chown app:app -R /app

WORKDIR /app

# Install runtime packages
RUN apt-get -yqq update && \
    apt-get -yqq install --no-install-recommends \
        git \
        gcc \
        python3-pip \
        python3-dev \
        python3-setuptools \
        libldap2-dev \
        libsasl2-dev \
        libmagic-dev \
        libmagickwand-dev \
        libglu1-mesa-dev \
        libxi6 && \
    pip3 install --no-cache-dir --upgrade pip

# Clone MyTardis and MyData repos
RUN git clone --depth 1 --branch chunked-upload \
    https://github.com/mytardis/mytardis.git ./ && \
    git clone --depth 1 --branch chunked-upload \
    https://github.com/mytardis/mytardis-app-mydata.git ./tardis/apps/mydata/

COPY requirements.txt /app/tardis/apps/mydata/

# Install Python packages
RUN cat requirements-base.txt \
    requirements-test.txt \
    requirements-ldap.txt \
    tardis/apps/social_auth/requirements.txt \
    tardis/apps/mydata/requirements.txt \
    > /tmp/requirements.txt && \
    # Display packages
    sort /tmp/requirements.txt && \
    pip3 install --no-cache-dir -q -r /tmp/requirements.txt && \
    pip3 install codecov

COPY test.py /app/

RUN mkdir -p var/store
RUN chown -R app:app /app

USER app

CMD bash -c "python3 test.py test tardis/apps/mydata/tests && ([[ -v CODECOV_TOKEN ]] && codecov -X gcov --root tardis/apps/mydata -b master -c $GITHUB_SHA || true)"
