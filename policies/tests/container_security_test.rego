# ==============================================================================
# Container Security Policy Tests
# ==============================================================================
# Proves each container security rule works correctly:
# - Should-deny cases (violations detected)
# - Should-allow cases (compliant pods pass)
# ==============================================================================

package container_security_test

import rego.v1

import data.container_security

# --- Test: Privileged container is denied ---

test_deny_privileged_container if {
    result := container_security.deny with input as {
        "spec": {
            "containers": [{
                "name": "bad-container",
                "image": "nginx:1.25",
                "securityContext": {
                    "privileged": true,
                    "runAsNonRoot": true,
                    "readOnlyRootFilesystem": true,
                    "allowPrivilegeEscalation": false,
                },
                "resources": {"limits": {"cpu": "100m", "memory": "128Mi"}},
            }],
        },
    }
    count(result) > 0
}

# --- Test: Latest tag is denied ---

test_deny_latest_tag if {
    result := container_security.deny with input as {
        "spec": {
            "containers": [{
                "name": "latest-container",
                "image": "nginx:latest",
                "securityContext": {
                    "privileged": false,
                    "runAsNonRoot": true,
                    "readOnlyRootFilesystem": true,
                    "allowPrivilegeEscalation": false,
                },
                "resources": {"limits": {"cpu": "100m", "memory": "128Mi"}},
            }],
        },
    }
    count(result) > 0
}

# --- Test: Missing resource limits is denied ---

test_deny_no_resource_limits if {
    result := container_security.deny with input as {
        "spec": {
            "containers": [{
                "name": "no-limits",
                "image": "nginx:1.25",
                "securityContext": {
                    "privileged": false,
                    "runAsNonRoot": true,
                    "readOnlyRootFilesystem": true,
                    "allowPrivilegeEscalation": false,
                },
            }],
        },
    }
    count(result) > 0
}

# --- Test: Non-root not set is denied ---

test_deny_no_run_as_non_root if {
    result := container_security.deny with input as {
        "spec": {
            "containers": [{
                "name": "root-container",
                "image": "nginx:1.25",
                "securityContext": {
                    "privileged": false,
                    "readOnlyRootFilesystem": true,
                    "allowPrivilegeEscalation": false,
                },
                "resources": {"limits": {"cpu": "100m", "memory": "128Mi"}},
            }],
        },
    }
    count(result) > 0
}

# --- Test: Host PID denied ---

test_deny_host_pid if {
    result := container_security.deny with input as {
        "spec": {
            "hostPID": true,
            "containers": [{
                "name": "good-container",
                "image": "nginx:1.25",
                "securityContext": {
                    "privileged": false,
                    "runAsNonRoot": true,
                    "readOnlyRootFilesystem": true,
                    "allowPrivilegeEscalation": false,
                },
                "resources": {"limits": {"cpu": "100m", "memory": "128Mi"}},
            }],
        },
    }
    count(result) > 0
}

# --- Test: Compliant container is allowed ---

test_allow_compliant_container if {
    result := container_security.deny with input as {
        "spec": {
            "containers": [{
                "name": "good-container",
                "image": "nginx:1.25",
                "securityContext": {
                    "privileged": false,
                    "runAsNonRoot": true,
                    "readOnlyRootFilesystem": true,
                    "allowPrivilegeEscalation": false,
                },
                "resources": {"limits": {"cpu": "100m", "memory": "128Mi"}},
            }],
        },
    }
    count(result) == 0
}
