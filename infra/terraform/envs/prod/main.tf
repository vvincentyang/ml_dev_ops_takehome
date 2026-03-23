variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "tf_state_bucket" {
  type        = string
  description = "S3 bucket holding Terraform state (from cfn-bootstrap)"
}

variable "aws_account_id" {
  type        = string
  description = "AWS account ID"
}

data "terraform_remote_state" "shared" {
  backend = "s3"
  config = {
    bucket = var.tf_state_bucket
    key    = "shared/terraform.tfstate"
    region = var.aws_region
  }
}

locals {
  env = "prod"
  tags = {
    Project     = "ml-app"
    Environment = local.env
    ManagedBy   = "Terraform"
  }
}

module "networking" {
  source   = "../../modules/networking"
  env      = local.env
  vpc_cidr = "10.2.0.0/16"
  tags     = local.tags
}

module "ecs" {
  source     = "../../modules/ecs"
  env        = local.env
  aws_region = var.aws_region

  image_uri = "203159929121.dkr.ecr.us-west-2.amazonaws.com/ml-app:latest"

  desired_count           = 2
  cpu                     = 512
  memory                  = 1024
  use_spot                = false   # regular FARGATE for production stability
  task_execution_role_arn = data.terraform_remote_state.shared.outputs.task_execution_role_arn
  target_group_arn        = module.networking.alb_target_group_arn
  private_subnet_ids      = module.networking.private_subnet_ids
  ecs_sg_id               = module.networking.ecs_sg_id

  tags = local.tags
}

output "alb_dns_name" {
  description = "Production ALB DNS"
  value       = module.networking.alb_dns_name
}
