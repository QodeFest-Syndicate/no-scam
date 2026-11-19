variable "region" {
  description = "Alibaba Cloud region; defaults to Kuala Lumpur."
  type        = string
  default     = "ap-southeast-3"
}

variable "availability_zone" {
  description = "Zone in the selected region with capacity for the chosen instance type."
  type        = string
}

variable "instance_type" {
  description = "Available x86_64 ECS instance type with at least 2 vCPU and 4 GiB RAM."
  type        = string
}

variable "image_id" {
  description = "Pinned Alibaba Cloud Ubuntu 24.04 x86_64 system image ID in the selected region."
  type        = string

  validation {
    condition     = startswith(var.image_id, "ubuntu_24_04_x64_")
    error_message = "Select an Ubuntu 24.04 x86_64 system image (ubuntu_24_04_x64_...)."
  }
}

variable "key_pair_name" {
  description = "Name of an existing ECS SSH key pair in the selected region; never a private key."
  type        = string
}

variable "ssh_cidrs" {
  description = "Administrator IPv4 CIDRs allowed to SSH and tunnel to the app; /24 or narrower."
  type        = set(string)

  validation {
    condition = length(var.ssh_cidrs) > 0 && alltrue([
      for cidr in var.ssh_cidrs : can(cidrnetmask(cidr)) && try(tonumber(split("/", cidr)[1]) >= 24, false)
    ])
    error_message = "Provide at least one IPv4 CIDR with a /24 through /32 prefix; do not expose SSH to the internet."
  }
}

variable "http_cidrs" {
  description = "Optional IPv4 CIDRs allowed to reach demo HTTP on port 8000; empty keeps it SSH-tunnel-only. No TLS or authentication is provided."
  type        = set(string)
  default     = []

  validation {
    condition = alltrue([
      for cidr in var.http_cidrs : can(cidrnetmask(cidr)) && try(tonumber(split("/", cidr)[1]) >= 24, false)
    ])
    error_message = "Demo HTTP access must use IPv4 CIDRs with a /24 through /32 prefix; use SSH tunnelling for encrypted access."
  }
}

variable "container_image" {
  description = "Published linux/amd64 image by immutable sha256 digest. For private registries, authenticate Docker on the host after provisioning."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.:-]*/[a-z0-9._/-]+@sha256:[a-f0-9]{64}$", var.container_image))
    error_message = "Use a registry/repository@sha256:<64 lowercase hex characters> image reference, not a mutable tag."
  }
}

variable "name" {
  description = "Resource name prefix."
  type        = string
  default     = "no-scam-demo"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,39}$", var.name))
    error_message = "Use 2-40 lowercase letters, digits or hyphens, starting with a letter."
  }
}

variable "internet_bandwidth_mbps" {
  description = "Maximum public outbound bandwidth, billed by traffic."
  type        = number
  default     = 5

  validation {
    condition     = var.internet_bandwidth_mbps >= 1 && var.internet_bandwidth_mbps <= 100 && floor(var.internet_bandwidth_mbps) == var.internet_bandwidth_mbps
    error_message = "Bandwidth must be a whole number from 1 to 100 Mbps."
  }
}

variable "deletion_protection" {
  description = "Prevent accidental ECS deletion. Disable in a separate apply before an intentional replacement or teardown."
  type        = bool
  default     = true
}
