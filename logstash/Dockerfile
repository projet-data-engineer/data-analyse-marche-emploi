FROM docker.elastic.co/logstash/logstash:8.0.0

# delete default configuration
RUN rm -f /usr/share/logstash/pipeline/logstash.conf

# copy configurations
# COPY logstash/pipeline/ /usr/share/logstash/pipeline/
# COPY logstash/config/ /usr/share/logstash/config/