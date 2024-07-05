
# TODOs (air-management)

- getsert (upsert too, *sert_many|one) genérico! (com testes) (em nossa defesa copilot que falou dos testes)
- fastbaby (all of it) +memetrics +logging (com testes)
- entity intermediate? parametrizable callable factories (com testes)
- redbaby subtypes (com testes)
- error handling (http-error-schemas, mensagens de erro boas) (com testes)
- documentação (com testes :play-button:)

## queries

- all users of an app
- recent activity of a user

## serious todos

- upon user login, save
  - with which authprovider the user authenticated
  - from which org the user authenticated
  - the user's ip address

## syntax for multiple values with the same key in a query string

?extra.key=1&extra.value=2&extra.key=3&extra.value=4
extra_key = [1, 3]
extra_value = [2, 4]

## roadmapinha

1. docs
2. infostar vs creator
3. tauth migration scripts
   1. tauth legacy organizations -> entities
4. deploy to AWS
5. integration meltingface
6. override headers for infostar fields
7. integration memetrics
8. tests
