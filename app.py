import pulumi_aws as aws
import docker_repo
import net
import pulumi_docker as docker

########################################
# This is for node.js app server setup
########################################

port = 8081

#Create a SecurityGroup that permits HTTP ingress and unrestricted egress.
sec_grp = aws.ec2.SecurityGroup('app-secgrp',
	vpc_id=net.default_vpc.id,
	description='Enable HTTP access',
	ingress=[aws.ec2.SecurityGroupIngressArgs(
		protocol='tcp',
		from_port=port,
		to_port=port,
		cidr_blocks=['0.0.0.0/0'],
	)],
  	egress=[aws.ec2.SecurityGroupEgressArgs(
		protocol='-1',
		from_port=0,
		to_port=0,
		cidr_blocks=['0.0.0.0/0'],
	)],
)

# Create a load balancer to listen for HTTP traffic on port 8081.
loadbalancer = aws.lb.LoadBalancer('app-lb',
	security_groups=[sec_grp.id],
	subnets=net.default_vpc_subnets.ids,
)

targetgroup = aws.lb.TargetGroup('app-tg',
	port=port,
	protocol='HTTP',
	target_type='ip',
	vpc_id=net.default_vpc.id,
)

listener = aws.lb.Listener('app',
	load_balancer_arn=loadbalancer.arn,
	port=port,
	default_actions=[aws.lb.ListenerDefaultActionArgs(
		type='forward',
		target_group_arn=targetgroup.arn,
	)],
)

image = docker.Image("nodejs-dockerimage",
    image_name=docker_repo.app_ecr_repo.repository_url,
    build="./nodejs",
    skip_push=False,
    registry=docker_repo.app_registry
)
