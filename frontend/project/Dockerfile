# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Build arguments for Vite environment variables
ARG VITE_API_SERVER_URL=http://localhost:2030
ARG VITE_AI_SERVER_URL=http://localhost:9999

# Set environment variables for build
ENV VITE_API_SERVER_URL=$VITE_API_SERVER_URL
ENV VITE_AI_SERVER_URL=$VITE_AI_SERVER_URL

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application with environment variables
RUN echo "Building with VITE_API_SERVER_URL=$VITE_API_SERVER_URL" && \
    echo "Building with VITE_AI_SERVER_URL=$VITE_AI_SERVER_URL" && \
    npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve to run the production build
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./

# Expose port (will be overridden by environment variable)
EXPOSE 5173

# Start the application
CMD ["sh", "-c", "serve -s dist -l tcp://0.0.0.0:${FRONTEND_PORT:-5173}"]
