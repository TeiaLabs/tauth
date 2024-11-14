package tauth.datasources

import rego.v1

import data.tauth.utils.build_permission_name

admin_resources := _filter_resource(build_permission_name(["ds", "admin"]))

write_resources := admin_resources | _filter_resource(build_permission_name(["ds", "write"]))

read_resources := _filter_resource(build_permission_name(["ds", "read"])) | write_resources

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
	has_valid_alias(resource)
}

has_valid_alias(resource) if {
	org_alias := trim_prefix(input.entity.owner_ref.handle, "/")
	alias := object.get(input.request.query, "db_alias", org_alias)
	resource.metadata.alias == alias
}

# set comprehension for allowed resources
_filter_resource(permission_prefix) := {allowed_ids |
	some permission in input.permissions
	startswith(permission.name, permission_prefix)
	some r in input.resources
	endswith(permission.name, r._id)
	some id in r.ids
	allowed_ids = {
		"id": id.id,
		"resource_ref": r._id,
		"metadata": id.metadata,
	}
}
