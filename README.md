# ADK Crash Course: From Beginner to Expert

[This Codelab](https://codelabs.developers.google.com/onramp/instructions), but you don't need Colab or Jupyter Notebook

> [!NOTE]
> You will notice there's not a lot of memory or runners throughout the example code here
> compared to the Codelab, and that's because running `adk` here already creates/manages
> that for you


## Requirements
```sh
pip install -r requirements.txt
```

- create `.env` file with the following ENV VARs:
```
GOOGLE_API_KEY = "Thequickbrownfoxjumpsoverthelazydog!"
GOOGLE_GENAI_USE_VERTEXAI = "False"
```
or...
```
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT="my-gcp-project-id-with-vertex-ai-apis-enabled"
GOOGLE_CLOUD_LOCATION=global
```

> [!TIP]
> Add `**/.env` to your `.gitignore` so you don't accidentally commit any API keys to your repo
> I already have it in my repo, so if you cloned this, you should be ok

> [!WARNING]
> Don't just take my work for it! Check it yourself to make sure you're not committing anything sensitive!


## Codelab
> [!IMPORTANT]
> Replace import statement:
> `from google.adk.tools import google_search` with
> `from google.adk.tools.google_search_tool import GoogleSearchTool`
> and call tool by referencing `GoogleSearchTool()` if standalone,
> or as `GoogleSearchTool(bypass_multi_tools_limit=True)` when using with other tools


### Colab 1: Tools & Memory
- Day Trip Agent
- Weather Agent
- Trip Data Concierge Agent
- Multi Day Trip Agent

> [!NOTE]
> For "Scenario 3b: Agent WITHOUT Memory",
> start a new session after the first question :)


### Colab 2: MultiAgents
- Find & Navigate Agent
- Iterative Planner Agent
- Parallel Planner Agent


### Challenge
Put together the ULTIMATE Router Agent mentioned in the Codelab by combining:
- Foodie Agent
- Find & Navigate Agent
- Iterative Planner Agent
- Parallel Planner Agent
- Day Trip Agent
