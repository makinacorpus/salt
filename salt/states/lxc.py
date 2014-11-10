# -*- coding: utf-8 -*-
'''
lxc / Spin up and control LXC containers
=========================================
'''
__docformat__ = 'restructuredtext en'
import traceback

# Import salt libs
from salt.exceptions import CommandExecutionError, SaltInvocationError


def present(name,
            running=True,
            clone_from=None,
            snapshot=False,
            profile=None,
            template=None,
            options=None,
            image=None,
            config=None,
            fstype=None,
            size=None,
            backing=None,
            vgname=None,
            lvname=None):
    '''
    .. versionchanged:: 2014.7.1
        The ``lxc.created`` state has been renamed to ``lxc.present``, and the
        ``lxc.cloned`` state has been merged into this state.

    Create the named container if it does not exist

    name
        The name of the container to be created

    running : True
        * If ``True``, ensure that the container is running
        * If ``False``, ensure that the container is stopped
        * If ``None``, do nothing with regards to the running state of the
          container

        .. versionadded:: 2014.7.1

    clone_from
        Create named container as a clone of the specified container

    snapshot : False
        Use Copy On Write snapshots (LVM). Only supported with ``clone_from``.

    profile
        Profile to use in container creation (see the :ref:`LXC Tutorial
        <lxc-tutorial-profiles>` for more information). Values in a profile
        will be overridden by the parameters listed below.

    **Container Creation Arguments**

    template
        The template to use. E.g., 'ubuntu' or 'fedora'. Conflicts with the
        ``image`` argument.

        .. note::

            The ``download`` template requires the following three parameters
            to be defined in ``options``:

            * **dist** - The name of the distribution
            * **release** - Release name/version
            * **arch** - Architecture of the container

            The available images can be listed using the :mod:`lxc.images
            <salt.modules.lxc.images>` function.

    options
        .. versionadded:: 2014.7.1

        Template-specific options to pass to the lxc-create command. These
        correspond to the long options (ones beginning with two dashes) that
        the template script accepts. For example:

        .. code-block:: yaml

            web01:
              lxc.present:
                - template: download
                - options:
                    dist: centos
                    release: 6
                    arch: amd64

        Remember to double-indent the options, due to :ref:`how PyYAML works
        <nested-dict-indentation>`.

    image
        A tar archive to use as the rootfs for the container. Conflicts with
        the ``template`` argument.

    backing
        The type of storage to use. Set to ``lvm`` to use an LVM group.
        Defaults to filesystem within /var/lib/lxc.

    fstype
        Filesystem type to use on LVM logical volume

    size
        Size of the volume to create. Only applicable if ``backing`` is set to
        ``lvm``.

    vgname : lxc
        Name of the LVM volume group in which to create the volume for this
        container. Only applicable if ``backing`` is set to ``lvm``.

    lvname
        Name of the LVM logical volume in which to create the volume for this
        container. Only applicable if ``backing`` is set to ``lvm``.
    '''
    ret = {'name': name,
           'result': True,
           'comment': 'Container \'{0}\' already exists'.format(name),
           'changes': {}}

    # Sanity checks
    create_type_count = len([x for x in (template, image, clone_from) if x])
    if create_type_count > 1:
        ret['result'] = False
        ret['comment'] = ('Only one of template, image, or clone_from is '
                          'permitted')
    elif create_type_count == 0:
        ret['result'] = False
        ret['comment'] = 'One of template, image, or clone_from is required'
    elif clone_from and not __salt__['lxc.exists'](clone_from):
        ret['result'] = False
        ret['comment'] = ('Clone source \'{0}\' does not exist'
                          .format(clone_from))
    if not ret['result']:
        return ret

    state = {'old': __salt__['lxc.state'](name)}
    if state['old'] is None:
        # Container does not exist

        action = 'cloned from {0}'.format(clone_from) if clone_from \
            else 'created'

        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = (
                'Container \'{0}\' will be {1}'.format(
                    name,
                    'cloned from {0}'.format(clone_from) if clone_from
                    else 'created')
            )
            return ret

        try:
            if clone_from:
                result = __salt__['lxc.clone'](name,
                                               clone_from,
                                               profile=profile,
                                               snapshot=snapshot,
                                               size=size,
                                               backing=backing,
                                               vgname=vgname)
            else:
                result = __salt__['lxc.create'](profile=profile,
                                                template=template,
                                                options=options,
                                                image=image,
                                                config=config,
                                                fstype=fstype,
                                                size=size,
                                                backing=backing,
                                                vgname=vgname,
                                                lvname=lvname)
        except (CommandExecutionError, SaltInvocationError) as exc:
            ret['result'] = False
            ret['comment'] = exc.strerror
        else:
            if clone_from:
                ret['comment'] = ('Cloned container \'{0}\' as \'{1}\''
                                  .format(clone_from, name))
            else:
                ret['comment'] = 'Created container \'{0}\''.format(name)

    if ret['result'] is not False:
        # Enforce the "running" parameter
        if running is None:
            # Don't do anything
            pass
        elif running:
            if result['state'] != 'running':
                error = ', but it could not be started'
                try:
                    state['new'] = __salt__['lxc.start'](name)['state']
                    if post != 'running':
                        ret['result'] = False
                        ret['comment'] += error
                except (SaltInvocationError, CommandExecutionError) as exc:
                    ret['result'] = False
                    ret['comment'] += '{0}: {1}'.format(error, exc)
        else:
            if result['state'] != 'stopped':
                error = ', but it could not be stopped'
                try:
                    state['new'] = __salt__['lxc.stop'](name)['state']
                    if post != 'stopped':
                        ret['result'] = False
                        ret['comment'] += error
                except (SaltInvocationError, CommandExecutionError) as exc:
                    ret['result'] = False
                    ret['comment'] += '{0}: {1}'.format(error, exc)

    if 'new' not in state:
        # Make sure we know the final state of the container before we return
        state['new'] = __salt__['lxc.state'](name)
    if state['old'] != state['new']:
        ret['changes']['state'] = state
    return ret


def absent(name):
    '''
    Ensure a container is not present, destroying it if present

    name
        Name of the container to destroy

    .. code-block:: yaml

        my_instance_name2:
          lxc.absent

    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Container \'{0}\' does not exist'.format(name)}

    if not __salt__['lxc.exists'](name):
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Container \'{0}\' would be removed'.format(name)
        return ret

    try:
        result = __salt__['lxc.destroy'](name)
    except (SaltInvocationError, CommandExecutionError) as exc:
        ret['result'] = False
        ret['comment'] = 'Failed to destroy container: {0}'.format(exc)
        return ret

    ret['changes'] = result['changes']
    ret['result'] = result['result']
    return ret


def running(name, restart=False):
    '''
    .. versionchanged:: 2014.7.1
        Renamed from **lxc.started** to **lxc.running**

    Ensure that a container is running

    .. note::

        This state does not enforce the existence of the named container, it
        just starts the container if it is not running. To ensure that the
        named container exists, use :mod:`lxc.present
        <salt.states.lxc.present>`.

    name
        The name of the container

    restart : False
        Restart container if it is already running

    .. code-block:: yaml

        web01:
          lxc.running
    '''
    ret = {'name': name,
           'result': True,
           'comment': 'Container \'{0}\' is already running'.format(name),
           'changes': {}}

    state = {'old': __salt__['lxc.state'](name)}
    if state['old'] is None:
        ret['result'] = False
        ret['comment'] = 'Container \'{0}\' does not exist'.format(name)
        return ret
    elif state['old'] == 'running' and not restart:
        return ret
    elif state['old'] == 'stopped' and restart:
        # No need to restart since container is not running
        restart = False

    if restart:
        if state['old'] != 'stopped':
            action = ('restart', 'restarted')
        else:
            action = ('start', 'started')
    else:
        if state['old'] == 'frozen':
            action = ('unfreeze', 'unfrozen')
        else:
            action = ('start', 'started')

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = ('Container \'{0}\' would be {1}'
                          .format(name, action[1]))
        return ret

    try:
        if state['old'] == 'frozen' and not restart:
            result = __salt__['lxc.unfreeze'](name)
        else:
            result = __salt__['lxc.start'](name, restart=restart)
    except (CommandExecutionError, SaltInvocationError) as exc:
        ret['result'] = False
        ret['comment'] = exc.strerror
        state['new'] = __salt__['lxc.state'](name)
    else:
        state['new'] = result['state']
        if state['new'] != 'running':
            ret['result'] = False
            ret['comment'] = ('Unable to {0} container \'{1}\''
                              .format(action[0], name))
        else:
            ret['comment'] = ('Container \'{0}\' was successfully {1}'
                              .format(name, action[1]))
        try:
            ret['changes']['restarted'] = result['restarted']
        except KeyError:
            pass

    if state['old'] != state['new']:
        ret['changes']['state'] = state
    return ret


def frozen(name, start=True):
    '''
    .. versionadded:: 2014.7.1

    Ensure that a container is frozen

    .. note::

        This state does not enforce the existence of the named container, it
        just freezes the container if it is running. To ensure that the named
        container exists, use :mod:`lxc.present <salt.states.lxc.present>`.

    name
        The name of the container

    start : True
        Start container first, if necessary. If ``False``, then this state will
        fail if the container is not running.

    .. code-block:: yaml

        web01:
          lxc.frozen

        web02:
          lxc.frozen:
            - start: False
    '''
    ret = {'name': name,
           'result': True,
           'comment': 'Container \'{0}\' is already frozen'.format(name),
           'changes': {}}

    state = {'old': __salt__['lxc.state'](name)}
    if state['old'] is None:
        ret['result'] = False
        ret['comment'] = 'Container \'{0}\' does not exist'.format(name)
    elif state['old'] == 'stopped' and not start:
        ret['result'] = False
        ret['comment'] = 'Container \'{0}\' is stopped'.format(name)

    if ret['result'] == False or state['old'] == 'frozen':
        return ret

    if state['old'] == 'stopped':
        action = ('start and freeze', 'started and frozen')
    else:
        action = ('freeze', 'frozen')

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = ('Container \'{0}\' would be {1}'
                          .format(name, action[1]))
        return ret

    try:
        result = __salt__['lxc.freeze'](name, start_first=start)
    except (CommandExecutionError, SaltInvocationError) as exc:
        ret['result'] = False
        ret['comment'] = exc.strerror
        state['new'] = __salt__['lxc.state'](name)
    else:
        state['new'] = result['state']
        if state['new'] != 'frozen':
            ret['result'] = False
            ret['comment'] = ('Unable to {0} container \'{1}\''
                              .format(action[0], name))
        else:
            ret['comment'] = ('Container \'{0}\' was successfully {1}'
                              .format(name, action[1]))
        try:
            ret['changes']['started'] = result['started']
        except KeyError:
            pass

    if state['old'] != state['new']:
        ret['changes']['state'] = state
    return ret


def stopped(name, kill=False):
    '''
    Ensure that a container is running

    .. note::

        This state does not enforce the existence of the named container, it
        just stops the container if it running or frozen. To ensure that the
        named container exists, use :mod:`lxc.present
        <salt.states.lxc.present>`, or use the :mod:`lxc.absent
        <salt.states.lxc.absent>` state to ensure that the container does not
        exist.

    name
        The name of the container

    kill : False
        Do not wait for the container to stop, kill all tasks in the container.
        Older LXC versions will stop containers like this irrespective of this
        argument.

        .. versionadded:: 2014.7.1

    .. code-block:: yaml

        web01:
          lxc.stopped
    '''
    ret = {'name': name,
           'result': True,
           'comment': 'Container \'{0}\' is already stopped'.format(name),
           'changes': {}}

    state = {'old': __salt__['lxc.state'](name)}
    if state['old'] is None:
        ret['result'] = False
        ret['comment'] = 'Container \'{0}\' does not exist'.format(name)
        return ret
    elif state['old'] == 'stopped':
        return ret

    if kill:
        action = ('force-stop', 'force-stopped')
    else:
        action = ('stop', 'stopped')

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = ('Container \'{0}\' would be {1}'
                          .format(name, action[1]))
        return ret

    try:
        result = __salt__['lxc.stop'](name, kill=kill)
    except (CommandExecutionError, SaltInvocationError) as exc:
        ret['result'] = False
        ret['comment'] = exc.strerror
        state['new'] = __salt__['lxc.state'](name)
    else:
        state['new'] = result['state']
        if state['new'] != 'stopped':
            ret['result'] = False
            ret['comment'] = ('Unable to {0} container \'{1}\''
                              .format(action[0], name))
        else:
            ret['comment'] = ('Container \'{0}\' was successfully {1}'
                              .format(name, action[1]))

    if state['old'] != state['new']:
        ret['changes']['state'] = state
    return ret


# Deprecated states
def created(name, **kwargs):
    '''
    State has been renamed, show deprecation notice
    '''
    salt.utils.warn_until(
        'Boron',
        'The lxc.created state has been renamed to lxc.present, please use '
        'lxc.present'
    )
    return present(name, **kwargs)


def cloned(name, orig, **kwargs):
    '''
    State has been renamed, show deprecation notice
    '''
    salt.utils.warn_until(
        'Boron',
        'The lxc.cloned state has been merged into the lxc.present state. '
        'Please update your states to use lxc.present, with the '
        '\'clone_from\' argument set to the name of the clone source.'
    )
    return present(name, clone_from=orig, **kwargs)
