# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["test_mutations 1"] = {
    "data": {
        "introduceShip": {
            "ship": {"id": "U2hpcDo5", "name": "Peter"},
            "faction": {
                "name": "Alliance to Restore the Republic",
                "ships": {
                    "edges": [
                        {"node": {"id": "U2hpcDox", "name": "X-Wing"}},
                        {"node": {"id": "U2hpcDoy", "name": "Y-Wing"}},
                        {"node": {"id": "U2hpcDoz", "name": "A-Wing"}},
                        {"node": {"id": "U2hpcDo0", "name": "Millenium Falcon"}},
                        {"node": {"id": "U2hpcDo1", "name": "Home One"}},
                        {"node": {"id": "U2hpcDo5", "name": "Peter"}},
                    ]
                },
            },
        }
    }
}
