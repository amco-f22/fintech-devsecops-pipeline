# ==============================================================================
# PCI-DSS Compliance Policy — OPA/Rego
# ==============================================================================
# Maps to specific PCI-DSS requirements:
# - Req 2: Do not use vendor-supplied defaults
# - Req 3: Protect stored cardholder data (encryption)
# - Req 6: Develop and maintain secure systems
# - Req 7: Restrict access (RBAC / least privilege)
# - Req 8: Identify and authenticate access
# - Req 10: Track and monitor all access (audit logging)
# ==============================================================================

package pci_compliance

import rego.v1

# --- Req 2: No default credentials / passwords in env vars ---

sensitive_patterns := ["PASSWORD", "SECRET", "API_KEY", "TOKEN", "PRIVATE_KEY", "CARD_NUMBER", "CVV"]

deny contains msg if {
    some container in input.spec.containers
    some env in container.env
    some pattern in sensitive_patterns
    contains(upper(env.name), pattern)
    env.value != ""
    not env.valueFrom
    msg := sprintf(
        "PCI-DSS Req 2: Container '%s' has sensitive env var '%s' with plaintext value — use Secrets or external vault",
        [container.name, env.name],
    )
}

# --- Req 3: Require encrypted volumes ---

deny contains msg if {
    some volume in input.spec.volumes
    volume.hostPath
    msg := sprintf(
        "PCI-DSS Req 3: Volume '%s' uses hostPath — use encrypted PersistentVolumeClaim instead",
        [volume.name],
    )
}

# --- Req 6: Require liveness and readiness probes ---

deny contains msg if {
    some container in input.spec.containers
    not container.livenessProbe
    msg := sprintf(
        "PCI-DSS Req 6: Container '%s' must define livenessProbe for reliability",
        [container.name],
    )
}

deny contains msg if {
    some container in input.spec.containers
    not container.readinessProbe
    msg := sprintf(
        "PCI-DSS Req 6: Container '%s' must define readinessProbe for safe rollouts",
        [container.name],
    )
}

# --- Req 7: Deny cluster-admin service account binding ---

deny contains msg if {
    input.kind == "ClusterRoleBinding"
    input.roleRef.name == "cluster-admin"
    msg := sprintf(
        "PCI-DSS Req 7: ClusterRoleBinding '%s' grants cluster-admin — use least-privilege roles",
        [input.metadata.name],
    )
}

# --- Req 8: Require service account (no default) ---

deny contains msg if {
    input.spec.serviceAccountName == "default"
    msg := "PCI-DSS Req 8: Pod must not use 'default' service account — create a dedicated SA with IRSA"
}

deny contains msg if {
    not input.spec.serviceAccountName
    msg := "PCI-DSS Req 8: Pod must specify a serviceAccountName"
}

# --- Req 10: Require audit labels ---

deny contains msg if {
    not input.metadata.labels["app.kubernetes.io/part-of"]
    msg := "PCI-DSS Req 10: Pod must have 'app.kubernetes.io/part-of' label for audit tracking"
}

deny contains msg if {
    not input.metadata.labels["app.kubernetes.io/managed-by"]
    msg := "PCI-DSS Req 10: Pod must have 'app.kubernetes.io/managed-by' label for audit tracking"
}
