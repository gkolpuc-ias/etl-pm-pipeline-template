To finish you project setup setup your config in `tasks.py` and execute `invoke init`

1. Go to `tasks.py` and edit following lines (use lower case characters and '-' as separator):

```
config = {
        'DAG_NAME': 'xyz-daily',
        'PARTNER_NAME': 'xyz',
        'SERVICE_NAME': 'daily-processor',
    }
```

2. execute `invoke init` to finish setup
3. Remove `init` function from `tasks.py`

To complete your repo setup follow https://github.com/integralads/re-documentation/blob/master/jenkins-ng/getting-started.md page get CI_CD in place.