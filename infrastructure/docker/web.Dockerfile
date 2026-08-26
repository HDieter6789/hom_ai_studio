FROM node:20-slim AS builder
WORKDIR /srv/apps/web

COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm install

COPY apps/web ./
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /srv/apps/web
ENV NODE_ENV=production

COPY --from=builder /srv/apps/web/public ./public
COPY --from=builder /srv/apps/web/.next ./.next
COPY --from=builder /srv/apps/web/node_modules ./node_modules
COPY --from=builder /srv/apps/web/package.json ./package.json

EXPOSE 3000
CMD ["npm", "run", "start"]
