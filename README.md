There are several options:

Option 1: Deploy all existing components into AWS ecs
Option 2: Migrate the existing functionalities into AWS services

other options like deploying all the existing components into AWS eks

The source code presented here is based on option 1.

There are some pending features not implemented:

1) nginx reversed proxy config file is hardcoded with the domain name. I have not figured out how to dynamically inject the domain name
2) the connection to redis server is not successful yet. Need to debug what goes wrong
3) have not implemented the MySQL server yet

How to run the code:

### create new task

pulumi stack init aws-py-fargate

### set AWS region

pulumi config set aws:region us-east-1

### configure redish password as an env variable

pulumi config set redis-password abcd1234 --secret

### create and activate virtual env and install dependencies

python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

### deploy the code

pulumi up

### test the nginx reversed proxy routing to static html (please note that the dns is hardcoded still in nginx_proxy/nginx.conf)

curl http://$(pulumi stack output proxy_url)

### test the nginx reversed proxy routing to node.js api (please note that the dns is hardcoded still in nginx_proxy/nginx.conf)

curl http://$(pulumi stack output proxy_url)/api

### test the static html directly

curl http://$(pulumi stack output web_url):8080

### test the node.js api directly

curl http://$(pulumi stack output web_url):8081/count
