terraform_version: 7.7.7
ec2_subnets: ['defaulto20_subnet1a', 'defaulto20_subnet1b']
using_aurora: False
enable_rds: default10_true




provider "aws" {
  region     = "us-east-1"
  default_tags {
    tags = {
      Environment   = dev
    }
  }
}


terraform {
  required_version = 7.7.7

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = 8.8.8
    }
  }
}

