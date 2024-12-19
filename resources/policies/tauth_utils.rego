package tauth.utils

import rego.v1

build_permission_name(parts) = concat("::", parts)

check_permission(target) if {
	some permission in input.permissions
	permission.name == target 
}