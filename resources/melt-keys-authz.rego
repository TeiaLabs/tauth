package tauth.melt_key

import rego.v1

default is_valid_user = false
default is_valid_admin = false
default is_valid_superuser = false

is_valid_user := true if {
    input.infostar.authprovider_type == "melt-key"
}

is_valid_admin := true if {
    is_valid_user
    input.infostar.apikey_name == "default"
}

is_valid_superuser := true if {
    is_valid_admin
    input.infostar.authprovider_org == "/"
}
