# -*- coding: utf-8 -*-
'''
Utils for making various web calls. Primarily designed for REST, SOAP, webhooks
and the like, but also useful for basic HTTP testing.

.. versionaddedd:: 2015.2
'''

# Import python libs
from __future__ import absolute_import
import json
import logging
# pylint: disable=no-name-in-module
import salt.ext.six.moves.http_cookiejar
import salt.ext.six.moves.urllib as urllib
# pylint: enable=no-name-in-module
from salt.ext.six import string_types
from salt._compat import ElementTree as ET
import os.path
import pprint
import socket

import ssl
try:
    from ssl import CertificateError  # pylint: disable=E0611
    from ssl import match_hostname  # pylint: disable=E0611
    HAS_MATCHHOSTNAME = True
except ImportError:
    try:
        from backports.ssl_match_hostname import CertificateError
        from backports.ssl_match_hostname import match_hostname
        HAS_MATCHHOSTNAME = True
    except ImportError:
        try:
            from salt.ext.ssl_match_hostname import CertificateError
            from salt.ext.ssl_match_hostname import match_hostname
            HAS_MATCHHOSTNAME = True
        except ImportError:
            HAS_MATCHHOSTNAME = False

# Import salt libs
import salt.utils
import salt.utils.xmlutil as xml
import salt.loader
import salt.config
import salt.version
from salt._compat import ElementTree as ET
from salt.template import compile_template
from salt import syspaths

# Import 3rd party libs
import salt.ext.six as six
# pylint: disable=import-error,no-name-in-module
import salt.ext.six.moves.http_client
import salt.ext.six.moves.http_cookiejar
import salt.ext.six.moves.urllib.request as urllib_request
from salt.ext.six.moves.urllib.error import URLError
# pylint: enable=import-error,no-name-in-module

# Don't need a try/except block, since Salt depends on tornado
import tornado.httputil
from tornado.httpclient import HTTPClient

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False

try:
    import certifi
    HAS_CERTIFI = True
except ImportError:
    HAS_CERTIFI = False

log = logging.getLogger(__name__)
JARFILE = os.path.join(syspaths.CACHE_DIR, 'cookies.txt')
SESSIONJARFILE = os.path.join(syspaths.CACHE_DIR, 'cookies.session.p')
USERAGENT = 'Salt/{0}'.format(salt.version.__version__)


def query(url,
          method='GET',
          params=None,
          data=None,
          data_file=None,
          header_dict=None,
          header_list=None,
          header_file=None,
          username=None,
          password=None,
          auth=None,
          decode=False,
          decode_type='auto',
          status=False,
          headers=False,
          text=False,
          cookies=None,
          cookie_jar=JARFILE,
          cookie_format='lwp',
          persist_session=False,
          session_cookie_jar=SESSIONJARFILE,
          data_render=False,
          data_renderer=None,
          header_render=False,
          header_renderer=None,
          template_dict=None,
          test=False,
          test_url=None,
          node='minion',
          port=80,
          opts=None,
          backend='tornado',
          requests_lib=None,
          ca_bundle=None,
          verify_ssl=None,
          cert=None,
          text_out=None,
          headers_out=None,
          decode_out=None,
          stream=False,
          handle=False,
          agent=USERAGENT,
          **kwargs):
    '''
    Query a resource, and decode the return data
    '''
    ret = {}

    if opts is None:
        if node == 'master':
            opts = salt.config.master_config(
                os.path.join(syspaths.CONFIG_DIR, 'master')
            )
        elif node == 'minion':
            opts = salt.config.minion_config(
                os.path.join(syspaths.CONFIG_DIR, 'minion')
            )
        else:
            opts = {}

    if requests_lib is None:
        requests_lib = opts.get('requests_lib', False)

    if requests_lib is True:
        log.warn('Please set "backend" to "requests" instead of setting '
                 '"requests_lib" to "True"')

        if HAS_REQUESTS is False:
            ret['error'] = ('http.query has been set to use requests, but the '
                            'requests library does not seem to be installed')
            log.error(ret['error'])
            return ret

        backend = 'requests'

    else:
        requests_log = logging.getLogger('requests')
        requests_log.setLevel(logging.WARNING)

    if ca_bundle is None:
        ca_bundle = get_ca_bundle(opts)

    if verify_ssl is None:
        verify_ssl = opts.get('verify_ssl', True)

    if cert is None:
        cert = opts.get('cert', None)

    if data_file is not None:
        data = _render(
            data_file, data_render, data_renderer, template_dict, opts
        )

    log.debug('Using {0} Method'.format(method))
    if method == 'POST':
        log.trace('POST Data: {0}'.format(pprint.pformat(data)))

    if header_file is not None:
        header_tpl = _render(
            header_file, header_render, header_renderer, template_dict, opts
        )
        if isinstance(header_tpl, dict):
            header_dict = header_tpl
        else:
            header_list = header_tpl.splitlines()

    if header_dict is None:
        header_dict = {}

    if header_list is None:
        header_list = []

    if persist_session is True and HAS_MSGPACK:
        # TODO: This is hackish; it will overwrite the session cookie jar with
        # all cookies from this one connection, rather than behaving like a
        # proper cookie jar. Unfortunately, since session cookies do not
        # contain expirations, they can't be stored in a proper cookie jar.
        if os.path.isfile(session_cookie_jar):
            with salt.utils.fopen(session_cookie_jar, 'r') as fh_:
                session_cookies = msgpack.load(fh_)
            if isinstance(session_cookies, dict):
                header_dict.update(session_cookies)
        else:
            with salt.utils.fopen(session_cookie_jar, 'w') as fh_:
                msgpack.dump('', fh_)

    for header in header_list:
        comps = header.split(':')
        if len(comps) < 2:
            continue
        header_dict[comps[0].strip()] = comps[1].strip()

    if username and password:
        auth = (username, password)
    else:
        auth = None

    if agent == USERAGENT:
        agent = '{0} http.query()'.format(agent)
    header_dict['User-agent'] = agent

    if backend == 'requests':
        sess = requests.Session()
        sess.auth = auth
        sess.headers.update(header_dict)
        log.trace('Request Headers: {0}'.format(sess.headers))
        sess_cookies = sess.cookies
        sess.verify = verify_ssl
    elif backend == 'urllib2':
        sess_cookies = None
    else:
        # Tornado
        sess_cookies = None

    if cookies is not None:
        if cookie_format == 'mozilla':
            sess_cookies = salt.ext.six.moves.http_cookiejar.MozillaCookieJar(cookie_jar)
        else:
            sess_cookies = salt.ext.six.moves.http_cookiejar.LWPCookieJar(cookie_jar)
        if not os.path.isfile(cookie_jar):
            sess_cookies.save()
        else:
            sess_cookies.load()

    if test is True:
        if test_url is None:
            return {}
        else:
            url = test_url
            ret['test'] = True

    if backend == 'requests':
        req_kwargs = {}
        if stream is True:
            if requests.__version__[0] == '0':
                # 'stream' was called 'prefetch' before 1.0, with flipped meaning
                req_kwargs['prefetch'] = False
            else:
                req_kwargs['stream'] = True

        # Client-side cert handling
        if cert is not None:
            if isinstance(cert, six.string_types):
                if os.path.exists(cert):
                    req_kwargs['cert'] = cert
            elif isinstance(cert, tuple):
                if os.path.exists(cert[0]) and os.path.exists(cert[1]):
                    req_kwargs['cert'] = cert
            else:
                log.error('The client-side certificate path that was passed is '
                          'not valid: {0}'.format(cert))

        result = sess.request(
            method, url, params=params, data=data, **req_kwargs
        )
        result.raise_for_status()
        if stream is True or handle is True:
            return {'handle': result}

        result_status_code = result.status_code
        result_headers = result.headers
        result_text = result.text
        result_cookies = result.cookies
    elif backend == 'urllib2':
        request = urllib_request.Request(url, data)
        handlers = [
            urllib_request.HTTPHandler,
            urllib_request.HTTPCookieProcessor(sess_cookies)
        ]

        if url.startswith('https') or port == 443:
            hostname = request.get_host()
            handlers[0] = urllib_request.HTTPSHandler(1)
            if not HAS_MATCHHOSTNAME:
                log.warn(('match_hostname() not available, SSL hostname checking '
                         'not available. THIS CONNECTION MAY NOT BE SECURE!'))
            elif verify_ssl is False:
                log.warn(('SSL certificate verification has been explicitly '
                         'disabled. THIS CONNECTION MAY NOT BE SECURE!'))
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((hostname, 443))
                sockwrap = ssl.wrap_socket(
                    sock,
                    ca_certs=ca_bundle,
                    cert_reqs=ssl.CERT_REQUIRED
                )
                try:
                    match_hostname(sockwrap.getpeercert(), hostname)
                except CertificateError as exc:
                    ret['error'] = (
                        'The certificate was invalid. '
                        'Error returned was: {0}'.format(
                            pprint.pformat(exc)
                        )
                    )
                    return ret

                # Client-side cert handling
                if cert is not None:
                    cert_chain = None
                    if isinstance(cert, six.string_types):
                        if os.path.exists(cert):
                            cert_chain = (cert)
                    elif isinstance(cert, tuple):
                        if os.path.exists(cert[0]) and os.path.exists(cert[1]):
                            cert_chain = cert
                    else:
                        log.error('The client-side certificate path that was '
                                  'passed is not valid: {0}'.format(cert))
                        return
                    if hasattr(ssl, 'SSLContext'):
                        # Python >= 2.7.9
                        context = ssl.SSLContext.load_cert_chain(*cert_chain)
                        handlers.append(urllib_request.HTTPSHandler(context=context))  # pylint: disable=E1123
                    else:
                        # Python < 2.7.9
                        cert_kwargs = {
                            'host': request.get_host(),
                            'port': port,
                            'cert_file': cert_chain[0]
                        }
                        if len(cert_chain) > 1:
                            cert_kwargs['key_file'] = cert_chain[1]
                        handlers[0] = salt.ext.six.moves.http_client.HTTPSConnection(**cert_kwargs)

        opener = urllib_request.build_opener(*handlers)
        for header in header_dict:
            request.add_header(header, header_dict[header])
        request.get_method = lambda: method
        try:
            result = opener.open(request)
        except URLError as exc:
            return {'Error': str(exc)}
        if stream is True or handle is True:
            return {'handle': result}

        result_status_code = result.code
        result_headers = result.headers.headers
        result_text = result.read()
    else:
        # Tornado
        req_kwargs = {}

        # Client-side cert handling
        if cert is not None:
            if isinstance(cert, six.string_types):
                if os.path.exists(cert):
                    req_kwargs['client_cert'] = cert
            elif isinstance(cert, tuple):
                if os.path.exists(cert[0]) and os.path.exists(cert[1]):
                    req_kwargs['client_cert'] = cert[0]
                    req_kwargs['client_key'] = cert[1]
            else:
                log.error('The client-side certificate path that was passed is '
                          'not valid: {0}'.format(cert))

        result = HTTPClient().fetch(
            tornado.httputil.url_concat(url, params),
            method=method,
            headers=header_dict,
            auth_username=username,
            auth_password=password,
            body=data,
            validate_cert=verify_ssl,
            **req_kwargs
        )

        if stream is True or handle is True:
            return {'handle': result}

        result_status_code = result.code
        result_headers = result.headers
        result_text = result.body
        if 'Set-Cookie' in result_headers.keys():
            result_cookies = parse_cookie_header(result_headers['Set-Cookie'])
            for item in result_cookies:
                sess_cookies.set_cookie(item)
        else:
            result_cookies = None

    if isinstance(result_headers, list):
        result_headers_dict = {}
        for header in result_headers:
            comps = header.split(':')
            result_headers_dict[comps[0].strip()] = ':'.join(comps[1:]).strip()
        result_headers = result_headers_dict

    log.debug('Response Status Code: {0}'.format(result_status_code))
    log.trace('Response Headers: {0}'.format(result_headers))
    log.trace('Response Cookies: {0}'.format(sess_cookies))
    try:
        log.trace('Response Text: {0}'.format(result_text))
    except UnicodeEncodeError as exc:
        log.trace(('Cannot Trace Log Response Text: {0}. This may be due to '
                  'incompatibilities between requests and logging.').format(exc))

    if text_out is not None and os.path.exists(text_out):
        with salt.utils.fopen(text_out, 'w') as tof:
            tof.write(result_text)

    if headers_out is not None and os.path.exists(headers_out):
        with salt.utils.fopen(headers_out, 'w') as hof:
            hof.write(result_headers)

    if cookies is not None:
        sess_cookies.save()

    if persist_session is True and HAS_MSGPACK:
        # TODO: See persist_session above
        if 'set-cookie' in result_headers:
            with salt.utils.fopen(session_cookie_jar, 'w') as fh_:
                session_cookies = result_headers.get('set-cookie', None)
                if session_cookies is not None:
                    msgpack.dump({'Cookie': session_cookies}, fh_)
                else:
                    msgpack.dump('', fh_)

    if status is True:
        ret['status'] = result_status_code

    if headers is True:
        ret['headers'] = result_headers

    if decode is True:
        if decode_type == 'auto':
            content_type = result_headers.get(
                'content-type', 'application/json'
            )
            if 'xml' in content_type:
                decode_type = 'xml'
            elif 'json' in content_type:
                decode_type = 'json'
            else:
                decode_type = 'plain'

        valid_decodes = ('json', 'xml', 'plain')
        if decode_type not in valid_decodes:
            ret['error'] = (
                'Invalid decode_type specified. '
                'Valid decode types are: {0}'.format(
                    pprint.pformat(valid_decodes)
                )
            )
            log.error(ret['error'])
            return ret

        if decode_type == 'json':
            ret['dict'] = json.loads(result_text)
        elif decode_type == 'xml':
            ret['dict'] = []
            items = ET.fromstring(result_text)
            for item in items:
                ret['dict'].append(xml.to_dict(item))
        else:
            text = True

        if decode_out and os.path.exists(decode_out):
            with salt.utils.fopen(decode_out, 'w') as dof:
                dof.write(result_text)

    if text is True:
        ret['text'] = result_text

    return ret


def get_ca_bundle(opts=None):
    '''
    Return the location of the ca bundle file. See the following article:

        http://tinyurl.com/k7rx42a
    '''
    if hasattr(get_ca_bundle, '__return_value__'):
        return get_ca_bundle.__return_value__

    if opts is None:
        opts = {}

    opts_bundle = opts.get('ca_bundle', None)
    if opts_bundle is not None and os.path.exists(opts_bundle):
        return opts_bundle

    file_roots = opts.get('file_roots', {'base': [syspaths.SRV_ROOT_DIR]})

    # Please do not change the order without good reason

    # Check Salt first
    for salt_root in file_roots.get('base', []):
        log.debug('file_roots is {0}'.format(salt_root))
        for path in ('cacert.pem', 'ca-bundle.crt'):
            if os.path.exists(path):
                return path

    locations = (
        # Debian has paths that often exist on other distros
        '/etc/ssl/certs/ca-certificates.crt',
        # RedHat is also very common
        '/etc/pki/tls/certs/ca-bundle.crt',
        '/etc/pki/tls/certs/ca-bundle.trust.crt',
        # RedHat's link for Debian compatability
        '/etc/ssl/certs/ca-bundle.crt',
        # Suse has an unusual path
        '/var/lib/ca-certificates/ca-bundle.pem',
        # OpenBSD has an unusual path
        '/etc/ssl/cert.pem',
    )
    for path in locations:
        if os.path.exists(path):
            return path

    if salt.utils.is_windows() and HAS_CERTIFI:
        return certifi.where()

    return None


def update_ca_bundle(
        target=None,
        source=None,
        opts=None,
        merge_files=None,
    ):
    '''
    Attempt to update the CA bundle file from a URL

    If not specified, the local location on disk (``target``) will be
    auto-detected, if possible. If it is not found, then a new location on disk
    will be created and updated.

    The default ``source`` is:

        http://curl.haxx.se/ca/cacert.pem

    This is based on the information at:

        http://curl.haxx.se/docs/caextract.html

    A string or list of strings representing files to be appended to the end of
    the CA bundle file may also be passed through as ``merge_files``.
    '''
    if opts is None:
        opts = {}

    if target is None:
        target = get_ca_bundle(opts)

    if target is None:
        log.error('Unable to detect location to write CA bundle to')
        return

    if source is None:
        source = opts.get('ca_bundle_url', 'http://curl.haxx.se/ca/cacert.pem')

    log.debug('Attempting to download {0} to {1}'.format(source, target))
    query(
        source,
        text=True,
        decode=False,
        headers=False,
        status=False,
        text_out=target
    )

    if merge_files is not None:
        if isinstance(merge_files, six.string_types):
            merge_files = [merge_files]

        if not isinstance(merge_files, list):
            log.error('A value was passed as merge_files which was not either '
                      'a string or a list')
            return

        merge_content = ''

        for cert_file in merge_files:
            if os.path.exists(cert_file):
                log.debug(
                    'Queueing up {0} to be appended to {1}'.format(
                        cert_file, target
                    )
                )
                try:
                    with salt.utils.fopen(cert_file, 'r') as fcf:
                        merge_content = '\n'.join((merge_content, fcf.read()))
                except IOError as exc:
                    log.error(
                        'Reading from {0} caused the following error: {1}'.format(
                            cert_file, exc
                        )
                    )

        if merge_content:
            log.debug('Appending merge_files to {0}'.format(target))
            try:
                with salt.utils.fopen(target, 'a') as tfp:
                    tfp.write('\n')
                    tfp.write(merge_content)
            except IOError as exc:
                log.error(
                    'Writing to {0} caused the following error: {1}'.format(
                        target, exc
                    )
                )


def _render(template, render, renderer, template_dict, opts):
    '''
    Render a template
    '''
    if render:
        if template_dict is None:
            template_dict = {}
        if not renderer:
            renderer = opts.get('renderer', 'yaml_jinja')
        rend = salt.loader.render(opts, {})
        return compile_template(template, rend, renderer, **template_dict)
    with salt.utils.fopen(template, 'r') as fh_:
        return fh_.read()


def parse_cookie_header(header):
    '''
    Parse the "Set-cookie" header, and return a list of cookies.

    This function is here because Tornado's HTTPClient doesn't handle cookies.
    '''
    attribs = ('expires', 'path', 'domain', 'version', 'httponly', 'secure', 'comment', 'max-age')

    # Split into cookie(s); handles headers with multiple cookies defined
    morsels = []
    for item in header.split(';'):
        item = item.strip()
        if ',' in item and 'expires' not in item:
            for part in item.split(','):
                morsels.append(part)
        else:
            morsels.append(item)

    # Break down morsels into actual cookies
    cookies = []
    cookie = {}
    value_set = False
    for morsel in morsels:
        parts = morsel.split('=')
        if parts[0].lower() in attribs:
            if parts[0] in cookie:
                cookies.append(cookie)
                cookie = {}
            if len(parts) > 1:
                cookie[parts[0]] = '='.join(parts[1:])
            else:
                cookie[parts[0]] = True
        else:
            if value_set is True:
                # This is a new cookie; save the old one and clear for this one
                cookies.append(cookie)
                cookie = {}
                value_set = False
            cookie[parts[0]] = '='.join(parts[1:])
            value_set = True

    if cookie:
        # Set the last cookie that was processed
        cookies.append(cookie)

    # These arguments are required by cookielib.Cookie()
    reqd = (
        'version',
        'port',
        'port_specified',
        'domain',
        'domain_specified',
        'domain_initial_dot',
        'path',
        'path_specified',
        'secure',
        'expires',
        'discard',
        'comment',
        'comment_url',
        'rest',
    )

    ret = []
    for cookie in cookies:
        name = None
        value = None
        for item in cookie.keys():
            if item in attribs:
                continue
            name = item
            value = cookie[item]
            del cookie[name]

        # cookielib.Cookie() requires an epoch
        if 'expires' in cookie:
            cookie['expires'] = salt.ext.six.moves.http_cookiejar.http2time(cookie['expires'])

        # Fill in missing required fields
        for req in reqd:
            if req not in cookie.keys():
                cookie[req] = None
        if cookie['version'] is None:
            cookie['version'] = 0
        if cookie['rest'] is None:
            cookie['rest'] = {}

        ret.append(salt.ext.six.moves.http_cookiejar.Cookie(name=name, value=value, **cookie))

    return ret
