# Use Node 16 Alpine as base image
FROM node:16-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Expose port 3000
EXPOSE 3000

# Start the application
CMD ["npm", "start"]