terraform {
  required_version = ">= 1.7.0, < 2.0.0"

  required_providers {
    alicloud = {
      source  = "aliyun/alicloud"
      version = "~> 2.2.0"
    }
  }

  backend "oss" {}
}

provider "alicloud" {
  region = var.region
}
