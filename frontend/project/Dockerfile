# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Build arguments for Vite environment variables
ARG VITE_API_SERVER_URL=http://localhost:2030
ARG VITE_AI_SERVER_URL=http://localhost:9999

# Set environment variables for build
ENV VITE_API_SERVER_URL=$VITE_API_SERVER_URL
ENV VITE_AI_SERVER_URL=$VITE_AI_SERVER_URL

# Copy package files first for better layer caching
COPY package*.json ./

# Install dependencies with cache mount for faster rebuilds
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline

# Copy source code after dependencies are installed
# This ensures dependencies are cached when only source code changes
COPY . .

# Build the application with environment variables
RUN echo "Building with VITE_API_SERVER_URL=$VITE_API_SERVER_URL" && \
    echo "Building with VITE_AI_SERVER_URL=$VITE_AI_SERVER_URL" && \
    npm run build

# Production stage - use minimal image
FROM node:18-alpine AS production

WORKDIR /app

# Install serve to run the production build
RUN npm install -g serve && \
    # Clean npm cache to reduce image size
    npm cache clean --force

# Create non-root user for security
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Copy built files from builder
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist

# Switch to non-root user
USER appuser

# Expose port (will be overridden by environment variable)
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${FRONTEND_PORT:-5173} || exit 1

# Start the application
CMD ["sh", "-c", "serve -s dist -l tcp://0.0.0.0:${FRONTEND_PORT:-5173}"]
