# ==============================================================================
# Container Security Policy — OPA/Rego
# ==============================================================================
# Enforces container security best practices for fintech workloads:
# - Deny privileged containers
# - Require non-root execution
# - Enforce resource limits (prevent noisy-neighbor DoS)
# - Block 'latest' tag (reproducible deployments)
# - Require read-only root filesystem
# ==============================================================================

package container_security

import rego.v1

# --- Deny privileged containers ---

deny contains msg if {
    some container in input.spec.containers
    container.securityContext.privileged == true
    msg := sprintf("DENY: Container '%s' must not run as privileged", [container.name])
}

# --- Require non-root user ---

deny contains msg if {
    some container in input.spec.containers
    not container.securityContext.runAsNonRoot
    msg := sprintf("DENY: Container '%s' must set securityContext.runAsNonRoot=true", [container.name])
}

# --- Block 'latest' tag ---

deny contains msg if {
    some container in input.spec.containers
    endswith(container.image, ":latest")
    msg := sprintf("DENY: Container '%s' uses ':latest' tag — use a specific version", [container.name])
}

deny contains msg if {
    some container in input.spec.containers
    not contains(container.image, ":")
    msg := sprintf("DENY: Container '%s' has no tag specified — use a specific version", [container.name])
}

# --- Enforce resource limits ---

deny contains msg if {
    some container in input.spec.containers
    not container.resources.limits
    msg := sprintf("DENY: Container '%s' must define resource limits", [container.name])
}

deny contains msg if {
    some container in input.spec.containers
    not container.resources.limits.cpu
    msg := sprintf("DENY: Container '%s' must define CPU limit", [container.name])
}

deny contains msg if {
    some container in input.spec.containers
    not container.resources.limits.memory
    msg := sprintf("DENY: Container '%s' must define memory limit", [container.name])
}

# --- Require read-only root filesystem ---

deny contains msg if {
    some container in input.spec.containers
    not container.securityContext.readOnlyRootFilesystem
    msg := sprintf("DENY: Container '%s' should use readOnlyRootFilesystem=true", [container.name])
}

# --- Deny host namespace sharing ---

deny contains msg if {
    input.spec.hostPID == true
    msg := "DENY: Pod must not share host PID namespace"
}

deny contains msg if {
    input.spec.hostIPC == true
    msg := "DENY: Pod must not share host IPC namespace"
}

# --- Deny privilege escalation ---

deny contains msg if {
    some container in input.spec.containers
    container.securityContext.allowPrivilegeEscalation == true
    msg := sprintf("DENY: Container '%s' must not allow privilege escalation", [container.name])
}
