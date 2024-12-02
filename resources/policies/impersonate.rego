package tauth.permissions

import rego.v1

import data.tauth.utils.check_permission
import data.tauth.utils.build_permission_name


default allow := false
allow if {
    check_permission(build_permission_name(["tauth", "impersonator"]))
}
