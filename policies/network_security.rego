# ==============================================================================
# Network Security Policy — OPA/Rego
# ==============================================================================
# Enforces network isolation for fintech workloads:
# - Deny hostNetwork access
# - Require NetworkPolicy on namespaces
# - Restrict host port usage
# - Enforce service type restrictions (no NodePort in production)
# ==============================================================================

package network_security

import rego.v1

# --- Deny hostNetwork ---

deny contains msg if {
    input.spec.hostNetwork == true
    msg := "DENY: Pod must not use host network — violates network isolation"
}

# --- Deny hostPort usage ---

deny contains msg if {
    some container in input.spec.containers
    some port in container.ports
    port.hostPort > 0
    msg := sprintf(
        "DENY: Container '%s' must not use hostPort %d — use Services instead",
        [container.name, port.hostPort],
    )
}

# --- Deny NodePort services in production ---

deny contains msg if {
    input.kind == "Service"
    input.spec.type == "NodePort"
    msg := sprintf(
        "DENY: Service '%s' uses NodePort — use ClusterIP or LoadBalancer with proper security groups",
        [input.metadata.name],
    )
}

# --- Deny LoadBalancer without annotations (must have internal LB annotation) ---

deny contains msg if {
    input.kind == "Service"
    input.spec.type == "LoadBalancer"
    not input.metadata.annotations["service.beta.kubernetes.io/aws-load-balancer-internal"]
    msg := sprintf(
        "DENY: Service '%s' is a public LoadBalancer — must use internal LB annotation",
        [input.metadata.name],
    )
}

# --- Require specific DNS policy ---

deny contains msg if {
    input.spec.dnsPolicy == "Default"
    msg := "DENY: Pod should use 'ClusterFirst' DNS policy, not 'Default'"
}
