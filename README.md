exfonica
========

In theory this will deploy the exfonica website.

Requirements
------------

Docker.

Role Variables
--------------

None.

Dependencies
------------

None.

Example Playbook
----------------

```yaml
---
- name: "Deploy exfonica."
  hosts: exfonica 
    roles:
       - role: exfonica 
...
```

License
-------

Copyright (c) 2010-2017, Mirumee Software

Author Information
------------------

Updated by Alex Harris for ECLA.
