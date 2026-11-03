# Консоль параметрлері

`self` параметрін бермеңіз. Қалғандары key=value форматында енгізіледі.

- `project(self, id, name)`
- `item(self, project, id, path, version, content)`
- `items(self, project)`
- `request(self, id, project, item, version, content, description)`
- `requests(self, id=None)`
- `decide(self, id, approve, approver, reason)`
- `apply(self, id, commit, test)`
- `baseline(self, id, project, approver, previous=None)`
- `get_baseline(self, id)`
- `compare(self, old, new)`
- `release(self, project, version, baseline)`
- `report(self, output=None)`
