package tauth.datasources

import rego.v1

admin_resources := _filter_resource("admin:")

write_resources := admin_resources | _filter_resource("write:")

read_resources := _filter_resource("read:") | write_resources

default has_admin := false

has_admin := resource if {
	resource := has_resource_access(admin_resources)
}

default has_write := false

has_write := resource if {
	resource := has_resource_access(write_resources)
}

default has_read := false

has_read := resource if {
	resource := has_resource_access(read_resources)
}

has_resource_access(resources) := resource if {
	some resource in resources
	resource.id == input.request.path.name
}

# set comprehension for allowed resources
_filter_resource(permission_prefix) := {allowed_ids |
	some permission in input.permissions
	startswith(permission.name, permission_prefix)
	some r in input.resources
	endswith(permission.name, r._id)
	allowed_ids := r.ids[_]
}
