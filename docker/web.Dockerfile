FROM node:24-bookworm-slim AS build
WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web ./
RUN npm run build

FROM node:24-bookworm-slim
ENV NODE_ENV=production
WORKDIR /app
RUN useradd --create-home --uid 10001 careloop
COPY --from=build --chown=careloop:careloop /app/.next/standalone ./
COPY --from=build --chown=careloop:careloop /app/.next/static ./.next/static
USER careloop
EXPOSE 3000
CMD ["node", "server.js"]
