FROM phusion/baseimage

CMD ["/sbin/my_init"]
RUN apt-get update && install_clean wget bzip2 unzip xvfb libxrender1 \
    libxtst6 libxi6 libglib2.0-dev xterm x11vnc
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
    add-apt-repository -y ppa:webupd8team/java && \
    apt-get update && install_clean oracle-java8-installer

# Install IB Gateway: Installs to ~/Jts
RUN wget https://download2.interactivebrokers.com/installers/ibgateway/latest-standalone/ibgateway-latest-standalone-linux-x64.sh && \
    chmod a+x ibgateway-latest-standalone-linux-x64.sh && \
    mv ibgateway-latest-standalone-linux-x64.sh ~ && \
    cd ~ && \
    (echo n | ./ibgateway-latest-standalone-linux-x64.sh) && \
    rm ibgateway-latest-standalone-linux-x64.sh
# n = answer "no" to whether the gateway should start immediately

# Install IB Controller: Installs to ~/IBController
RUN wget https://github.com/ib-controller/ib-controller/releases/download/3.4.0/IBController-3.4.0.zip && \
    unzip IBController-3.4.0.zip -d ~/IBController && \
    chmod -R 777 ~/IBController && \
    rm IBController-3.4.0.zip

# Install IB API.
RUN install_clean python3-setuptools python3-wheel python3-pip && \
    wget http://interactivebrokers.github.io/downloads/twsapi_macunix.973.07.zip && \
    unzip twsapi_macunix.973.07.zip && \
    cd IBJts/source/pythonclient && \
    python3 setup.py bdist_wheel && \
    python3 -m pip install --user --upgrade dist/ibapi-9.73.7-py3-none-any.whl

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
