# Rafiki AI Frontend
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Expose port
EXPOSE 5173

# Run dev server (or use nginx for production)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
