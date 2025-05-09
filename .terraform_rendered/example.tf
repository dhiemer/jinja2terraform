terraform_version: 20
ec2_subnets: ['defaulto20_error.site', 'defaulto20_internal.site']
using_aurora: False
enable_rds: default10_true



terraform {
  required_version = 20

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = 20
    }
  }
}
