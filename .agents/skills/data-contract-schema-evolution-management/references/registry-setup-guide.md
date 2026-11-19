# Schema Registry Setup and Operations Guide

## Selection Matrix

| Registry | Best fit | HA model | Auth focus | CI integration |
|---|---|---|---|---|
| Confluent Schema Registry | Kafka-centric Avro/Protobuf/JSON Schema | Multiple stateless nodes + durable Kafka | TLS, basic/RBAC, ACLs | REST compatibility/register APIs |
| AWS Glue Schema Registry | AWS-managed streaming | Regional managed service | IAM and KMS | AWS SDK/CLI checks |
| Apicurio Registry | Kubernetes/open-source, broad artifact types | Replicas + Kafka/SQL storage | OIDC, roles | REST/Maven/Gradle plugins |
| File-based | Local, air-gapped, small repositories | Git/object-store replication | Repository permissions | Native pull-request validation |

## Shared Design Rules

- Use stable subject/artifact names tied to logical contracts.
- Separate development, staging, and production credentials and namespaces.
- Permit CI or release automation to write; give runtime clients read-only access.
- Make released versions immutable and audit every registration/deletion.
- Configure compatibility per subject and check against all supported versions.
- Back up registry metadata, schemas, and storage dependencies.
- Monitor request latency/errors, rejected registrations, unknown IDs, cache age, and replication health.

## Confluent Schema Registry

### Configuration

Deploy at least two instances behind a health-aware load balancer. Point all instances at the same Kafka cluster and internal topic. Configure TLS in transit, authentication, schema normalization as appropriate, and explicit subject compatibility.

Typical subject strategies:

- topic-name for one contract per topic;
- record-name for shared records across topics;
- topic-record-name for isolation plus record identity.

Changing strategy after production publication can strand existing IDs; treat it as a migration.

### HA and Recovery

Registry nodes are replaceable; the Kafka backing topic is authoritative. Protect its replication, retention, compaction, and ACLs. Test restore into an isolated environment and verify IDs remain stable because payloads may embed schema IDs.

### CI/CD

1. Lint and compile the schema.
2. Query configured compatibility for the subject.
3. Check the proposal against every supported version.
4. Run generated-binding and golden-fixture tests.
5. Register before producer deployment.
6. Record returned ID/version in release evidence.

## AWS Glue Schema Registry

### Configuration

Create registries per environment or governance boundary, assign schema names by logical contract, select compatibility mode, and encrypt with an appropriate KMS key. Use IAM roles rather than embedded credentials.

### HA and Recovery

The service is managed regionally. Design applications for bounded registry unavailability through safe schema caching. For regional recovery, export schema definitions and recreate them through infrastructure automation; verify how IDs/versions affect serialized data and consumers.

### Authorization

Separate permissions for registry administration, schema registration, version reads, and deletion. Restrict KMS use consistently. Enable CloudTrail and alert on compatibility-mode changes and deletions.

### CI/CD

Use an assumed CI role to check/create schema versions. Promotion should use the same reviewed schema bytes across accounts, with environment-specific registry identifiers supplied by deployment configuration.

## Apicurio Registry

### Configuration

Choose KafkaSQL or SQL storage based on existing operations and recovery requirements. Define artifact groups for environment/domain boundaries, global rules sparingly, and artifact-specific validity/compatibility rules explicitly.

### HA and Recovery

Run multiple replicas with readiness probes and disruption budgets. For SQL storage, use a highly available database and tested backups. For KafkaSQL, protect the backing topics. Keep API and storage versions compatible during upgrades.

### Authorization

Integrate OIDC, map groups/service accounts to administrator, developer, and read-only roles, and use TLS. Do not expose anonymous writes. Audit artifact rules as well as versions.

### CI/CD

Use the REST API or build plugins to validate and register artifacts. Pin the artifact group, artifact ID, and compatibility rule in repository configuration so a pipeline cannot accidentally publish to a default group.

## File-Based Registry

### Layout

```text
registry/
  index.json
  orders/
    1.0.0/order.avsc
    1.1.0/order.avsc
  customers/
    2.0.0/customer.schema.json
```

The index should include subject, version history, hash, owner, compatibility mode, lifecycle, and relative path. Sign or review changes through source control; never overwrite a released path.

### HA and Authorization

Replicate through Git hosting or versioned object storage. Repository branch protection is the write authorization layer; runtime deployments consume pinned immutable artifacts or a published bundle. A file registry is unsuitable when globally coordinated real-time numeric IDs are required.

### CI/CD

- verify index hashes and unique versions;
- run compatibility checks against supported history;
- enforce owner approval through code owners;
- package an immutable registry snapshot;
- promote the same snapshot digest across environments.

## Operational Runbook

### Registry Unavailable

Use only cached schemas whose ID/fingerprint and TTL are known. Do not accept unvalidated new schema IDs indefinitely. Alert, preserve unread input durably, and resume after registry recovery.

### Incompatible Registration

Capture subject, proposed fingerprint, configured mode, comparison versions, and field-level blockers. Determine whether the proposal is wrong, configuration drifted, or a versioned contract is required. Never disable compatibility globally as an incident shortcut.

### Suspected Corruption or Deletion

Stop registrations, preserve backing storage, export audit logs, compare manifests/hashes, and restore in isolation. Verify old payload deserialization before reopening writes.

## Production Checklist

- HA and dependency failure modes are tested.
- TLS, least-privilege write/read roles, and audit logs are enabled.
- Compatibility is explicit per critical subject.
- Backups preserve IDs, versions, metadata, and rules.
- Clients have bounded caches and observable lookup failures.
- CI registers schemas before producers and retains evidence.
- Deletion is exceptional, approved, and checked against retention/replay.
