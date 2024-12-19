# OPA - Rego Integration

The power of OPA lies in its context. Tauth injects the following context:

- The set of user permissions
- Original request
- Tauth request
- User entity

You can interact with the context using the `input` variable.

### Example Usage

```rego
package example

default allow = false

# Allow only TeiaLabs users
allow {
    input.entity.owner_ref.handle == "/teialabs"
}
```

## Tauth Utilities Package

Tauth provides a utility Rego package called `tauth.utils`. Below is an example demonstrating its usage:

```rego
package tauth.permissions

import rego.v1
import data.tauth.utils.check_permission
import data.tauth.utils.build_permission_name

default allow := false

# Allow access if the user has the "tauth::impersonator" permission
allow if {
    check_permission(build_permission_name(["tauth", "impersonator"]))
}
```

### Utility Functions

- `check_permission`: Iterates through the user's permissions to check if the specified permission exists.
- `build_permission_name`: Helper function to build a permission name based on a list of strings, following Tauth's naming convention (separated by `::`).

You can find additional examples in `resources/policies`.  
For more information about Rego, refer to the [OPA documentation](https://www.openpolicyagent.org/docs/latest/policy-language/).

---

## MongoDB Plugin

Tauth uses a custom OPA runtime that supports connecting to its MongoDB instance with restricted access. 
For now, this plugin only has access to the `resources` collection.
Here's an example of how to query the database:

```rego
package example

import rego.v1

# Fetch allowed users from MongoDB
allowed_users := {r |
    some r in mongodb.query("resources", {"resource_collection": "datasources"})
}
```

The `mongodb.query` method returns a list of objects that match the specified filter.
