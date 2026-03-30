# ── Stage 1: Build ─────────────────────────────────────────────
FROM node:24-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 2: Production ────────────────────────────────────────
FROM node:24-alpine

RUN addgroup --gid 1000 app && adduser --uid 1000 --ingroup app --shell /bin/sh app

WORKDIR /app

COPY --from=build /app/build ./build
COPY --from=build /app/package.json ./

RUN npm install --omit=dev

USER app

EXPOSE 3000

CMD ["npm", "run", "start"]
