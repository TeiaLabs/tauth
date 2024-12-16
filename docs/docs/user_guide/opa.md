# Opa - Rego

You can check the examples in resources/policies. 
You can find more information about Rego [here](https://www.openpolicyagent.org/docs/latest/policy-language/).

## MongoDB Plugin
Tauth uses a custom opa runtime with support to connect to its own mongo database with restricted access.
Here is an example of how to use it.

```rego
package example

import rego.v1

allowed_users := {r |
	some r in mongodb.query("entities", {"owner_ref": "/teialabs"})
}
```

the mongodb.query method returns a list of objects that match your filter.
