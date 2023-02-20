import base64
import cgi
import json
import re
from dataclasses import Field, dataclass, fields, is_dataclass, make_dataclass
from datetime import date, datetime
from typing import Callable, Optional, Tuple, Union, get_args, get_origin
from xmlrpc.client import boolean

import requests
from dacite import from_dict
from dataclasses_json import DataClassJsonMixin


class SecurityClient:
    client: requests.Session
    query_params: dict[str, str] = {}

    def __init__(self, client: requests.Session):
        self.client = client

    def request(self, method, url, **kwargs):
        params = kwargs.get('params', {})
        kwargs["params"] = self.query_params | params

        return self.client.request(method, url, **kwargs)


def configure_security_client(client: requests.Session, security: dataclass):
    client = SecurityClient(client)

    sec_fields: Tuple[Field, ...] = fields(security)
    for sec_field in sec_fields:
        value = getattr(security, sec_field.name)
        if value is None:
            continue

        metadata = sec_field.metadata.get('security')
        if metadata is None:
            continue
        if metadata.get('option'):
            _parse_security_option(client, value)
            return
        elif metadata.get('scheme'):
            _parse_security_scheme(client, metadata, value)

    return client


def _parse_security_option(client: SecurityClient, option: dataclass):
    opt_fields: Tuple[Field, ...] = fields(option)
    for opt_field in opt_fields:
        metadata = opt_field.metadata.get('security')
        if metadata is None or metadata.get('scheme') is None:
            continue
        _parse_security_scheme(client, metadata.get(
            'scheme'), getattr(option, opt_field.name))


def _parse_security_scheme(client: SecurityClient, scheme_metadata: dict, scheme: dataclass):
    scheme_type = scheme_metadata.get('type')
    sub_type = scheme_metadata.get('sub_type')

    if scheme_type == 'http' and sub_type == 'basic':
        _parse_basic_auth_scheme(client, scheme)
        return

    scheme_fields: Tuple[Field, ...] = fields(scheme)
    for scheme_field in scheme_fields:
        metadata = scheme_field.metadata.get('security')
        if metadata is None or metadata.get('field_name') is None:
            continue

        header_name = metadata.get('field_name')
        value = getattr(scheme, scheme_field.name)

        if scheme_type == "apiKey":
            if sub_type == 'header':
                client.client.headers[header_name] = value
            elif sub_type == 'query':
                client.query_params[header_name] = value
            elif sub_type == 'cookie':
                client.client.cookies[header_name] = value
            else:
                raise Exception('not supported')
        elif scheme_type == "openIdConnect":
            client.client.headers[header_name] = value
        elif scheme_type == 'oauth2':
            client.client.headers[header_name] = value
        elif scheme_type == 'http':
            if sub_type == 'bearer':
                client.client.headers[header_name] = value
            else:
                raise Exception('not supported')
        else:
            raise Exception('not supported')


def _parse_basic_auth_scheme(client: SecurityClient, scheme: dataclass):
    username, password = ""

    scheme_fields: Tuple[Field, ...] = fields(scheme)
    for scheme_field in scheme_fields:
        metadata = scheme_field.metadata.get('security')
        if metadata is None or metadata.get('field_name') is None:
            continue

        field_name = metadata.get('field_name')
        value = getattr(scheme, scheme_field.name)

        if field_name == 'username':
            username = value
        if field_name == 'password':
            password = value

    data = f'{username}:{password}'.encode()
    client.client.headers['Authorization'] = f'Basic {base64.b64encode(data)}'


def generate_url(server_url: str, path: str, path_params: dataclass) -> str:
    param_fields: Tuple[Field, ...] = fields(path_params)
    for f in param_fields:
        param_metadata = f.metadata.get('path_param')
        if not param_metadata:
            continue
        if param_metadata.get('style', 'simple') == 'simple':
            param = getattr(path_params, f.name)
            if type(param) is list:
                pp_vals: list[str] = []
                for pp_val in param:
                    pp_vals.append(str(pp_val))
                path = path.replace(
                    '{' + param_metadata.get('field_name', f.name) + '}', ",".join(pp_vals), 1)
            elif type(param) is dict:
                pp_vals: list[str] = []
                for pp_key in param:
                    if param_metadata.get('explode'):
                        pp_vals.append(f"{pp_key}={param[pp_key]}")
                    else:
                        pp_vals.append(f"{pp_key},{param[pp_key]}")
                path = path.replace(
                    '{' + param_metadata.get('field_name', f.name) + '}', ",".join(pp_vals), 1)
            elif not isinstance(param, (str, int, float, complex, bool)):
                pp_vals: list[str] = []
                attrs: list[str] = [p for p in dir(param) if not p.startswith(
                    '__') and not callable(getattr(param, p))]
                for attr in attrs:
                    field: Field = _get_field_from_attr(param, attr)

                    param_value_metadata = field.metadata.get('path_param')
                    if not param_value_metadata:
                        continue

                    parm_name = param_value_metadata.get('field_name', f.name)

                    param_field_val = getattr(param, attr)
                    if field is not None and is_optional(field) and param_field_val is None:
                        continue
                    elif param_metadata.get('explode'):
                        pp_vals.append(f"{parm_name}={param_field_val}")
                    else:
                        pp_vals.append(f"{parm_name},{param_field_val}")
                path = path.replace(
                    '{' + param_metadata.get('field_name', f.name) + '}', ",".join(pp_vals), 1)
            else:
                path = path.replace(
                    '{' + param_metadata.get('field_name', f.name) + '}', str(param), 1)

    return server_url.removesuffix("/") + path


def _get_field_from_attr(obj, attr: str) -> Field:
    pp_fields: Tuple[Field, ...] = fields(obj)
    for pp_field in pp_fields:
        if pp_field.name == attr:
            return pp_field
    return None


def is_optional(field):
    return get_origin(field) is Union and type(None) in get_args(field)


def replace_parameters(string_with_params: str, params: dict[str, str]) -> str:
    for key, value in params.items():
        string_with_params = string_with_params.replace(
            '{' + key + '}', value)

    return string_with_params


def get_query_params(query_params: dataclass) -> dict[str, list[str]]:
    if query_params is None:
        return {}

    params: dict[str, list[str]] = {}

    param_fields: Tuple[Field, ...] = fields(query_params)
    for f in param_fields:
        metadata = f.metadata.get('query_param')
        if not metadata:
            continue

        param_name = f.name
        f_name = metadata.get("field_name")
        serialization = metadata.get('serialization', '')
        if serialization != '':
            params = params | _get_serialized_query_params(
                metadata, f_name, getattr(query_params, param_name))
        else:
            style = metadata.get('style', 'form')
            if style == 'deepObject':
                params = params | _get_deep_object_query_params(
                    metadata, f_name, getattr(query_params, param_name))
            elif style == 'form':
                params = params | _get_form_query_params(
                    metadata, f_name, getattr(query_params, param_name))
            else:
                raise Exception('not yet implemented')
    return params


def get_headers(headers_params: dataclass) -> dict[str, str]:
    if headers_params is None:
        return {}

    headers: dict[str, str] = {}

    param_fields: Tuple[Field, ...] = fields(headers_params)
    for f in param_fields:
        metadata = f.metadata.get('header')
        if not metadata:
            continue

        value = _serialize_header(metadata.get(
            'explode', False), getattr(headers_params, f.name))

        if value != '':
            headers[metadata.get('field_name', f.name)] = value

    return headers


def _get_serialized_query_params(metadata: dict, field_name: str, obj: any) -> dict[str, list[str]]:
    params: dict[str, list[str]] = {}

    serialization = metadata.get('serialization', '')
    if serialization == 'json':
        params[metadata.get("field_name", field_name)] = marshal_json(obj)

    return params


def _get_deep_object_query_params(metadata: dict, field_name: str, obj: any) -> dict[str, list[str]]:
    params: dict[str, list[str]] = {}

    if is_dataclass(obj):
        obj_fields: Tuple[Field, ...] = fields(obj)
        for obj_field in obj_fields:
            obj_param_metadata = obj_field.metadata.get('query_param')
            if not obj_param_metadata:
                continue
            params[
                f'{metadata.get("field_name", field_name)}[{obj_param_metadata.get("field_name", obj_field.name)}]'] = [
                getattr(obj, obj_field.name)]
    elif isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, list):
                params[f'{metadata.get("field_name", field_name)}[{key}]'] = value
            else:
                params[f'{metadata.get("field_name", field_name)}[{key}]'] = [
                    value]
    return params


def _get_query_param_field_name(obj_field: Field) -> str:
    obj_param_metadata = obj_field.metadata.get('query_param')

    if not obj_param_metadata:
        return ""

    return obj_param_metadata.get("field_name", obj_field.name)


def _get_form_query_params(metadata: dict, field_name: str, obj: any) -> dict[str, list[str]]:
    return _populate_form(field_name, metadata.get("explode", True), obj, _get_query_param_field_name)


def serialize_request_body(request: dataclass) -> Tuple[str, any, any]:
    if request is None:
        return None, None, None, None

    request_val = getattr(request, "request")
    if request_val is None:
        raise Exception("request body not found")

    request_fields: Tuple[Field, ...] = fields(request)
    request_metadata = None

    for f in request_fields:
        if f.name == "request":
            request_metadata = f.metadata.get('request')
            break

    if request_metadata is not None:
        # single request
        return serialize_content_type(request_metadata, request_val)

    request_fields: Tuple[Field, ...] = fields(request_val)
    for f in request_fields:
        req = getattr(request_val, f.name)
        if req is None:
            continue

        request_metadata = f.metadata.get('request')
        if request_metadata is None:
            raise Exception(
                f'missing request tag on request body field {f.name}')

        return serialize_content_type(request_metadata, request_val)


def serialize_content_type(metadata, request: dataclass) -> Tuple[str, any, list[list[any]]]:
    media_type = metadata.get('media_type', 'application/octet-stream')
    if re.match(r'text/plain', media_type) != None:
        return media_type, serialize_text(request), None, None
    if re.match(r'(application|text)\/.*?\+*json.*', media_type) != None:
        return media_type, None, serialize_json(request), None
    if re.match(r'multipart\/.*', media_type) != None:
        return serialize_multipart_form(media_type, request)
    if re.match(r'application\/x-www-form-urlencoded.*', media_type) != None:
        return media_type, serialize_form(request, 'request'), None, None
    if isinstance(request, (bytes, bytearray)):
        return media_type, request, None, None
    if isinstance(request, str):
        return media_type, request, None, None

    raise Exception(
        f"invalid request body type {type(request)} for mediaType {metadata['media_type']}")


def serialize_text(request: dataclass) -> str:
    request_fields: Tuple[Field, ...] = fields(request)
    for f in request_fields:
        field_metadata = f.metadata.get('request')
        if field_metadata is None:
            continue

        field_value = getattr(request, f.name)
        if field_value is None or not isinstance(field_value, str):
            continue
        return field_value
    return None


def serialize_json(request: dataclass) -> str:
    request_fields: Tuple[Field, ...] = fields(request)
    for f in request_fields:
        field_metadata = f.metadata.get('request')
        if field_metadata is None:
            continue

        field_value = getattr(request, f.name)
        if field_value is None:
            continue

        return json.dumps(field_value)
    return marshal_json(request)


def dict_to_dataclass(orig: dict[str, any], dataclass_type: str):
    cast_type = str(dataclass_type).replace(
        "typing.Optional[", "").replace("]", "")

    cast_modules = cast_type.split(".")[:-1]
    if cast_modules[0] == "typing":
        # This is a built-in type, not a data_class
        return orig

    module = None
    for m in cast_modules:
        if not module:
            module = __import__(m)
        else:
            module = getattr(module, m)

    cast_type = cast_type.split(".")[-1:][0]
    cast_class = getattr(module, cast_type)
    data_class = from_dict(cast_class, orig)
    data_fields = fields(data_class)
    for f in data_fields:
        name = f.name
        for meta_key, meta_value in f.metadata.items():
            try:
                name = meta_value["field_name"]
                break
            except KeyError:
                continue

        try:
            original_value = orig[f.name]
        except KeyError:
            original_value = orig[name]

        setattr(data_class, f.name, original_value)
    return data_class


def parse_field(field: Field, data_class: dataclass, metadata_string: str):
    field_metadata = field.metadata.get(metadata_string)
    if field_metadata is None:
        return None

    field_value = getattr(data_class, field.name)
    if field_value is None:
        return None
    try:
        return dict_to_dataclass(field_value, field.type)
    except Exception:
        return field_value


def serialize_multipart_form(media_type: str, request: dataclass) -> Tuple[str, any, list[list[any]]]:
    form: list[list[any]] = []
    request_fields: Tuple[Field, ...] = fields(request)
    for f in request_fields:
        field_value = parse_field(f, request, 'request')
        if not field_value:
            continue

        if is_dataclass(field_value):
            value_request_fields = fields(field_value)

            for field_value_f in value_request_fields:
                field_metadata = field_value_f.metadata.get('multipart_form')

                if not field_metadata:
                    continue
                if field_metadata.get("file") is True:
                    file = getattr(field_value, field_value_f.name)
                    file = dict_to_dataclass(file, field_value_f.type)
                    file_fields = fields(file)

                    file_name = ""
                    field_name = ""
                    content = bytes()

                    for file_field in file_fields:
                        file_metadata = file_field.metadata.get(
                            'multipart_form')
                        if file_metadata is None:
                            continue
                        if file_metadata.get("content") is True:
                            content = getattr(file, file_field.name)
                        else:
                            field_name = file_metadata.get(
                                "field_name", file_field.name)
                            file_name = getattr(file, file_field.name)
                    if field_name == "" or file_name == "" or content == bytes():
                        raise Exception('invalid multipart/form-data file')

                    form.append([field_name, [file_name, content]])
                elif field_metadata.get("json") is True:
                    to_append = [field_metadata.get("field_name", field_value_f.name), [
                        None, marshal_json(getattr(field_value, field_value_f.name)), "application/json"]]
                    form.append(to_append)
                else:
                    val = getattr(field_value, field_value_f.name)
                    field_name = field_metadata.get(
                        "field_name", field_value_f.name)
                    if isinstance(val, list):
                        for value in val:
                            form.append([field_name + "[]", [None, value]])
                    else:
                        form.append([field_name, [None, val]])
    return media_type, None, None, form


def _get_form_field_name(obj_field: Field) -> str:
    obj_param_metadata = obj_field.metadata.get('form')

    if not obj_param_metadata:
        return ""

    return obj_param_metadata.get("field_name", obj_field.name)


def serialize_dict(original: dict, explode: bool, field_name, existing: Optional[dict[str, list[str]]]) -> dict[
    str, list[str]]:
    if existing is None:
        existing = []

    if explode is True:
        for k, v in original.items():
            if k not in existing:
                existing[k] = []
            existing[k].append(v)
    else:
        temp = []
        for k, v in original.items():
            temp.append(str(k))
            temp.append(str(v))
        if field_name not in existing:
            existing[field_name] = []
        existing[field_name].append(",".join(temp))
    return existing


def serialize_form(data: dataclass, meta_string: str) -> dict[str, any]:
    form: dict[str, list[str]] = {}
    request_fields: Tuple[Field, ...] = fields(data)

    for f in request_fields:
        field_value = parse_field(f, data, meta_string)
        if not field_value:
            continue

        if is_dataclass(field_value):
            value_fields = fields(field_value)
            for value_f in value_fields:
                value = parse_field(value_f, field_value, 'form')
                if not value:
                    continue
                metadata = value_f.metadata.get('form')
                if metadata is None:
                    continue

                f_name = metadata["field_name"]
                if is_dataclass(value):
                    if "style" not in metadata or ("json" in metadata and metadata["json"] is True):
                        if f_name not in form:
                            form[f_name] = []
                        form[f_name].append(json.dumps(
                            getattr(field_value, f_name)))
                    else:
                        if "style" in metadata and metadata["style"] == "form":
                            form = form | serialize_form(value, "form")

                elif isinstance(value, dict):
                    if "json" in metadata and metadata["json"] is True:
                        if f_name not in form:
                            form[f_name] = []
                        form[f_name].append(json.dumps(value))
                    else:
                        explode = "explode" in metadata and metadata["explode"] is True
                        serialize_dict(value, explode, f_name, form)
                elif isinstance(value, list):
                    if "explode" in metadata and metadata["explode"] is True:
                        if f_name not in form:
                            form[f_name] = []
                        for item in value:
                            form[f_name].append(item)
                    else:
                        if value_f.name not in form:
                            form[f_name] = []
                        form[f_name].append(",".join(value))
                else:
                    if value_f.name not in form:
                        form[f_name] = []
                    form[f_name].append(str(value))
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    for v in value:
                        if not key in form:
                            form[key] = []
                        form[key].append(v)
                else:
                    if not key in form:
                        form[key] = []
                    form[key].append(value)
        elif isinstance(data, list):
            for value in data:
                if isinstance(value, list):
                    for v in value:
                        if not key in form:
                            form[meta_string] = []
                        form[meta_string].append(v)
                else:
                    if not key in form:
                        form[meta_string] = []
                    form[meta_string].append(value)
    return form


def _populate_form(field_name: str, explode: boolean, obj: any, get_field_name_func: Callable) -> dict[str, list[str]]:
    params: dict[str, str | list[str]] = {}

    if is_dataclass(obj):
        items = []

        obj_fields: Tuple[Field, ...] = fields(obj)
        for obj_field in obj_fields:
            obj_field_name = get_field_name_func(obj_field)
            if obj_field_name == "":
                continue

            if explode:
                params[obj_field_name] = [getattr(obj, obj_field.name)]
            else:
                items.append(
                    f'{obj_field_name},{getattr(obj, obj_field.name)}')

        if len(items) > 0:
            params[field_name] = [','.join(items)]
    elif isinstance(obj, dict):
        items = []
        for key, value in obj.items():
            if explode:
                _populate_simple_param(params, key, value)
            else:
                items.append(f'{key},{value}')

        if len(items) > 0:
            params[field_name] = [','.join(items)]
    elif isinstance(obj, list):
        items = []

        for value in obj:
            if explode:
                if not field_name in params:
                    params[field_name] = []
                params[field_name].append(value)
            else:
                items.append(value)

        if len(items) > 0:
            params[field_name] = [','.join([str(item) for item in items])]
    else:
        _populate_simple_param(params, field_name, obj)

    return params


def _populate_simple_param(params: dict[str, str | list[str]], field_name: str, value: any):
    # Python uses True and False instead of true and false for booleans;
    # This json encodes the values _only_ if the value is a boolean.
    if value is True or value is False:
        params[field_name] = json.dumps(value)
    else:
        params[field_name] = value


def _serialize_header(explode: boolean, obj: any) -> str:
    if is_dataclass(obj):
        items = []
        obj_fields: Tuple[Field, ...] = fields(obj)
        for obj_field in obj_fields:
            obj_param_metadata = obj_field.metadata.get('header')

            if not obj_param_metadata:
                continue

            obj_field_name = obj_param_metadata.get(
                "field_name", obj_field.name)
            if obj_field_name == "":
                continue

            if explode:
                items.append(
                    f'{obj_field_name}={getattr(obj, obj_field.name)}')
            else:
                items.append(obj_field_name)
                items.append(getattr(obj, obj_field.name))

        if len(items) > 0:
            return [','.join(items)]
    elif isinstance(obj, dict):
        items = []

        for key, value in obj.items():
            if explode:
                items.append(f'{key}={value}')
            else:
                items.append(key)
                items.append(value)

        if len(items) > 0:
            return ','.join([str(item) for item in items])
    elif isinstance(obj, list):
        return ','.join(obj)
    else:
        return f'{obj}'


def unmarshal_json(data, t):
    d = json.loads(data)
    return dict_to_dataclass(d, t)


def marshal_json(c):
    Marshal = make_dataclass('Marshal', [('res', type(c))],
                             bases=(DataClassJsonMixin,))
    m = Marshal(res=c)
    d = m.to_dict()
    return json.dumps(d["res"])


def match_content_type(content_type: str, pattern: str) -> boolean:
    if content_type == pattern or pattern == "*" or pattern == "*/*":
        return True

    media_type, _ = cgi.parse_header(content_type)

    if media_type == pattern:
        return True

    parts = media_type.split("/")
    if len(parts) == 2:
        if f'{parts[0]}/*' == pattern or f'*/{parts[1]}' == pattern:
            return True

    return False


def datetimeisoformat(optional: bool):
    def isoformatoptional(v):
        if optional and v is None:
            return None
        return datetime.isoformat(v)

    return isoformatoptional


def dateisoformat(optional: bool):
    def isoformatoptional(v):
        if optional and v is None:
            return None
        return date.isoformat(v)

    return isoformatoptional


def field_name(name):
    def override(_, _field_name=name):
        return _field_name

    return override
