FROM camunda/zeebe:8.5.22

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates netcat-openbsd && \
    curl -fL --retry 3 -o /usr/local/bin/zbctl https://github.com/camunda/zeebe/releases/download/8.5.22/zbctl && \
    chmod +x /usr/local/bin/zbctl && \
    apt-get remove -y curl && \
    apt-get autoremove -y && \
    apt-get clean
ENTRYPOINT ["sh", "-ec"]
