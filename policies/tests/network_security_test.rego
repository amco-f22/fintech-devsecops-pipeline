# ==============================================================================
# Network Security Policy Tests
# ==============================================================================

package network_security_test

import rego.v1

import data.network_security

# --- Test: hostNetwork denied ---

test_deny_host_network if {
    result := network_security.deny with input as {
        "spec": {
            "hostNetwork": true,
            "containers": [{"name": "app", "image": "app:1.0"}],
        },
    }
    count(result) > 0
}

# --- Test: hostPort denied ---

test_deny_host_port if {
    result := network_security.deny with input as {
        "spec": {
            "containers": [{
                "name": "app",
                "image": "app:1.0",
                "ports": [{"containerPort": 8080, "hostPort": 8080}],
            }],
        },
    }
    count(result) > 0
}

# --- Test: NodePort service denied ---

test_deny_nodeport_service if {
    result := network_security.deny with input as {
        "kind": "Service",
        "metadata": {"name": "bad-service"},
        "spec": {"type": "NodePort"},
    }
    count(result) > 0
}

# --- Test: Public LoadBalancer denied ---

test_deny_public_loadbalancer if {
    result := network_security.deny with input as {
        "kind": "Service",
        "metadata": {
            "name": "public-lb",
            "annotations": {},
        },
        "spec": {"type": "LoadBalancer"},
    }
    count(result) > 0
}

# --- Test: Internal LoadBalancer allowed ---

test_allow_internal_loadbalancer if {
    result := network_security.deny with input as {
        "kind": "Service",
        "metadata": {
            "name": "internal-lb",
            "annotations": {
                "service.beta.kubernetes.io/aws-load-balancer-internal": "true",
            },
        },
        "spec": {"type": "LoadBalancer"},
    }
    # Should not contain any LoadBalancer denial
    not_lb_denied := {msg | some msg in result; contains(msg, "LoadBalancer")}
    count(not_lb_denied) == 0
}

# --- Test: Compliant pod allowed ---

test_allow_compliant_pod if {
    result := network_security.deny with input as {
        "spec": {
            "hostNetwork": false,
            "dnsPolicy": "ClusterFirst",
            "containers": [{
                "name": "app",
                "image": "app:1.0",
                "ports": [{"containerPort": 8080}],
            }],
        },
    }
    count(result) == 0
}
