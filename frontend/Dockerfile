# pull official base image
FROM node:14-alpine3.11

# set working directory
WORKDIR /opt

# add `/app/node_modules/.bin` to $PATH
ENV PATH /opt/node_modules/.bin:$PATH

# install app dependencies
COPY package.json ./
COPY package-lock.json ./
RUN npm install