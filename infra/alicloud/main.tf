locals {
  tags = {
    Application = "no-scam"
    ManagedBy   = "terraform"
  }

  cloud_config = "#cloud-config\n${yamlencode({
    package_update = true
    packages       = ["docker.io"]
    ssh_pwauth     = false
    write_files = [
      {
        path        = "/etc/no-scam/app.env"
        owner       = "root:root"
        permissions = "0600"
        content     = "PYTHON_DOTENV_DISABLED=1\n"
      },
      {
        path        = "/etc/systemd/system/no-scam.service"
        owner       = "root:root"
        permissions = "0644"
        content = templatefile("${path.module}/no-scam.service.tftpl", {
          container_image = var.container_image
          bind_address    = length(var.http_cidrs) == 0 ? "127.0.0.1" : "0.0.0.0"
        })
      }
    ]
    runcmd = [
      ["systemctl", "enable", "--now", "docker"],
      ["systemctl", "daemon-reload"],
      ["systemctl", "enable", "--now", "no-scam"]
    ]
  })}"
}

resource "alicloud_vpc" "app" {
  vpc_name   = var.name
  cidr_block = "10.42.0.0/16"
  tags       = local.tags
}

resource "alicloud_vswitch" "app" {
  vswitch_name = var.name
  vpc_id       = alicloud_vpc.app.id
  zone_id      = var.availability_zone
  cidr_block   = "10.42.1.0/24"
}

resource "alicloud_security_group" "app" {
  security_group_name = var.name
  vpc_id              = alicloud_vpc.app.id
  security_group_type = "normal"
  inner_access_policy = "Drop"
  tags                = local.tags
}

resource "alicloud_security_group_rule" "ssh" {
  for_each = var.ssh_cidrs

  security_group_id = alicloud_security_group.app.id
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "22/22"
  cidr_ip           = each.value
}

resource "alicloud_security_group_rule" "http" {
  for_each = var.http_cidrs

  security_group_id = alicloud_security_group.app.id
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "8000/8000"
  cidr_ip           = each.value
}

resource "terraform_data" "bootstrap" {
  triggers_replace = [sha256(local.cloud_config), var.image_id]
}

resource "alicloud_instance" "app" {
  instance_name              = var.name
  host_name                  = var.name
  image_id                   = var.image_id
  instance_type              = var.instance_type
  instance_charge_type       = "PostPaid"
  vswitch_id                 = alicloud_vswitch.app.id
  security_groups            = [alicloud_security_group.app.id]
  key_name                   = var.key_pair_name
  internet_charge_type       = "PayByTraffic"
  internet_max_bandwidth_out = var.internet_bandwidth_mbps
  system_disk_category       = "cloud_essd"
  system_disk_size           = 40
  system_disk_encrypted      = true
  http_tokens                = "required"
  http_endpoint              = "enabled"
  instance_metadata_tags     = "disabled"
  deletion_protection        = var.deletion_protection
  user_data                  = base64encode(local.cloud_config)
  tags                       = local.tags

  # Cloud-init first-boot modules do not rerun when ECS merely updates user data.
  lifecycle {
    replace_triggered_by = [terraform_data.bootstrap]
  }

  depends_on = [
    alicloud_security_group_rule.ssh,
    alicloud_security_group_rule.http
  ]
}
