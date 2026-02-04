# ---------- Angular build ---------- 
FROM node:22 AS build
WORKDIR /app

# Kopiraj cijeli Angular projekt
COPY uks-client ./  

# Instaliraj dependencies
RUN npm install --legacy-peer-deps  # ili samo npm install

# Buildaj Angular
RUN npm run build -- --output-path=dist

# ---------- NGINX runtime ----------
FROM nginx:alpine

# Kopiraj build u NGINX
COPY --from=build /app/dist /usr/share/nginx/html
COPY uks-nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
