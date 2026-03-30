FROM node:20-slim

WORKDIR /app

COPY package.json .
RUN npm install

COPY server.js .

EXPOSE 9000

CMD ["npm", "start"]