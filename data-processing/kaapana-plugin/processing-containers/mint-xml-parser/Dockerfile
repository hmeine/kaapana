FROM local-only/base-python-cpu:latest

LABEL IMAGE="mint-xml-parser"
LABEL VERSION="0.1.0"
LABEL CI_IGNORE="True"

# Install OpenJDK-8
RUN apt-get update && \
    apt-get install -y openjdk-11-jre && \
    apt-get install -y ant && \
    apt-get clean;

# Setup JAVA_HOME -- useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64/
RUN export JAVA_HOME

RUN curl 'https://kumisystems.dl.sourceforge.net/project/saxon/Saxon-HE/11/Java/SaxonHE11-4J.zip' -o saxon.zip
RUN unzip saxon.zip -d saxon

COPY files/* /kaapanasrc/
CMD ["python3","-u","/kaapanasrc/mint-xml-parser.py"]