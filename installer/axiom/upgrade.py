# -*- test-case-name: axiom.test.test_upgrading -*-
_upgradeRegistry = {}

def registerUpgrader(upgrader, typeName, oldVersion, newVersion):
    """
    Register a callable which can perform a schema upgrade between two
    particular versions.

    @param upgrader: A one-argument callable which will upgrade an object.  It
    is invoked with an instance of the old version of the object.
    @param typeName: The database typename for which this is an upgrader.
    @param oldVersion: The version from which this will upgrade.
    @param newVersion: The version tow hich this will upgrade.  This must be
    exactly one greater than C{oldVersion}.
    """
    # assert (typeName, oldVersion, newVersion) not in _upgradeRegistry, "duplicate upgrader"

    # ^ this makes the tests blow up so it's just disabled for now; perhaps we
    # should have a specific test mode
    assert newVersion - oldVersion == 1, "read the doc string"
    assert isinstance(typeName, str), "read the doc string"
    _upgradeRegistry[typeName, oldVersion, newVersion] = upgrader

def registerAttributeCopyingUpgrader(itemType, fromVersion, toVersion):
    """
    Register an upgprader for C{itemType}, from C{fromVersion} to C{toVersion},
    which will copy all attributes from the legacy item to the new item.

    @param itemType: L{axiom.item.Item} subclass
    @return: None
    """
    def upgrader(old):
        return old.upgradeVersion(itemType.typeName, fromVersion, toVersion,
                                  **dict((str(name), getattr(old, name))
                                            for (name, _) in old.getSchema()))
    registerUpgrader(upgrader, itemType.typeName, fromVersion, toVersion)


def registerDeletionUpgrader(itemType, fromVersion, toVersion):
    """
    Register an upgrader for C{itemType}, from C{fromVersion} to C{toVersion},
    which will delete the item from the database.

    @param itemType: L{axiom.item.Item} subclass
    @return: None
    """
    # XXX This should actually do something more special so that a new table is
    # not created and such.
    def upgrader(old):
        old.deleteFromStore()
        return None
    registerUpgrader(upgrader, itemType.typeName, fromVersion, toVersion)


def upgradeAllTheWay(o, typeName, version):
    while True:
        try:
            upgrader = _upgradeRegistry[typeName, version, version + 1]
        except KeyError:
            break
        else:
            o = upgrader(o)
            version += 1
    return o
