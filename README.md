To finish you project setup your config in `tasks.py` and execute `invoke init` with parameters.


1. execute `invoke init <PARTNER_NAME> <DAG_NAME> <SERVICE_NAME>` to finish setup
```
Help:
        DAG_NAME - name of the initial airflow dag to be created
        PARTNER_NAME - name of the partner e.g. 'facebook', 'youtube'
        SERVICE_NAME - name of the initial service to be created
```
2. Remove `init` function from `tasks.py`

To complete your repo setup follow https://github.com/integralads/re-documentation/blob/master/jenkins-ng/getting-started.md page get CI_CD in place.