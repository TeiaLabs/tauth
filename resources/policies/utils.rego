package tauth.utils

import rego.v1

build_permission_name(parts) = concat("::", parts)