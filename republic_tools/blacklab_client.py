import http
from http import HTTPStatus

import requests
from icecream import ic
from requests import Response

import republic_tools


class BlackLabClient:
    def __init__(self, base_url: str, timeout: int = None, verbose: bool = False, outputformat: str = "json"):
        self.base_url = base_url.strip('/')
        self.timeout = timeout
        self.verbose = verbose
        self.outputformat = outputformat

    def __str__(self):
        return f'BlackLabClient({self.base_url})'

    def __repr__(self):
        return self.__str__()

    def get_server_info(self):
        url = f'{self.base_url}/'
        response = self.__get(url=url)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_corpus_information(self, corpus_name: str):
        url = f'{self.base_url}/{corpus_name}'
        response = self.__get(url=url)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_corpus_status(self, corpus_name: str):
        url = f'{self.base_url}/{corpus_name}/status'
        response = self.__get(url=url)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_corpus_field_information(self, corpus_name: str, field_name: str):
        url = f'{self.base_url}/{corpus_name}/fields/{field_name}'
        response = self.__get(url=url)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_corpus_hits(self, corpus_name: str, patt=None):
        url = f'{self.base_url}/{corpus_name}/hits'
        params = {}
        if patt:
            params["patt"] = patt
        response = self.__get(url=url, params=params)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_corpus_docs(self, corpus_name: str):
        url = f'{self.base_url}/{corpus_name}/docs'
        response = self.__get(url=url)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_corpus_document_metadata(self, corpus_name: str, document_pid: str):
        url = f'{self.base_url}/{corpus_name}/docs/{document_pid}'
        response = self.__get(url=url)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_corpus_document_contents(self, corpus_name: str, document_pid: str):
        url = f'{self.base_url}/{corpus_name}/docs/{document_pid}/contents'
        response = self.__get(url=url)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_corpus_document_snippet(self, corpus_name: str, document_pid: str):
        url = f'{self.base_url}/{corpus_name}/docs/{document_pid}/snippet'
        response = self.__get(url=url)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_corpus_term_frequency(self, corpus_name: str, annotation: str = 'word'):
        url = f'{self.base_url}/{corpus_name}/termfreq'
        params = {"annotation": annotation}
        response = self.__get(url=url, params=params)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_corpus_autocomplete(self, corpus_name: str):
        url = f'{self.base_url}/{corpus_name}/autocomplete'
        response = self.__get(url=url)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_corpus_sharing(self, corpus_name: str):
        url = f'{self.base_url}/{corpus_name}/sharing'
        response = self.__get(url=url)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_input_formats(self):
        url = f'{self.base_url}/input-formats'
        response = self.__get(url=url)
        
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_input_format_configuration(self, format_name: str):
        url = f'{self.base_url}/input-formats/{format_name}'
        response = self.__get(url=url)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def get_cache_info(self):
        url = f'{self.base_url}/cache-info'
        response = self.__get(url=url)
        return self.__handle_response(response, {HTTPStatus.OK: lambda r: r.json()})

    def __get(self, url, params=None, **kwargs):
        args = self.__set_defaults(kwargs)
        return requests.get(url, params=params, **args)

    def __head(self, url, params=None, **kwargs):
        args = self.__set_defaults(kwargs)
        return requests.head(url, params=params, **args)

    def __post(self, url, data=None, json=None, **kwargs):
        args = self.__set_defaults(kwargs)
        return requests.post(url, data=data, json=json, **args)

    def __put(self, url, data=None, **kwargs):
        args = self.__set_defaults(kwargs)
        return requests.put(url, data=data, **args)

    def __delete(self, url, **kwargs):
        ic(url)
        ic(kwargs)
        args = self.__set_defaults(kwargs)
        return requests.delete(url, **args)

    def __set_defaults(self, args: dict):
        # ic(args)
        if 'headers' not in args:
            args['headers'] = {}
        args['headers']['User-Agent'] = f'blacklab-python-client/{republic_tools.__version__}'
        args['headers']['Accept'] = 'application/json' if self.outputformat == 'json' else 'application/xml'
        if self.timeout:
            args['timeout'] = self.timeout
        return args

    def __handle_response(self, response: Response, result_producers: dict):
        status_code = response.status_code
        status_message = http.client.responses[status_code]
        # ic(response.request.headers)
        if self.verbose:
            print(f'-> {response.request.method} {response.request.url}')
            print(f'<- {status_code} {status_message}')
        if status_code in result_producers:
            # if (self.raise_exceptions):
            return result_producers[response.status_code](response)
            # else:
            #     return Success(response, result)
        else:
            # if (self.raise_exceptions):
            raise Exception(
                f'{response.request.method} {response.request.url} returned {status_code} {status_message}'
                + f': "{response.text}"')
