"""
    tknorris shared module
    Copyright (C) 2016 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import time
import kodi
import cProfile
import StringIO
import pstats
from xbmc import LOGDEBUG, LOGERROR, LOGFATAL, LOGINFO, LOGNONE, LOGNOTICE, LOGSEVERE, LOGWARNING  # @UnusedImport

name = kodi.get_name()
enabled_comp = kodi.get_setting('enabled_comp')
if enabled_comp:
    enabled_comp = enabled_comp.split(',')
else:
    enabled_comp = None

def log(msg, level=LOGDEBUG, component=None):
    req_level = level
    # override message level to force logging when addon logging turned on
    if kodi.get_setting('addon_debug') == 'true' and level == LOGDEBUG:
        level = LOGNOTICE
    
    try:
        if isinstance(msg, unicode):
            msg = '%s (ENCODED)' % (msg.encode('utf-8'))

        if req_level != LOGDEBUG or (enabled_comp is None or component in enabled_comp):
            kodi.__log('%s: %s' % (name, msg), level)
            
    except Exception as e:
        try: kodi.__log('Logging Failure: %s' % (e), level)
        except: pass  # just give up

def profile(file_path, sort_by):
    def decorator(method):
        def method_profile_on(*args, **kwargs):
            pr = cProfile.Profile(builtins=False)
            pr.enable()
            result = pr.runcall(method, *args, **kwargs)
            pr.disable()
            s = StringIO.StringIO()
            params = (sort_by,) if isinstance(sort_by, basestring) else sort_by
            ps = pstats.Stats(pr, stream=s).sort_stats(*params)
            ps.print_stats()
            with open(file_path, 'w') as f:
                f.write(s.getvalue())
                
            return result
        
        def method_profile_off(*args, **kwargs):
            return method(*args, **kwargs)
    
        if __is_debugging():
            return method_profile_on
        else:
            return method_profile_off
        
    return decorator
    
        
def trace(method):
    #  @debug decorator
    def method_trace_on(*args, **kwargs):
        start = time.time()
        result = method(*args, **kwargs)
        end = time.time()
        log('{name!r} time: {time:2.4f}s args: |{args!r}| kwargs: |{kwargs!r}|'.format(name=method.__name__, time=end - start, args=args, kwargs=kwargs), LOGDEBUG)
        return result

    def method_trace_off(*args, **kwargs):
        return method(*args, **kwargs)

    if __is_debugging():
        return method_trace_on
    else:
        return method_trace_off

def __is_debugging():
    command = {'jsonrpc': '2.0', 'id': 1, 'method': 'Settings.getSettings', 'params': {'filter': {'section': 'system', 'category': 'logging'}}}
    js_data = kodi.execute_jsonrpc(command)
    for item in js_data.get('result', {}).get('settings', {}):
        if item['id'] == 'debug.showloginfo':
            return item['value']
    
    return False
