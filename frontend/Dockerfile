# syntax=docker/dockerfile:1

### Build stage: compile the Vite frontend into static files.
FROM node:20-alpine AS build

WORKDIR /srv/web

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html vite.config.ts tsconfig.json vitest.config.ts biome.json ./
COPY src ./src

ARG VITE_API_BASE=http://localhost:8000
ENV VITE_API_BASE=${VITE_API_BASE}

RUN npm run build

### Runtime stage: serve the static build with nginx (SPA fallback).
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /srv/web/dist /usr/share/nginx/html

EXPOSE 80
