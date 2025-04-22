FROM node:20-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
USER nobody

ENTRYPOINT ["/usr/bin/tini", "-s", "--"]
CMD ["tail", "-f", "/dev/null"]
