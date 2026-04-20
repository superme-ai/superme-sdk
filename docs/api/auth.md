# Authentication

Get your API key at [superme.ai/settings](https://superme.ai/settings) → **API Keys**.

```python
import os
from superme_sdk import SuperMeClient

client = SuperMeClient(api_key=os.environ["SUPERME_API_KEY"])
```

Or use the token helpers below to load it from disk or environment automatically:

::: superme_sdk.auth
