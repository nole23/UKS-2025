FROM nginx:alpine

# Kopiraj samo server blok u conf.d
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
