# Base image
FROM node:18-alpine as base

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Development stage
FROM base as development
COPY package.json pnpm-lock.yaml ./
RUN pnpm install
COPY . .

# Production stage
FROM base as production
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --prod
COPY . .
RUN pnpm build

CMD ["pnpm", "start"] 