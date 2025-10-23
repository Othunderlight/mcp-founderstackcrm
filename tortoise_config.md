# docs db config for tortoise orm and aerich:
### export TORTOISE_ORM="src.config.settings.TORTOISE_ORM"

### uv run --active aerich init -t "src.config.settings.TORTOISE_ORM"
>> Success writing aerich config to pyproject.toml
>> Success creating migrations folder ./migrations

### uv run --active aerich init-db

>>      Built mcp-remote @ file:///home/omar/Desktop/mcp-auth-test
>> Uninstalled 1 package in 0.52ms
>> Installed 1 package in 1ms
>> Success creating app migration folder migrations/models
>> Success generating initial migration file for app "models"
>> Success writing schemas to database "/home/omar/Desktop/mcp-auth-test/sqlite.db"