# ADK + Database Sessions
If you want to run the examples with a simple, local DB as your session manager, use the agent code provided in this directory.

- to run:
```sh
adk web --session_service_uri="sqlite+aiosqlite:///./adk_sessions.db"
```

It should create a local *adk_sessions.db* file, which you can query with the `sqlite3_query_sessions.py` script I provided.


## Want to dive a little deeper?
You can connect to your local SQLite3 DB file and do more in-depth queries:
```sh
sqlite3 adk_sessions.db
```

- list tables
```sql 
.tables
```

- query contents of events table (which should show your chat history)
```sql
select * from events;
```
