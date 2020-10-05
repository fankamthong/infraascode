from pulumi import export, ResourceOptions
import pulumi
import pulumi_aws as aws
import json
import iam
import net
import proxy
import web
import app
import redis

####################################################################
### Spinning up nginx reversed proxy
####################################################################
# create task definition for nginx reversed proxy.
proxy_task_definition = aws.ecs.TaskDefinition('proxy-task',
    family='fargate-task-definition',
    cpu='256',
    memory='512',
    network_mode='awsvpc',
    requires_compatibilities=['FARGATE'],
    execution_role_arn=iam.role.arn,
    container_definitions=pulumi.Output.all(proxy.image.image_name).apply(lambda args: json.dumps([{
		'name': 'nginx-proxy',
		'image': args[0],
		'portMappings': [{
			'containerPort': proxy.port,
			'hostPort': proxy.port,
			'protocol': 'tcp'
		}],
        #"environment": [ # Pass the DNS name to dockerfile
        #    { "name": "DNS", "value": loadbalancer.dns_name },
        #],
}])))

# load balanced service running for nginx reversed proxy.
proxy_service = aws.ecs.Service('proxy-svc',
	cluster=net.cluster.arn,
    desired_count=3,
    launch_type='FARGATE',
    task_definition=proxy_task_definition.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
		assign_public_ip=True,
		subnets=net.default_vpc_subnets.ids,
		security_groups=[proxy.sec_grp.id],
	),
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
		target_group_arn=proxy.targetgroup.arn,
		container_name='nginx-proxy',
		container_port=proxy.port,
	)],
    opts=ResourceOptions(depends_on=[proxy.listener]),
)

####################################################################
### Spinning up nginx web server
####################################################################
# create task definition for nginx web server.
web_task_definition = aws.ecs.TaskDefinition('web-task',
    family='fargate-task-definition',
    cpu='256',
    memory='512',
    network_mode='awsvpc',
    requires_compatibilities=['FARGATE'],
    execution_role_arn=iam.role.arn,
    container_definitions=pulumi.Output.all(web.image.image_name).apply(lambda args: json.dumps([{
		'name': 'nginx-web',
		'image': args[0],
		'portMappings': [{
			'containerPort': web.port,
			'hostPort': web.port,
			'protocol': 'tcp'
		}],
        #"environment": [ # Pass the DNS name to dockerfile
        #    { "name": "DNS", "value": loadbalancer.dns_name },
        #],
}])))

# load balanced service running for nginx web server.
web_service = aws.ecs.Service('web-svc',
	cluster=net.cluster.arn,
    desired_count=3,
    launch_type='FARGATE',
    task_definition=web_task_definition.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
		assign_public_ip=True,
		subnets=net.default_vpc_subnets.ids,
		security_groups=[web.sec_grp.id],
	),
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
		target_group_arn=web.targetgroup.arn,
		container_name='nginx-web',
		container_port=web.port,
	)],
    opts=ResourceOptions(depends_on=[web.listener]),
)

####################################################################
### Spinning up nodejs app server
####################################################################

redis_endpoint = {"host": redis.loadbalancer.dns_name, "port": redis.port}

# create task definition for node.js app server.
app_task_definition = aws.ecs.TaskDefinition('app-task',
    family='fargate-task-definition',
    cpu='256',
    memory='512',
    network_mode='awsvpc',
    requires_compatibilities=['FARGATE'],
    execution_role_arn=iam.role.arn,
    task_role_arn=iam.task_role.arn,
    container_definitions=pulumi.Output.all(app.image.image_name, redis_endpoint).apply(lambda args: json.dumps([{
		'name': 'node-app',
		'image': args[0],
		'portMappings': [{
			'containerPort': app.port,
			'hostPort': app.port,
			'protocol': 'tcp'
		}],
        "environment": [ # Pass redis endpoint to node.js instances
            { "name": "REDIS", "value": args[1]["host"] },
            { "name": "REDIS_PORT", "value": str(args[1]["port"]) },
            { "name": "REDIS_PWD", "value": redis.password },
        ],
}])))

# load balanced service running for node.js app server.
app_service = aws.ecs.Service('node-svc',
	cluster=net.cluster.arn,
    desired_count=3,
    launch_type='FARGATE',
    task_definition=app_task_definition.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
		assign_public_ip=True,
		subnets=net.default_vpc_subnets.ids,
		security_groups=[app.sec_grp.id],
	),
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
		target_group_arn=app.targetgroup.arn,
		container_name='node-app',
		container_port=app.port,
	)],
    opts=ResourceOptions(depends_on=[app.listener]),
)

####################################################################
### Spinning up redis instances
####################################################################
# Creating a task definition for the Redis instance.
redis_task_definition = aws.ecs.TaskDefinition("redis-task-definition",
    family="redis-task-definition-family",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=iam.role.arn,
    task_role_arn=iam.task_role.arn,
    container_definitions=json.dumps([{
        "name": "redis-container",
        "image": "redis", # A pre-built docker image with a functioning redis server
        "memory": 512,
        "essential": True,
        "portMappings": [{
            "containerPort": redis.port,
            "hostPort": redis.port,
            "protocol": "tcp"
        }],
        "command": ["redis-server", "--requirepass", redis.password],
	}]))

# load balanced service running for redis server
redis_service = aws.ecs.Service("redis-service",
	cluster=net.cluster.arn,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=redis_task_definition.arn,
    wait_for_steady_state=False,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
		assign_public_ip=True,
		subnets=net.default_vpc_subnets.ids,
		security_groups=[redis.sec_grp.id],
	),
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
		target_group_arn=redis.targetgroup.arn,
		container_name="redis-container",
		container_port=redis.port,
	)],
    opts=pulumi.ResourceOptions(depends_on=[redis.listener]),
)

export('proxy_url', proxy.loadbalancer.dns_name)
export('web_url', web.loadbalancer.dns_name)
export('app_url', app.loadbalancer.dns_name)
export('redis_url', redis.loadbalancer.dns_name)
