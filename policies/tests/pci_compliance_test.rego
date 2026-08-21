# ==============================================================================
# PCI-DSS Compliance Policy Tests
# ==============================================================================

package pci_compliance_test

import rego.v1

import data.pci_compliance

# --- Test: Plaintext password in env var denied ---

test_deny_plaintext_secret if {
    result := pci_compliance.deny with input as {
        "metadata": {
            "labels": {
                "app.kubernetes.io/part-of": "webhook",
                "app.kubernetes.io/managed-by": "argocd",
            },
        },
        "spec": {
            "serviceAccountName": "webhook-sa",
            "containers": [{
                "name": "app",
                "image": "app:1.0",
                "env": [{"name": "DB_PASSWORD", "value": "hunter2"}],
                "livenessProbe": {"httpGet": {"path": "/health"}},
                "readinessProbe": {"httpGet": {"path": "/health"}},
            }],
        },
    }
    count(result) > 0
}

# --- Test: Secret via valueFrom is allowed ---

test_allow_secret_from_ref if {
    result := pci_compliance.deny with input as {
        "metadata": {
            "labels": {
                "app.kubernetes.io/part-of": "webhook",
                "app.kubernetes.io/managed-by": "argocd",
            },
        },
        "spec": {
            "serviceAccountName": "webhook-sa",
            "containers": [{
                "name": "app",
                "image": "app:1.0",
                "env": [{
                    "name": "DB_PASSWORD",
                    "valueFrom": {"secretKeyRef": {"name": "db-secret", "key": "password"}},
                }],
                "livenessProbe": {"httpGet": {"path": "/health"}},
                "readinessProbe": {"httpGet": {"path": "/health"}},
            }],
        },
    }
    # Should have no secret-related denials
    secret_denials := {msg | some msg in result; contains(msg, "Req 2")}
    count(secret_denials) == 0
}

# --- Test: hostPath volume denied ---

test_deny_hostpath_volume if {
    result := pci_compliance.deny with input as {
        "metadata": {
            "labels": {
                "app.kubernetes.io/part-of": "webhook",
                "app.kubernetes.io/managed-by": "argocd",
            },
        },
        "spec": {
            "serviceAccountName": "webhook-sa",
            "volumes": [{"name": "data", "hostPath": {"path": "/var/data"}}],
            "containers": [{
                "name": "app",
                "image": "app:1.0",
                "livenessProbe": {"httpGet": {"path": "/health"}},
                "readinessProbe": {"httpGet": {"path": "/health"}},
            }],
        },
    }
    count(result) > 0
}

# --- Test: Default service account denied ---

test_deny_default_service_account if {
    result := pci_compliance.deny with input as {
        "metadata": {
            "labels": {
                "app.kubernetes.io/part-of": "webhook",
                "app.kubernetes.io/managed-by": "argocd",
            },
        },
        "spec": {
            "serviceAccountName": "default",
            "containers": [{
                "name": "app",
                "image": "app:1.0",
                "livenessProbe": {"httpGet": {"path": "/health"}},
                "readinessProbe": {"httpGet": {"path": "/health"}},
            }],
        },
    }
    count(result) > 0
}

# --- Test: Missing audit labels denied ---

test_deny_missing_labels if {
    result := pci_compliance.deny with input as {
        "metadata": {"labels": {}},
        "spec": {
            "serviceAccountName": "webhook-sa",
            "containers": [{
                "name": "app",
                "image": "app:1.0",
                "livenessProbe": {"httpGet": {"path": "/health"}},
                "readinessProbe": {"httpGet": {"path": "/health"}},
            }],
        },
    }
    count(result) > 0
}

# --- Test: Missing probes denied ---

test_deny_missing_probes if {
    result := pci_compliance.deny with input as {
        "metadata": {
            "labels": {
                "app.kubernetes.io/part-of": "webhook",
                "app.kubernetes.io/managed-by": "argocd",
            },
        },
        "spec": {
            "serviceAccountName": "webhook-sa",
            "containers": [{
                "name": "app",
                "image": "app:1.0",
            }],
        },
    }
    count(result) > 0
}
