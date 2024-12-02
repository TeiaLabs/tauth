package tauth.melt_key

import rego.v1

default is_user := false
# REDO THIS POLICY
is_user if {
	input.infostar.authprovider_type == "melt-key"
}

default is_admin := false

is_admin if {
	is_user
	input.infostar.apikey_name == "default"
}

default is_superuser := false

is_superuser if {
	is_admin
	input.infostar.authprovider_org == "/"
}

default allow := {"authorized": false, "type": null}

allow := {"authorized": true, "type": "superuser"} if {
	is_superuser
} else := {"authorized": true, "type": "admin"} if {
	is_admin
} else := {"authorized": true, "type": "user"} if {
	is_user
}
