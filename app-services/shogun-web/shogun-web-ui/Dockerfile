FROM node:20-alpine AS builder
WORKDIR /app
# NEXT_PUBLIC_API_URL is a build-time value — Next.js compiles rewrite destinations
# into the server bundle, so it must be injected as a build ARG, not a runtime ENV.
ARG NEXT_PUBLIC_API_URL=http://shogun-web-api:8090
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
