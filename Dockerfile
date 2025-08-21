FROM nginx:alpine

COPY index.html /usr/share/nginx/html/
COPY dns_lookup.py /usr/share/nginx/html/

RUN echo 'server {' > /etc/nginx/conf.d/default.conf && \
  echo '    listen 7001;' >> /etc/nginx/conf.d/default.conf && \
  echo '    server_name localhost;' >> /etc/nginx/conf.d/default.conf && \
  echo '    root /usr/share/nginx/html;' >> /etc/nginx/conf.d/default.conf && \
  echo '    index index.html;' >> /etc/nginx/conf.d/default.conf && \
  echo '    location / {' >> /etc/nginx/conf.d/default.conf && \
  echo '        try_files $uri $uri/ =404;' >> /etc/nginx/conf.d/default.conf && \
  echo '    }' >> /etc/nginx/conf.d/default.conf && \
  echo '}' >> /etc/nginx/conf.d/default.conf

EXPOSE 7001

CMD ["nginx", "-g", "daemon off;"]
