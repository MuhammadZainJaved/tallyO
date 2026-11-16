FROM node:22-alpine AS dependencies
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --omit=dev

FROM nginx:1.27-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/src/ /usr/share/nginx/html/
COPY --from=dependencies /frontend/node_modules/angular/angular.min.js /usr/share/nginx/html/vendor/angular.min.js
COPY --from=dependencies /frontend/node_modules/angular-route/angular-route.min.js /usr/share/nginx/html/vendor/angular-route.min.js
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD wget -qO- http://127.0.0.1/healthz || exit 1
