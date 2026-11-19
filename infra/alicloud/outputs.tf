output "instance_id" {
  description = "Provisioned ECS instance ID."
  value       = alicloud_instance.app.id
}

output "public_ip" {
  description = "ECS public IPv4 address; changes when the instance is replaced."
  value       = alicloud_instance.app.public_ip
}

output "ssh_tunnel_command" {
  description = "Add -i /path/to/private-key if your key is not in the SSH agent, then browse localhost:8000."
  value       = "ssh -N -L 127.0.0.1:8000:127.0.0.1:8000 root@${alicloud_instance.app.public_ip}"
}

output "demo_http_url" {
  description = "Unencrypted demo-only endpoint; emitted only when HTTP client CIDRs are explicitly configured."
  value       = length(var.http_cidrs) == 0 ? null : "http://${alicloud_instance.app.public_ip}:8000"
}
