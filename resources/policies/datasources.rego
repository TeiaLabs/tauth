package tauth.datasources

import rego.v1

import data.tauth.utils.check_permission
import data.tauth.utils.build_permission_name

user_email_alias := alias if {
	handle := input.entity.handle
	email_domain = split(handle, "@")[1]
	alias := split(email_domain, ".")[0]
}

org_alias := trim_prefix(input.entity.owner_ref.handle, "/")

fallback_alias := user_email_alias if {
	org_alias == ""
} else := org_alias

alias := object.get(input.request.query, "db_alias", fallback_alias)

datasource_name := input.request.path.name

datasource_resources = mongodb.query(
	"resources",
	{
		"resource_collection": "datasources",
		"resource_identifier": datasource_name,
		"metadata.alias": alias,
	},
)


default return_size := 0

return_size = count(datasource_resources)

not_found := {"err": {"msg": "Datasource not found", "code": "404"}}


default ds2_has_admin := false

default ds2_has_read := false

default ds2_has_write := false

ds2_has_admin = not_found if {
	return_size == 0
}

ds2_has_admin = resource if {
	raw_resource := has_resource_access("admin")
	resource := parse_resource(raw_resource)
}

ds2_has_read = not_found if {
	return_size == 0
}

ds2_has_read = resource if {
	raw_resource := has_resource_access("read")
	resource := parse_resource(raw_resource)
}

ds2_has_read = resource if {
	raw_resource := has_resource_access("write")
	resource := parse_resource(raw_resource)
}

ds2_has_read = resource if {
	raw_resource := has_resource_access("admin")
	resource := parse_resource(raw_resource)
}

ds2_has_write = not_found if {
	return_size == 0
}

ds2_has_write = resource if {
	raw_resource := has_resource_access("write")
	resource := parse_resource(raw_resource)
}

ds2_has_write = resource if {
	raw_resource := has_resource_access("admin")
	resource := parse_resource(raw_resource)
}

has_resource_access(permission_level) := resource if {
	some resource in datasource_resources
	check_permission(build_permission_name(["ds", permission_level, resource._id]))
}
parse_resource(raw_resource) := resource if {
	resource = {
		"resource_identifier": raw_resource.resource_identifier,
		"resource_ref": raw_resource._id,
		"metadata": raw_resource.metadata,
	}
}

default read_many := []

read_many := {resources |
	ds_permissions := [permissions_name | is_ds_permission(input.permissions[i]); permissions_name := parse_permission(input.permissions[i].name)]
	filter := create_read_many_filter(ds_permissions)
	raw_resources = mongodb.query("resources", filter)
	some raw_resource in raw_resources
	resources = parse_resource(raw_resource)
}

parse_permission(perm_name) = split(perm_name, "::")[2]

create_read_many_filter(ds_permissions) := filter if {
	filter = {
		"_id": {"$in": ds_permissions},
		"metadata.alias": alias,
	}
}

is_ds_permission(permission) if {
	startswith(permission.name, "ds::")
}
