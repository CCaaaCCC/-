FROM node:20-alpine AS build
ENV NODE_OPTIONS=--max-old-space-size=1536
ARG NPM_REGISTRY=https://registry.npmmirror.com
WORKDIR /app
COPY package*.json ./
RUN npm config set registry ${NPM_REGISTRY} \
	&& npm config set fetch-retries 5 \
	&& npm config set fetch-retry-mintimeout 20000 \
	&& npm config set fetch-retry-maxtimeout 120000 \
	&& npm install --no-audit --fund=false
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
