mock_provider "alicloud" {}

variables {
  availability_zone = "ap-southeast-3a"
  instance_type     = "ecs.e-c1m2.large"
  image_id          = "ubuntu_24_04_x64_20G_alibase_test.vhd"
  key_pair_name     = "test-key"
  ssh_cidrs         = ["192.0.2.10/32"]
  container_image   = "registry.example/no-scam@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}

run "secure_defaults" {
  command = plan

  assert {
    condition     = length(alicloud_security_group_rule.http) == 0
    error_message = "HTTP must not be exposed by default."
  }

  assert {
    condition     = alicloud_security_group_rule.ssh["192.0.2.10/32"].port_range == "22/22"
    error_message = "SSH must be limited to the supplied administrator CIDR."
  }

  assert {
    condition     = alicloud_instance.app.system_disk_encrypted && alicloud_instance.app.deletion_protection
    error_message = "Disk encryption and deletion protection must be enabled."
  }

  assert {
    condition     = alicloud_instance.app.http_tokens == "required"
    error_message = "Instance metadata must require IMDSv2."
  }

  assert {
    condition     = alicloud_instance.app.instance_charge_type == "PostPaid" && alicloud_instance.app.internet_charge_type == "PayByTraffic"
    error_message = "The demo must use pay-as-you-go compute and traffic."
  }

  assert {
    condition     = strcontains(base64decode(alicloud_instance.app.user_data), "127.0.0.1:8000:8000")
    error_message = "Tunnel-only deployments must bind the Docker port to loopback."
  }

  assert {
    condition     = strcontains(base64decode(alicloud_instance.app.user_data), "--read-only") && strcontains(base64decode(alicloud_instance.app.user_data), "--cap-drop ALL")
    error_message = "Container runtime hardening must be present."
  }

  assert {
    condition     = !strcontains(base64decode(alicloud_instance.app.user_data), "DASHSCOPE_API_KEY")
    error_message = "AI credentials must not be embedded in cloud-init."
  }

  assert {
    condition     = yamldecode(base64decode(alicloud_instance.app.user_data)).write_files[0].permissions == "0600"
    error_message = "The runtime environment file must be private to root."
  }

  assert {
    condition     = length(base64decode(alicloud_instance.app.user_data)) < 16384
    error_message = "Decoded cloud-init must fit the ECS user-data size limit."
  }

  assert {
    condition     = strcontains(base64decode(alicloud_instance.app.user_data), "--pull=missing") && !strcontains(base64decode(alicloud_instance.app.user_data), "ExecStartPre=/usr/bin/docker pull")
    error_message = "Restarts must reuse the cached immutable image during registry outages."
  }
}

run "restricted_demo_http" {
  command = plan

  variables {
    http_cidrs = ["198.51.100.12/32"]
  }

  assert {
    condition     = alicloud_security_group_rule.http["198.51.100.12/32"].port_range == "8000/8000"
    error_message = "Explicit demo clients must be allowed on the app port only."
  }

  assert {
    condition     = strcontains(base64decode(alicloud_instance.app.user_data), "0.0.0.0:8000:8000")
    error_message = "Explicit HTTP access must bind the host port beyond loopback."
  }
}

run "reject_public_ssh" {
  command = plan

  variables {
    ssh_cidrs = ["0.0.0.0/0"]
  }

  expect_failures = [var.ssh_cidrs]
}

run "reject_public_http" {
  command = plan

  variables {
    http_cidrs = ["0.0.0.0/0"]
  }

  expect_failures = [var.http_cidrs]
}

run "reject_mutable_image" {
  command = plan

  variables {
    container_image = "registry.example/no-scam:latest"
  }

  expect_failures = [var.container_image]
}

run "reject_wrong_os" {
  command = plan

  variables {
    image_id = "aliyun_linux_3_x64_test"
  }

  expect_failures = [var.image_id]
}
