MakinaCorpus Saltstack fork
=======================================

- We unmarked the makina corpus repo to be an official fork to keep only one branch, without release.
  This drastically improve git clones as the repo is for now < 50 mo (~160mo for saltstack's one)
- We contribute a lot to salt, but pullrequests will be done via other forks to avoid growing this repo size


In progress
------------
- [Make print_cli resilient on slow systems](https://github.com/makinacorpus/salt/commit/de5a19bac8ffeecf97e5242ca0b46bbbf2485cd0)


DIVERGENCES TO KEEP AT ALL COSTS:
----------------------------------
- [MC: lower virtual noice / 0877a28873bda58af9e391aac70b4dcd0a4f5f77](https://github.com/makinacorpus/salt/commit/0877a28873bda58af9e391aac70b4dcd0a4f5f77)
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
- 2015.8:
    - [service.dead](https://github.com/saltstack/salt/commit/49962880c3b230c7fbcd174c1dba93a88d284ffe)
- Retry states:
    - [856407ee27dff368d44fafdda9918de86f36ce47](https://github.com/saltstack/salt/commit/856407ee27dff368d44fafdda9918de86f36ce47)
    - [6658c2f12b07254b16b67691e1876ed36df9be26](https://github.com/saltstack/salt/commit/6658c2f12b07254b16b67691e1876ed36df9be26)
    - [aa7bfb422cfaff1b3fe92406393b3e8761c07724](https://github.com/saltstack/salt/commit/aa7bfb422cfaff1b3fe92406393b3e8761c07724)
    - [2ad701784acd929d245a3e8d82139af73fb75194](https://github.com/saltstack/salt/commit/2ad701784acd929d245a3e8d82139af73fb75194)
    - [8eeebf8112d22424f86263856d33195bfd9906cc](https://github.com/saltstack/salt/commit/8eeebf8112d22424f86263856d33195bfd9906cc)
    - [e706f8e6060a952526753a267e4b7cf375c8ca17](https://github.com/saltstack/salt/commit/e706f8e6060a952526753a267e4b7cf375c8ca17)

- [backport 1](https://github.com/makinacorpus/salt/commit/bed138bfa1e375ca65441c6821e398895d69d7aa)
- [backport 2](https://github.com/makinacorpus/salt/commit/1d11453c466c62712f741735cbffec4d7cdb0665)
- [backport 3](https://github.com/makinacorpus/salt/commit/0e0b8bedaed001b2359873c1be2d38e5376303df)
- [backport 4](https://github.com/makinacorpus/salt/commit/7150efe9661c9bc759b1e226f2f043822d051f92)
- [Backport mysql from salt/develop](https://github.com/makinacorpus/salt/commit/b7c109a35ba41c7c74d71b191ba6144bcf36d425)
- [backport docker.io from salt/develop](https://github.com/makinacorpus/salt/commit/0152b0478a63a80636265238f66566e0bfd445d9)
- [backport pip from salt/develop](https://github.com/makinacorpus/salt/commit/c6b79a229f7fc81d322e81c484c0b627f130c39c)
- [Handle ascii errors in jinja error logging](https://github.com/makinacorpus/salt/commit/b0020af512b78799793485cde620197f32994a85)

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
 - [Fix pkg.latest_version using localized output](https://github.com/makinacorpus/salt/commit/a1a0ab1bcd6cb08a84418735560835f716bee4fe)

