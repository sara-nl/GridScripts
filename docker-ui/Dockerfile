# Dockerfile to create a container with the UMD UI service
#
# Built the container by:
# docker build -t umd-ui .
#
# Run it by:
# docker run -it <id> startui


FROM centos:7
MAINTAINER Ron Trompert <ron.trompert@surfsara.nl>
LABEL version="0.1"
LABEL description="Container image to run the UMD UI service."
USER root
WORKDIR /root
RUN rm -f /etc/yum.repos.d/UMD-* /etc/yum.repos.d/epel-*
RUN  rpm --import http://repository.egi.eu/sw/production/umd/UMD-RPM-PGP-KEY
RUN yum install -y http://repository.egi.eu/sw/production/umd/4/centos7/x86_64/updates/umd-release-4.1.3-1.el7.centos.noarch.rpm
RUN yum install -y epel-release wget
RUN wget http://repository.egi.eu/sw/production/cas/1/current/repo-files/egi-trustanchors.repo -O /etc/yum.repos.d/egi-trustanchors.repo
RUN yum install -y ui
RUN yum update -y

RUN mkdir .globus
COPY ./userkey.pem /root/.globus/userkey.pem
RUN chmod 600 /root/.globus/userkey.pem
COPY ./usercert.pem /root/.globus/usercert.pem
RUN chmod 644 /root/.globus/usercert.pem
COPY ./x509up_u0 /tmp/x509up_u0
RUN chmod 600 /tmp/x509up_u0

# Replace myvo.eu with your VO name
#------------8<-------------

RUN mkdir /etc/grid-security/vomsdir/myvo.eu

# You can look up the necessary information on your VO at:
# https://operations-portal.egi.eu/vo/search#VOV_section

COPY voms.grid.sara.nl.lsc /etc/grid-security/vomsdir/myvo.eu/voms.grid.sara.nl.lsc

RUN mkdir /etc/vomses

COPY myvo.eu-voms.grid.sara.nl /etc/vomses/myvo.eu-voms.grid.sara.nl
#------------8<-------------

# Make sure that your firewall lets the port range below through. If this is 
# not the case, then use passive gridftp.
EXPOSE 20000-25000
ENV GLOBUS_TCP_PORT_RANGE 20000,25000

COPY ./startui.sh /root
ENTRYPOINT ["/root/startui.sh"]
CMD ["startui"]
