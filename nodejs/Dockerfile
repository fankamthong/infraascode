FROM node:12

# Create app directory
WORKDIR /usr/src/app

# Install app dependencies
COPY package*.json ./

RUN npm install

RUN npm install redis

# Bundle app source
COPY . .

EXPOSE 8081
CMD [ "node", "server.js" ]
