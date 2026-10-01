FROM node:22-alpine

WORKDIR /app

COPY package.json ./
# No lockfile yet in Phase 0 scaffold; install resolves from package.json.
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
