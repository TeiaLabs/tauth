# Authorization Service

- Roles stored in TAuth

- Policies
  - Comprised of
    - Name (e.g., "read_files", "is_admin", "is_owner")
    - Actor (user)
    - Action (e.g., read, write, delete)
    - Resource(s) (e.g., context, time of day, etc.)
    - Rules (authorization logic)
  - Types
    - Role-based Access Control (RBAC)
    - Attribute-based Access Control (ABAC)
    - Relationship-based Access Control (ReBAC)
    - Discretionary Access Control (DAC)
    - Mandatory Access Control (MAC)
    - Rule-based Access Control (RBAC)
  - Policy as Code (PaC)
    - Languages
      - Open Policy Agent (OPA) - Rego (https://www.openpolicyagent.org/, https://www.openpolicyagent.org/docs/latest/policy-language/)
      - Amazon - Cedar (https://www.cedarpolicy.com/en)
      - OpenFPGA (https://openfga.dev/)
      - Oso - Polar (https://www.osohq.com/, https://www.osohq.com/docs/reference/polar)
    - Sub-policies (use policies inside other policies)
  - Policy store (per service, stores rules/"authorization logic")
  - Design details
    - `authorize` function
    - Administration endpoints (e.g., CRUD)
    - Decision (i.e., which policies apply to a given request)
    - Enforcement (i.e., how to enforce the policies)
    - How do policies access the context?
      - Policy Information Point (PIP)
      - Store role permissions (e.g., `user` -> ["read:files", "write:files"])
      - Store role-resource associations
      - Would be necessary in case we need to check for trial data (e.g., how many times a user has downloaded a file)
      - We could store locally-scoped roles for RBAC
      - If a policy could generate filters, we could use them to restrict DB access (this is what Oso's Polar does)

- FastAPI Middleware
