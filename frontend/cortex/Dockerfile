# Build stage
FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
RUN corepack use yarn@latest

# Add build dependencies
RUN apk add --no-cache python3 make g++ sqlite-dev

# Define build args for environment variables
ARG API_BASE_URL

# Copy package.json and yarn.lock first (for better caching)
COPY package*.json yarn.lock* ./

# Install dependencies (this layer cached unless package files change)
RUN yarn install --frozen-lockfile

# Copy application source code (excludes node_modules via .dockerignore)
COPY . .

# Set environment variables
ENV API_BASE_URL=${API_BASE_URL}
ENV NODE_ENV=production

# Increase Node.js heap size to prevent out-of-memory errors during build
# 4096 = 4GB, adjust based on your needs (can go up to 8GB or more if needed)
ENV NODE_OPTIONS=--max-old-space-size=4096

# Generate static files
# Using NODE_OPTIONS from ENV to ensure sufficient memory
RUN yarn generate || (echo "Build failed. See error above." && exit 1)

# Serving stage
FROM node:22-alpine AS serve

WORKDIR /app
RUN corepack enable

# Install serve using npm instead of yarn global
RUN npm install -g serve

# Copy built assets from the build stage
COPY --from=build /app/.output/public ./public

# Expose port
EXPOSE 3000

# Start the static server
CMD ["serve", "-s", "public", "-l", "3000"]

