FROM phusion/baseimage

CMD ["/sbin/my_init"]
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
    add-apt-repository -y ppa:webupd8team/java && \
    apt-get update && \
    apt-get upgrade -y && \
    install_clean wget bzip2 unzip xvfb libxrender1 \
    libxtst6 libxi6 libglib2.0-dev xterm x11vnc oracle-java8-installer \
    python3-setuptools python3-wheel python3-pip gtk2.0 lsof net-tools

# Copy over installation files downloaded by ./download.sh.
ADD tws-stable-standalone-linux-x64.sh /root/tws-stable-standalone-linux-x64.sh
ADD IBController-3.4.0.zip /root/IBController-3.4.0.zip
ADD twsapi_macunix.973.07.zip /root/twsapi_macunix.973.07.zip

# Install IB Trader Workstation: Installs to ~/Jts
RUN cd ~ && \
    chmod a+x tws-stable-standalone-linux-x64.sh && \
    (echo n | ./tws-stable-standalone-linux-x64.sh) && \
    rm tws-stable-standalone-linux-x64.sh
# n = answer "no" to whether should start immediately

# Install IB Controller: Installs to ~/IBController
RUN cd ~ && \
    unzip IBController-3.4.0.zip -d ~/IBController && \
    chmod -R 777 ~/IBController && \
    rm IBController-3.4.0.zip

# Install IB API.
RUN cd ~ && \
    unzip twsapi_macunix.973.07.zip && \
    cd IBJts/source/pythonclient && \
    python3 setup.py bdist_wheel && \
    python3 -m pip install --user --upgrade dist/ibapi-9.73.7-py3-none-any.whl && \
    cd ~ && \
    rm -r IBJts twsapi_macunix.973.07.zip

RUN rm ~/IBController/**/*.bat

RUN mkdir /etc/service/xvfb
ADD xvfb.sh /etc/service/xvfb/run
RUN chmod +x /etc/service/xvfb/run

RUN mkdir /etc/service/x11vnc
ADD x11vnc.sh /etc/service/x11vnc/run
RUN chmod +x /etc/service/x11vnc/run

RUN mkdir /etc/service/ib_gateway
ADD ib_gateway.sh /etc/service/ib_gateway/run
RUN chmod +x /etc/service/ib_gateway/run

ADD read_snapshot.py /root/read_snapshot.py

# x11vnc
EXPOSE 5900/tcp
# port for ibc
#EXPOSE 4452/tcp
