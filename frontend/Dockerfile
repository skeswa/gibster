# Build stage
FROM node:20-alpine AS builder
WORKDIR /app

# Accept build arguments
ARG NEXT_PUBLIC_API_URL=http://localhost:8000

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Set environment variable for build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application
RUN npm run build

# Ensure public directory exists (even if empty)
RUN mkdir -p /app/public

# Production stage
FROM node:20-alpine
WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]