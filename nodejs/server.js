'use strict';

const express = require('express');

// Constants
const PORT = 8081;
const HOST = '0.0.0.0';

const REDIS_HOST = process.env.REDIS;
const REDIS_PORT = process.env.REDIS_PORT;
const REDIS_PWD = process.env.REDIS_PWD;

// App
const app = express();
app.get('/count', (req, res) => {

  var count = 0;
  var msg = '';
  // redis client connection
  var redis = require('redis');
  var client = redis.createClient(REDIS_PORT, REDIS_HOST, {no_ready_check: true});

  if(!client){
      msg = 'client does not exist';
  }

  client.auth(REDIS_PWD, function (err) {
      if (err) {
        msg = 'Failed to authenticate redis';
      };
  });
  client.on('error', function (err) {
      msg = 'Failed to authenticate redis';
  });
  client.on('connect', function() {
      msg = 'Connected to Redis';
  });
  //get the user request counter
  client.get('counter', function (error, result) {
      if (error) {
          count = 1;
          msg = 'Failed to get counter';
      }else{
          count = count + result;
      }
  });
  // update the user request counter
  client.set('counter', count, redis.print);

  msg = 'message:' + msg + ' ' + REDIS_HOST + ' ' + REDIS_PORT + ' ' + REDIS_PWD + ' with count = ' + count;

  res.send(msg);
});

app.listen(PORT, HOST);
console.log(`Running on http://${HOST}:${PORT}`);
