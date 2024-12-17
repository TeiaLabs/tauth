package tauth.datasources

import rego.v1

import data.tauth.utils.check_permission
import data.tauth.utils.build_permission_name

org_alias := trim_prefix(input.entity.owner_ref.handle, "/")

alias := object.get(input.request.query, "db_alias", org_alias)

datasource_resources = mongodb.query(
	"resources",
	{
		"resource_collection": "datasources",
		"resource_identifier": datasource_name,
		"metadata.alias": alias,
	},
)

datasource_name := input.request.path.name


not_found := {"msg": "datasource not found"}

default ds2_has_admin := false

default ds2_has_read := false

default ds2_has_write := false

ds2_has_admin = not_found if {
	count(datasource_resources) == 0
}

ds2_has_admin = resource if {
	raw_resource := has_resource_access("admin")
	resource := parse_resource(raw_resource)
}

ds2_has_read = not_found if {
	count(datasource_resources) == 0
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
	count(datasource_resources) == 0
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
	check_permission(build_permission_name(["ds", permission_level, resource.id]))
}

parse_resource(raw_resource) := resource if {
	resource = {
		"resource_identifier": raw_resource.resource_identifier,
		"resource_ref": raw_resource.id,
		"metadata": raw_resource.metadata,
	}
}