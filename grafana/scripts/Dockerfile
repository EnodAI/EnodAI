FROM alpine:latest

RUN apk add --no-cache curl jq bash

COPY provision-dashboard.sh /provision-dashboard.sh
RUN chmod +x /provision-dashboard.sh

CMD ["/provision-dashboard.sh"]
