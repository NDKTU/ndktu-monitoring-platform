# Build stage
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Expose port 5173 for Vite
EXPOSE 5173

# Run Vite with --host to allow external access
CMD ["npm", "run", "dev", "--", "--host"]
