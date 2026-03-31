environment        = "production"
region             = "us-east-1"
project            = "fictional-engine"

vpc_cidr           = "10.1.0.0/16"
single_nat_gateway = false

kubernetes_version = "1.35"
node_instance_type = "t3.medium"
node_min_size      = 2
node_max_size      = 5
node_desired_size  = 2

eks_public_access_cidrs = ["178.222.168.58/32"]

domain_name = "fictional-engine.online"

db_instance_class  = "db.t3.micro"
db_name            = "inventory"
rds_multi_az            = true
rds_backup_retention    = 30
rds_deletion_protection = true
rds_skip_final_snapshot = false

github_org         = "dimitrije-janic"
github_repo        = "fictional-engine"

ecr_repositories   = ["backend", "frontend"]
