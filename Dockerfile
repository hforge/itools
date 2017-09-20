FROM alpine:3.5

## Install global dependencies
RUN apk add --update \
    build-base \
    cmake \
    gcc \
    gettext \
    git \
    glib \
    glib-dev \
    jpeg-dev \
    libffi-dev \
    libmagic \
    linux-headers \
    nodejs \
    openssl \
    py-gobject \
    py-pip \
    python \
    python-dev \
    util-linux-dev \
    xz \
    zlib-dev

# Install gulp and less
RUN npm install -g gulp less

# Configure git user
RUN git config --global user.email "hforge@hforge.org"
RUN git config --global user.name "hforge"

# Install PIP
ADD https://bootstrap.pypa.io/get-pip.py /tmp/
WORKDIR /tmp/
RUN python2 get-pip.py
RUN pip install --upgrade pip

# INSTALL sphinx
RUN pip install sphinx

# Install xapian
ADD http://oligarchy.co.uk/xapian/1.4.2/xapian-core-1.4.2.tar.xz /tmp/
WORKDIR /tmp/
RUN tar Jxf /tmp/xapian-core-1.4.2.tar.xz
WORKDIR /tmp/xapian-core-1.4.2
RUN ./configure && make && make install

# Install xapian-bindings python
ADD http://oligarchy.co.uk/xapian/1.4.2/xapian-bindings-1.4.2.tar.xz /tmp/
WORKDIR /tmp/
RUN tar Jxf /tmp/xapian-bindings-1.4.2.tar.xz
WORKDIR /tmp/xapian-bindings-1.4.2
RUN ./configure --with-python && make && make install

# Install libgit2
ADD https://github.com/libgit2/libgit2/archive/v0.26.0.zip /tmp/
WORKDIR /tmp/
RUN unzip v0.26.0.zip
WORKDIR /tmp/libgit2-0.26.0
RUN mkdir build
WORKDIR /tmp/libgit2-0.26.0/build
RUN cmake ..
RUN cmake --build . --target install

# Set ENV to compile pillow (https://github.com/python-pillow/Pillow/issues/1763)
ENV LIBRARY_PATH=/lib:/usr/lib

# INSTALL libgit2 (https://github.com/python-pillow/Pillow/issues/1763)
RUN pip install pygit2==0.26.0

# Declare libgit2 (XXX We have to export lib direcory)
RUN ln -s /usr/local/lib/libgit2.so.26 /usr/lib/libgit2.so.26

# Install ikaaro dependencies
RUN mkdir -p /tmp/itools
ADD ./ /tmp/itools/
RUN pip install -r /tmp/itools/requirements.txt

# Install itools
WORKDIR /tmp/itools
RUN python setup.py install

# Install PIL (because it's not part of itools requirements)
RUN pip install pillow==3.0.0
