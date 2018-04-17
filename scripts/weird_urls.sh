


#!/bin/bash
echo "blab blab la : http://mykibana.server/app/kibana#/discover?_g=(refreshInterval:(display:Off,pause:!f,value:0),time:(from:now-24h,mode:quick,to:now))&_a=(columns:!(levelname,syslog_message,extra.flat),interval:auto,query:(language:lucene,query:'uuid:%22076a4d47-4af5-4808-ab7d-1d5e6983e7c6%22'),sort:!('@timestamp',asc))"
