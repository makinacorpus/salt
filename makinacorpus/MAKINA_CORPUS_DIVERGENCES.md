MakinaCorpus Saltstack fork
=======================================

- We unmarked the makina corpus repo to be an official fork to keep only one branch, without release.
  This drastically improve git clones as the repo is for now < 50 mo (~160mo for saltstack's one)
- We contribute a lot to salt, but pullrequests will be done via other forks to avoid growing this repo size

DIVERGENCES TO KEEP AT ALL COSTS:
----------------------------------
- [protect VT logs from unicode strings / 6039f1a8327892978da220b50f30e002c97d0a51](https://github.com/makinacorpus/salt/commit/6039f1a8327892978da220b50f30e002c97d0a51)

    - Upstream did not accepted this trivial changeset, even as a later changeable changeset, issue is pending for more than a while here:

        - https://github.com/saltstack/salt/issues/21441
        - https://github.com/saltstack/salt/pull/20918

- [raise appropriate AttributeEror for certain collectionmapping attributes / 86afa91b189cfe80b497cbe9d5489bf2212acc29](https://github.com/makinacorpus/salt/commit/86afa91b189cfe80b497cbe9d5489bf2212acc29)

    - for tests reasons only, but in spirit the loader doesnt respect without the patch that much a dict-like interface toward the copy method.
    - https://github.com/saltstack/salt/pull/22940#issuecomment-95259610
    - proposed as fix but unrelated: https://github.com/saltstack/salt/pull/22950
    - tried to rediscuss on https://github.com/saltstack/salt/issues/23317



Backports
-----------
- [backport 1](https://github.com/makinacorpus/salt/commit/bed138bfa1e375ca65441c6821e398895d69d7aa)
- [backport 2](https://github.com/makinacorpus/salt/commit/1d11453c466c62712f741735cbffec4d7cdb0665)
- [backport 3](https://github.com/makinacorpus/salt/commit/0e0b8bedaed001b2359873c1be2d38e5376303df)
- [backport 4](https://github.com/makinacorpus/salt/commit/7150efe9661c9bc759b1e226f2f043822d051f92)


Removed changesets
-------------------
- [environ hotfix / 337ed10cfc9f53724e653e9d3ccef317005d9817](https://github.com/makinacorpus/salt/commit/337ed10cfc9f53724e653e9d3ccef317005d9817)

       - See https://github.com/saltstack/salt/issues/24480

Notes
-------
- zcbuildout now living in [makina-states/salt_fork](https://github.com/makinacorpus/makina-states/tree/master/salt_fork).

    - [module](https://github.com/makinacorpus/makina-states/blob/master/salt_fork/modules/zcbuildout.py)
    - [state](https://github.com/makinacorpus/makina-states/blob/master/salt_fork/states/zcbuildout.py)


PR
----
 - [extpillar](https://github.com/saltstack/salt/pull/31380/commits)

