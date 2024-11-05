package tauth.datasources

import rego.v1



admin_filtered_resources = [resource |
	some i
	resource = input.resources[i]
	has_ds_admin_permission(resource)
]

read_filtered_resources = [resource |
	some i
	resource = input.resources[i]
	has_ds_read_permission(resource)
]

write_filtered_resources = [resource |
	some i
	resource = input.resources[i]
	has_ds_write_permission(resource)
]

has_ds_admin_permission(resource) if {
	some j
	resource.permissions[j].name == "DS-admin"
	startswith(resource.permissions[j].entity_handle, "/datasources")

}

has_ds_read_permission(resource) if {
	some j
	resource.permissions[j].name == "DS-read"
	startswith(resource.permissions[j].entity_handle, "/datasources")
}

has_ds_write_permission(resource) if {
	some j
	resource.permissions[j].name == "DS-write"
	startswith(resource.permissions[j].entity_handle, "/datasources")
}