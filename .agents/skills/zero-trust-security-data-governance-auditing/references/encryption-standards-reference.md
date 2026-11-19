# Encryption Standards Reference

Use approved current organizational and jurisdictional standards. Algorithm names alone do not provide security: mode, key size, randomness, implementation, protocol, rotation, access, and failure handling matter.

## Algorithm Selection

- **Symmetric encryption:** AES-256-GCM is a common authenticated-encryption choice. Generate a unique nonce per key and never reuse it; authenticate context as additional data. ChaCha20-Poly1305 is useful where hardware AES acceleration is unavailable.
- **Asymmetric encryption/key establishment:** prefer modern well-reviewed platform profiles. RSA, when required for interoperability, should use at least 2048-bit keys and OAEP/PSS rather than legacy padding. Do not encrypt bulk data directly with RSA.
- **Signatures:** ECDSA with approved curves or EdDSA where supported. ECDSA requires correct nonce generation; validate curve and signature encoding.
- **Hashing:** SHA-256/384 for integrity; HMAC for keyed integrity. For passwords use a memory-hard KDF such as Argon2id, or an approved PBKDF profile with unique salts and an upgrade path.

Avoid ECB mode, unauthenticated CBC for new designs, DES/3DES, MD5/SHA-1 for security decisions, custom cryptography, predictable IVs/nonces, and embedded keys.

## Data at Rest

Encrypt databases, disks, object stores, queues, search indexes, logs, caches, snapshots, backups, and exports according to classification. Storage encryption does not replace row/object authorization or field-level protection. Record where plaintext exists, including memory, temporary files, ETL, support tools, analytics, and restore environments.

## Envelope Encryption

1. Generate a random data-encryption key (DEK) close to use.
2. Encrypt data with authenticated encryption and contextual AAD (tenant, record type, version).
3. Wrap the DEK using a key-encryption key (KEK) in KMS/HSM.
4. Store ciphertext, wrapped DEK, algorithm/version, nonce, and authentication tag—never plaintext DEK.
5. Unwrap through authorized workload identity; keep plaintext key lifetime short and avoid logs/dumps.

Per-tenant or per-domain KEKs improve isolation and revocation but increase lifecycle complexity. Rewrap DEKs to rotate KEKs without re-encrypting all data; rotate DEKs based on volume, time, compromise, or policy.

## KMS and HSM Governance

Separate key administrators from data users. Restrict encrypt/decrypt, grant, export, disable, schedule-deletion, and policy-change permissions. Use non-exportable HSM-backed keys where assurance requires it. Enable immutable audit logs, deletion protection, multi-party approval for destructive actions, regional/residency controls, backup/recovery, and tested break-glass access.

Inventory key owner, purpose, data class, region, aliases/IDs, algorithm, creation, rotation, consumers, expiry, recovery, and destruction evidence. Test disable and recovery before relying on them.

## TLS Configuration

Use TLS 1.3 by default and TLS 1.2 only with approved AEAD suites where compatibility requires it. Disable SSL, TLS 1.0/1.1, weak ciphers, static RSA key exchange, compression, and invalid certificate bypass. Validate hostname, chain, purpose, revocation strategy, and time. Use mTLS for workload identity where risk and architecture warrant it.

Automate certificate issuance, renewal, deployment, expiry alerting, revocation, and inventory. Short-lived certificates reduce revocation dependence but require reliable renewal. Define behavior when OCSP, CA, or certificate automation is unavailable.

## Field-Level Encryption

Apply when storage administrators, analytics systems, backups, or support tools must not see restricted fields. Bind ciphertext to tenant/record/field with AAD; version formats; design query/index needs explicitly. Deterministic encryption leaks equality and frequency; use only after threat analysis. Tokenization or format-preserving encryption may preserve workflows but creates a high-value token/key service.

## Rotation and Cryptographic Agility

Version ciphertext and protocol profiles. Maintain decrypt-old/encrypt-new during migration; measure remaining old material; rehearse rollback without reintroducing weak writes. Emergency rotation must revoke access, invalidate caches/sessions as needed, assess historical use, and preserve incident evidence.

## Verification Checklist

- Approved algorithm/mode/library and threat model.
- Randomness, nonce uniqueness, AAD, tag verification, and error handling tested.
- Keys absent from source, artifacts, logs, and unprotected state.
- Least-privilege key use, separation of duties, audit, rotation, recovery, and destruction.
- TLS peer identity and downgrade configuration tested.
- Backups, replicas, exports, logs, and restores included.
- Performance, availability, residency, and compromise recovery measured.
